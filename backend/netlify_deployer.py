"""
Netlify API Integration Module
Handles deployment of static sites to Netlify using the File Digest method
"""
import hashlib
import time
from pathlib import Path
from typing import Dict, Optional, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)


class NetlifyDeploymentError(Exception):
    """Custom exception for Netlify deployment errors"""
    pass


class NetlifyDeployer:
    """Handle Netlify deployments using the File Digest method"""
    
    def __init__(self, access_token: str, base_url: str = "https://api.netlify.com/api/v1"):
        self.access_token = access_token
        self.base_url = base_url
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "POST", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        })
        return session
    
    def create_site(self, site_name: Optional[str] = None) -> Dict:
        """
        Create a new Netlify site.
        Returns site information including site_id.
        """
        try:
            payload = {}
            if site_name:
                payload["name"] = site_name
            
            response = self.session.post(
                f"{self.base_url}/sites",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            site = response.json()
            logger.info(f"Created new Netlify site: {site['id']} - {site.get('name', 'unnamed')}")
            return site
        except requests.exceptions.HTTPError as e:
            error_msg = f"Failed to create site: {e.response.status_code}"
            if e.response.text:
                error_msg += f" - {e.response.text}"
            logger.error(error_msg)
            raise NetlifyDeploymentError(error_msg)
        except Exception as e:
            logger.error(f"Unexpected error creating site: {str(e)}")
            raise NetlifyDeploymentError(f"Failed to create site: {str(e)}")
    
    def compute_file_hashes(self, directory: Path) -> Dict[str, str]:
        """
        Compute SHA1 hashes for all files in a directory.
        Returns a dict mapping relative paths to SHA1 hashes.
        """
        hashes = {}
        if not directory.exists():
            raise NetlifyDeploymentError(f"Directory {directory} does not exist")
        
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                # Get relative path using forward slashes
                relative_path = file_path.relative_to(directory)
                relative_path_str = str(relative_path).replace("\\", "/")
                
                # Compute SHA1 hash in binary mode
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.sha1(f.read()).hexdigest()
                    hashes[relative_path_str] = file_hash
        
        logger.info(f"Computed hashes for {len(hashes)} files")
        return hashes
    
    def create_deployment(self, site_id: str, files_dict: Dict[str, str]) -> Dict:
        """
        Create a deployment manifest with Netlify.
        Returns the deployment object including required files list.
        """
        deploy_data = {
            "files": files_dict,
            "async": True  # Use async mode for better reliability
        }
        
        logger.info(f"Creating deployment for site {site_id} with {len(files_dict)} files")
        
        try:
            response = self.session.post(
                f"{self.base_url}/sites/{site_id}/deploys",
                json=deploy_data,
                timeout=30
            )
            response.raise_for_status()
            deployment = response.json()
            logger.info(f"Deployment created: {deployment['id']}, state: {deployment['state']}")
            return deployment
        except requests.exceptions.HTTPError as e:
            error_msg = f"Failed to create deployment: {e.response.status_code}"
            if e.response.text:
                error_msg += f" - {e.response.text}"
            logger.error(error_msg)
            raise NetlifyDeploymentError(error_msg)
        except Exception as e:
            logger.error(f"Unexpected error creating deployment: {str(e)}")
            raise NetlifyDeploymentError(f"Failed to create deployment: {str(e)}")
    
    def upload_file(self, deploy_id: str, file_path: Path, relative_path: str) -> bool:
        """
        Upload a single file to Netlify.
        Returns True if successful, False otherwise.
        """
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Remove leading slash and ensure proper URL encoding
            upload_path = relative_path.lstrip('/')
            upload_url = f"{self.base_url}/deploys/{deploy_id}/files/{upload_path}"
            
            response = self.session.put(
                upload_url,
                data=file_content,
                headers={"Content-Type": "application/octet-stream"},
                timeout=60
            )
            
            if response.status_code == 422:
                logger.error(f"SHA1 mismatch for file: {relative_path}")
                return False
            
            response.raise_for_status()
            logger.debug(f"Uploaded: {relative_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload {relative_path}: {str(e)}")
            return False
    
    def get_deployment_status(self, deploy_id: str) -> Dict:
        """Get the current status of a deployment"""
        try:
            response = self.session.get(f"{self.base_url}/deploys/{deploy_id}", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get deployment status: {str(e)}")
            raise NetlifyDeploymentError(f"Failed to get deployment status: {str(e)}")
    
    def wait_for_ready_state(self, deploy_id: str, max_attempts: int = 30) -> Dict:
        """
        Poll deployment until it's ready for file uploads.
        Returns the deployment object when ready.
        """
        for attempt in range(max_attempts):
            deployment = self.get_deployment_status(deploy_id)
            state = deployment['state']
            
            logger.info(f"Deployment {deploy_id} state: {state} (attempt {attempt + 1}/{max_attempts})")
            
            if state in ['prepared', 'ready']:
                return deployment
            elif state == 'error':
                raise NetlifyDeploymentError(f"Deployment entered error state: {deployment.get('error_message', 'Unknown error')}")
            
            time.sleep(2)
        
        raise NetlifyDeploymentError(f"Deployment did not become ready within {max_attempts * 2} seconds")
    
    def deploy_directory(self, directory: str, site_id: Optional[str] = None, site_name: Optional[str] = None) -> Dict:
        """
        Deploy a complete directory to Netlify.
        If site_id is not provided, creates a new site automatically.
        Returns deployment information including URL and site_id.
        """
        directory_path = Path(directory)
        
        # Create new site if no site_id provided
        if not site_id:
            logger.info("No site_id provided, creating new Netlify site...")
            site = self.create_site(site_name)
            site_id = site['id']
            logger.info(f"Using new site: {site_id}")
        
        # Step 1: Compute hashes for all files
        logger.info(f"Starting deployment of {directory} to site {site_id}")
        files_dict = self.compute_file_hashes(directory_path)
        
        if not files_dict:
            raise NetlifyDeploymentError("No files found to deploy")
        
        # Step 2: Create deployment manifest
        deployment = self.create_deployment(site_id, files_dict)
        deploy_id = deployment['id']
        
        # Step 3: Wait for deployment to be ready for uploads (if in preparing state)
        if deployment.get('state') == 'preparing':
            logger.info("Waiting for deployment to be ready for uploads...")
            deployment = self.wait_for_ready_state(deploy_id)
        
        # Step 4: Upload required files
        required_files = deployment.get('required', [])
        logger.info(f"Need to upload {len(required_files)} files")
        
        uploaded = 0
        failed = 0
        
        for file_path in required_files:
            actual_file_path = directory_path / file_path
            if actual_file_path.exists():
                if self.upload_file(deploy_id, actual_file_path, file_path):
                    uploaded += 1
                else:
                    failed += 1
            else:
                logger.warning(f"Required file not found: {file_path}")
                failed += 1
        
        logger.info(f"Upload complete: {uploaded} succeeded, {failed} failed")
        
        if failed > 0:
            raise NetlifyDeploymentError(f"Failed to upload {failed} files")
        
        # Step 5: Get final deployment status
        final_deployment = self.get_deployment_status(deploy_id)
        
        return {
            "deploy_id": final_deployment['id'],
            "site_id": site_id,
            "state": final_deployment['state'],
            "url": final_deployment.get('deploy_ssl_url') or final_deployment.get('ssl_url'),
            "site_name": final_deployment.get('name'),
            "created_at": final_deployment.get('created_at'),
            "published_at": final_deployment.get('published_at')
        }
        
        # Step 1: Compute hashes for all files
        logger.info(f"Starting deployment of {directory} to site {site_id}")
        files_dict = self.compute_file_hashes(directory_path)
        
        if not files_dict:
            raise NetlifyDeploymentError("No files found to deploy")
        
        # Step 2: Create deployment manifest
        deployment = self.create_deployment(site_id, files_dict)
        deploy_id = deployment['id']
        
        # Step 3: Wait for deployment to be ready for uploads (if in preparing state)
        if deployment.get('state') == 'preparing':
            logger.info("Waiting for deployment to be ready for uploads...")
            deployment = self.wait_for_ready_state(deploy_id)
        
        # Step 4: Upload required files
        required_files = deployment.get('required', [])
        logger.info(f"Need to upload {len(required_files)} files")
        
        uploaded = 0
        failed = 0
        
        for file_path in required_files:
            actual_file_path = directory_path / file_path
            if actual_file_path.exists():
                if self.upload_file(deploy_id, actual_file_path, file_path):
                    uploaded += 1
                else:
                    failed += 1
            else:
                logger.warning(f"Required file not found: {file_path}")
                failed += 1
        
        logger.info(f"Upload complete: {uploaded} succeeded, {failed} failed")
        
        if failed > 0:
            raise NetlifyDeploymentError(f"Failed to upload {failed} files")
        
        # Step 5: Get final deployment status
        final_deployment = self.get_deployment_status(deploy_id)
        
        return {
            "deploy_id": final_deployment['id'],
            "state": final_deployment['state'],
            "url": final_deployment.get('deploy_ssl_url') or final_deployment.get('ssl_url'),
            "site_name": final_deployment.get('name'),
            "created_at": final_deployment.get('created_at'),
            "published_at": final_deployment.get('published_at')
        }
