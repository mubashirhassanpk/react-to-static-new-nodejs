"""
Standalone FastAPI server for desktop application
Uses JSON file storage instead of MongoDB
"""
from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import aiofiles
import shutil
import subprocess
import asyncio
import zipfile
import io
from git import Repo
import json
import sys

# Import custom modules
from json_storage import JSONStorage, BuildsCollection
from port_utils import find_available_port, get_backend_url
from netlify_deployer import NetlifyDeployer, NetlifyDeploymentError

ROOT_DIR = Path(__file__).parent

# Initialize JSON storage
DATA_FILE = ROOT_DIR / "data" / "builds.json"
storage = JSONStorage(DATA_FILE)

# Create a mock database object that uses JSON storage
class Database:
    def __init__(self, storage: JSONStorage):
        self.builds = BuildsCollection(storage)

db = Database(storage)

# Create the main app without a prefix
app = FastAPI(title="React Static Site Builder")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Build storage directory
BUILDS_DIR = ROOT_DIR / "builds"
BUILDS_DIR.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Models
class Build(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    input_type: str  # "upload", "paste", "github"
    status: str  # "pending", "building", "completed", "failed"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    build_logs: str = ""
    output_path: Optional[str] = None
    preview_url: Optional[str] = None
    error_message: Optional[str] = None
    
    # Netlify deployment fields
    netlify_deploy_id: Optional[str] = None
    netlify_site_id: Optional[str] = None
    netlify_deploy_status: Optional[str] = None  # "deploying", "deployed", "failed"
    netlify_deploy_url: Optional[str] = None
    netlify_error_message: Optional[str] = None

class BuildCreate(BaseModel):
    input_type: str

class CodePaste(BaseModel):
    code: str
    filename: str = "App.js"

class GithubRepo(BaseModel):
    repo_url: str

class NetlifyDeployRequest(BaseModel):
    netlify_token: str = Field(description="Netlify personal access token")
    netlify_site_id: Optional[str] = Field(default=None, description="Netlify site ID (optional - will create new site if not provided)")
    site_name: Optional[str] = Field(default=None, description="Custom site name for new Netlify site (optional)")

# Background build function
async def run_build_process(build_id: str, source_dir: Path):
    try:
        # Update status to building
        await db.builds.update_one(
            {"id": build_id},
            {"$set": {"status": "building", "build_logs": "Starting build process...\n"}}
        )
        
        logs = "Starting build process...\n"
        
        # Check if package.json exists
        package_json = source_dir / "package.json"
        if not package_json.exists():
            raise Exception("No package.json found in the project")
        
        # Run yarn install
        logs += "\nRunning yarn install...\n"
        await db.builds.update_one({"id": build_id}, {"$set": {"build_logs": logs}})
        
        process = await asyncio.create_subprocess_exec(
            "yarn", "install",
            cwd=str(source_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        logs += stdout.decode() + stderr.decode()
        await db.builds.update_one({"id": build_id}, {"$set": {"build_logs": logs}})
        
        if process.returncode != 0:
            raise Exception(f"yarn install failed: {stderr.decode()}")
        
        # Run yarn build
        logs += "\n\nRunning yarn build...\n"
        await db.builds.update_one({"id": build_id}, {"$set": {"build_logs": logs}})
        
        process = await asyncio.create_subprocess_exec(
            "yarn", "build",
            cwd=str(source_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        logs += stdout.decode() + stderr.decode()
        await db.builds.update_one({"id": build_id}, {"$set": {"build_logs": logs}})
        
        if process.returncode != 0:
            raise Exception(f"yarn build failed: {stderr.decode()}")
        
        # Check if build directory exists (support both CRA's "build" and Vite's "dist")
        build_dir = source_dir / "build"
        if not build_dir.exists():
            build_dir = source_dir / "dist"
            if not build_dir.exists():
                # List available directories to help debug
                available_dirs = [d.name for d in source_dir.iterdir() if d.is_dir()]
                raise Exception(f"Build directory not found after build. Available directories: {', '.join(available_dirs)}")
        
        # Create ZIP file
        output_dir = BUILDS_DIR / build_id
        output_dir.mkdir(exist_ok=True)
        zip_path = output_dir / "build.zip"
        
        logs += "\n\nCreating ZIP file...\n"
        await db.builds.update_one({"id": build_id}, {"$set": {"build_logs": logs}})
        
        shutil.make_archive(str(output_dir / "build"), 'zip', build_dir)
        
        # Copy build files for preview
        preview_dir = output_dir / "preview"
        if preview_dir.exists():
            shutil.rmtree(preview_dir)
        shutil.copytree(build_dir, preview_dir)
        
        logs += "\n\nBuild completed successfully!\n"
        
        # Update build status
        await db.builds.update_one(
            {"id": build_id},
            {"$set": {
                "status": "completed",
                "build_logs": logs,
                "output_path": str(zip_path),
                "preview_url": f"/api/build/preview/{build_id}/index.html"
            }}
        )
        
    except Exception as e:
        error_msg = str(e)
        logs += f"\n\nBuild failed: {error_msg}\n"
        await db.builds.update_one(
            {"id": build_id},
            {"$set": {
                "status": "failed",
                "build_logs": logs,
                "error_message": error_msg
            }}
        )
    finally:
        # Clean up source directory
        if source_dir.exists():
            shutil.rmtree(source_dir)

# Netlify deployment background task
async def deploy_to_netlify(build_id: str, netlify_token: str, netlify_site_id: Optional[str] = None, site_name: Optional[str] = None):
    """Background task to deploy a completed build to Netlify"""
    try:
        # Update status to deploying
        await db.builds.update_one(
            {"id": build_id},
            {"$set": {"netlify_deploy_status": "deploying"}}
        )
        
        # Get build information
        build = await db.builds.find_one({"id": build_id})
        if not build:
            raise Exception("Build not found")
        
        if build['status'] != 'completed':
            raise Exception("Build must be completed before deploying to Netlify")
        
        # Find the build directory (preview directory)
        preview_dir = BUILDS_DIR / build_id / "preview"
        if not preview_dir.exists():
            raise Exception("Build directory not found")
        
        # Create Netlify deployer instance
        deployer = NetlifyDeployer(netlify_token)
        
        # Deploy to Netlify
        if netlify_site_id:
            logger.info(f"Starting Netlify deployment for build {build_id} to existing site {netlify_site_id}")
        else:
            logger.info(f"Starting Netlify deployment for build {build_id} - creating new site")
        
        # Deploy directory to Netlify
        result = deployer.deploy_directory(str(preview_dir), site_id=netlify_site_id, site_name=site_name)
        
        # Update build with deployment information including the site_id
        await db.builds.update_one(
            {"id": build_id},
            {"$set": {
                "netlify_deploy_id": result['deploy_id'],
                "netlify_site_id": result['site_id'],
                "netlify_deploy_status": "deployed",
                "netlify_deploy_url": result['url'],
                "netlify_error_message": None
            }}
        )
        
        logger.info(f"Successfully deployed to Netlify: {result['url']}")
        
    except NetlifyDeploymentError as e:
        error_msg = f"Netlify deployment error: {str(e)}"
        logger.error(error_msg)
        await db.builds.update_one(
            {"id": build_id},
            {"$set": {
                "netlify_deploy_status": "failed",
                "netlify_error_message": error_msg
            }}
        )
    except Exception as e:
        error_msg = f"Deployment failed: {str(e)}"
        logger.error(error_msg)
        await db.builds.update_one(
            {"id": build_id},
            {"$set": {
                "netlify_deploy_status": "failed",
                "netlify_error_message": error_msg
            }}
        )

# Routes
@api_router.get("/")
async def root():
    return {"message": "React to Static Site Builder API (Standalone Desktop Version)"}

@api_router.post("/build/upload", response_model=Build)
async def upload_build(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")
    
    build_id = str(uuid.uuid4())
    source_dir = BUILDS_DIR / f"source_{build_id}"
    source_dir.mkdir(exist_ok=True)
    
    # Save uploaded file
    zip_path = source_dir / "upload.zip"
    async with aiofiles.open(zip_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Extract ZIP
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(source_dir)
        zip_path.unlink()
    except Exception as e:
        shutil.rmtree(source_dir)
        raise HTTPException(status_code=400, detail=f"Failed to extract ZIP: {str(e)}")
    
    # Create build record
    build = Build(id=build_id, input_type="upload", status="pending")
    doc = build.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.builds.insert_one(doc)
    
    # Start build process in background
    background_tasks.add_task(run_build_process, build_id, source_dir)
    
    return build

@api_router.post("/build/paste", response_model=Build)
async def paste_build(background_tasks: BackgroundTasks, code_data: CodePaste):
    build_id = str(uuid.uuid4())
    source_dir = BUILDS_DIR / f"source_{build_id}"
    source_dir.mkdir(exist_ok=True)
    
    # Create a basic React project structure
    try:
        # Create package.json
        package_json = {
            "name": "react-app",
            "version": "0.1.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "browserslist": {
                "production": [">0.2%", "not dead", "not op_mini all"],
                "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
            }
        }
        
        async with aiofiles.open(source_dir / "package.json", 'w') as f:
            await f.write(json.dumps(package_json, indent=2))
        
        # Create src directory
        src_dir = source_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        # Create public directory
        public_dir = source_dir / "public"
        public_dir.mkdir(exist_ok=True)
        
        # Create index.html
        index_html = '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>React App</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>'''
        async with aiofiles.open(public_dir / "index.html", 'w') as f:
            await f.write(index_html)
        
        # Create index.js
        index_js = '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);'''
        async with aiofiles.open(src_dir / "index.js", 'w') as f:
            await f.write(index_js)
        
        # Save the user's code
        async with aiofiles.open(src_dir / code_data.filename, 'w') as f:
            await f.write(code_data.code)
        
    except Exception as e:
        shutil.rmtree(source_dir)
        raise HTTPException(status_code=400, detail=f"Failed to create project: {str(e)}")
    
    # Create build record
    build = Build(id=build_id, input_type="paste", status="pending")
    doc = build.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.builds.insert_one(doc)
    
    # Start build process in background
    background_tasks.add_task(run_build_process, build_id, source_dir)
    
    return build

@api_router.post("/build/github", response_model=Build)
async def github_build(background_tasks: BackgroundTasks, repo_data: GithubRepo):
    build_id = str(uuid.uuid4())
    source_dir = BUILDS_DIR / f"source_{build_id}"
    source_dir.mkdir(exist_ok=True)
    
    # Validate and clone GitHub repo
    try:
        # First, validate the repository URL format
        repo_url = repo_data.repo_url.strip()
        if not repo_url.startswith(('https://github.com/', 'http://github.com/', 'git@github.com:')):
            shutil.rmtree(source_dir)
            raise HTTPException(
                status_code=400, 
                detail="Invalid GitHub URL. Must be in format: https://github.com/username/repository"
            )
        
        # Try to check if repository exists by making a simple HTTP request
        import requests
        # Convert git@ URL to https if needed
        check_url = repo_url
        if check_url.startswith('git@github.com:'):
            check_url = check_url.replace('git@github.com:', 'https://github.com/')
        if check_url.endswith('.git'):
            check_url = check_url[:-4]
        
        # Check if repository exists
        try:
            response = requests.head(check_url, timeout=10, allow_redirects=True)
            if response.status_code == 404:
                shutil.rmtree(source_dir)
                raise HTTPException(
                    status_code=404,
                    detail=f"Repository not found at {check_url}. Please verify:\n"
                           "1. The repository URL is correct\n"
                           "2. The repository exists and is public\n"
                           "3. The repository owner username is correct"
                )
        except requests.RequestException as req_err:
            # If we can't check, we'll still try to clone
            logger.warning(f"Could not verify repository existence: {req_err}")
        
        # Clone the repository with environment settings to avoid interactive prompts
        env = os.environ.copy()
        env['GIT_TERMINAL_PROMPT'] = '0'  # Disable git credential prompts
        
        # Use git command directly for better control
        result = subprocess.run(
            ['git', 'clone', repo_url, str(source_dir)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            env=env
        )
        
        if result.returncode != 0:
            shutil.rmtree(source_dir)
            error_msg = result.stderr or result.stdout or "Unknown error"
            
            # Provide user-friendly error messages
            if "Repository not found" in error_msg or "not found" in error_msg.lower():
                raise HTTPException(
                    status_code=404,
                    detail=f"Repository not found: {repo_url}\n"
                           "Please check that:\n"
                           "1. The repository URL is correct\n"
                           "2. The repository exists and is public\n"
                           "3. You have spelled the username and repository name correctly"
                )
            elif "could not read Username" in error_msg or "Authentication failed" in error_msg:
                raise HTTPException(
                    status_code=403,
                    detail=f"Repository is private or requires authentication: {repo_url}\n"
                           "Please ensure the repository is public or contact support for private repository access."
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to clone repository: {error_msg}"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        if source_dir.exists():
            shutil.rmtree(source_dir)
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to clone repository: {str(e)}"
        )
    
    # Create build record
    build = Build(id=build_id, input_type="github", status="pending")
    doc = build.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.builds.insert_one(doc)
    
    # Start build process in background
    background_tasks.add_task(run_build_process, build_id, source_dir)
    
    return build

@api_router.get("/build/status/{build_id}", response_model=Build)
async def get_build_status(build_id: str):
    build = await db.builds.find_one({"id": build_id})
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    
    if isinstance(build['created_at'], str):
        build['created_at'] = datetime.fromisoformat(build['created_at'])
    
    return build

@api_router.get("/build/download/{build_id}")
async def download_build(build_id: str):
    build = await db.builds.find_one({"id": build_id})
    if not build or build['status'] != 'completed':
        raise HTTPException(status_code=404, detail="Build not found or not completed")
    
    zip_path = Path(build['output_path'])
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Build file not found")
    
    return FileResponse(zip_path, media_type='application/zip', filename='build.zip')

@api_router.get("/build/preview/{build_id}/{file_path:path}")
async def preview_build(build_id: str, file_path: str):
    build = await db.builds.find_one({"id": build_id})
    if not build or build['status'] != 'completed':
        raise HTTPException(status_code=404, detail="Build not found or not completed")
    
    preview_dir = BUILDS_DIR / build_id / "preview"
    file_path_obj = preview_dir / file_path
    
    # Security check
    if not str(file_path_obj.resolve()).startswith(str(preview_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not file_path_obj.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if file_path_obj.is_file():
        # Determine media type
        media_type = "text/html"
        if file_path.endswith('.js'):
            media_type = "application/javascript"
        elif file_path.endswith('.css'):
            media_type = "text/css"
        elif file_path.endswith('.json'):
            media_type = "application/json"
        elif file_path.endswith('.png'):
            media_type = "image/png"
        elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
            media_type = "image/jpeg"
        elif file_path.endswith('.svg'):
            media_type = "image/svg+xml"
        elif file_path.endswith('.wasm'):
            media_type = "application/wasm"
        
        # For HTML files, rewrite asset paths to work with preview URL structure
        if file_path.endswith('.html'):
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Rewrite absolute paths to relative paths for preview
            base_path = f"/api/build/preview/{build_id}/"
            
            # Replace common absolute path patterns
            html_content = html_content.replace('href="/', f'href="{base_path}')
            html_content = html_content.replace("href='/", f"href='{base_path}")
            html_content = html_content.replace('src="/', f'src="{base_path}')
            html_content = html_content.replace("src='/", f"src='{base_path}")
            
            # Return modified HTML
            return HTMLResponse(content=html_content, media_type="text/html")
        
        return FileResponse(file_path_obj, media_type=media_type)
    
    raise HTTPException(status_code=404, detail="File not found")

@api_router.get("/builds", response_model=List[Build])
async def get_builds():
    cursor = await db.builds.find({})
    builds = await cursor.sort("created_at", -1).to_list(100)
    
    for build in builds:
        if isinstance(build['created_at'], str):
            build['created_at'] = datetime.fromisoformat(build['created_at'])
    
    return builds

@api_router.post("/build/deploy-netlify/{build_id}")
async def deploy_build_to_netlify(build_id: str, request: NetlifyDeployRequest, background_tasks: BackgroundTasks):
    """Deploy a completed build to Netlify"""
    # Check if build exists and is completed
    build = await db.builds.find_one({"id": build_id})
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    
    if build['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Build must be completed before deploying to Netlify")
    
    # Start deployment in background
    background_tasks.add_task(
        deploy_to_netlify,
        build_id,
        request.netlify_token,
        request.netlify_site_id,
        request.site_name
    )
    
    return {
        "message": "Netlify deployment started",
        "build_id": build_id
    }

@api_router.get("/build/netlify-status/{build_id}")
async def get_netlify_deployment_status(build_id: str):
    """Get Netlify deployment status for a build"""
    build = await db.builds.find_one({"id": build_id})
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    
    return {
        "build_id": build_id,
        "netlify_deploy_id": build.get('netlify_deploy_id'),
        "netlify_deploy_status": build.get('netlify_deploy_status'),
        "netlify_deploy_url": build.get('netlify_deploy_url'),
        "netlify_error_message": build.get('netlify_error_message')
    }

# Include the router in the main app
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],  # For standalone desktop app, allow all origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Main entry point for standalone app
if __name__ == "__main__":
    import uvicorn
    
    # Find available port
    port = find_available_port(8000, 9000)
    if not port:
        logger.error("No available ports found")
        sys.exit(1)
    
    logger.info(f"Starting server on http://127.0.0.1:{port}")
    
    # Write port to a file so Electron can read it
    port_file = ROOT_DIR / "server_port.txt"
    with open(port_file, 'w') as f:
        f.write(str(port))
    
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
