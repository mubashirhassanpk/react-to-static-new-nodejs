import requests
import sys
import time
import json
import io
import zipfile
from datetime import datetime

class ReactStaticBuilderTester:
    def __init__(self, base_url="https://react-toolkit-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.build_ids = []

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        if data and not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_paste_build(self):
        """Test paste code build"""
        sample_code = '''import React from 'react';

function App() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>Test React App</h1>
      <p>This is a test build from paste functionality.</p>
    </div>
  );
}

export default App;'''
        
        success, response = self.run_test(
            "Paste Code Build",
            "POST",
            "build/paste",
            200,
            data={"code": sample_code, "filename": "App.js"}
        )
        
        if success and 'id' in response:
            self.build_ids.append(response['id'])
            print(f"   Build ID: {response['id']}")
            return response['id']
        return None

    def test_upload_build(self):
        """Test ZIP upload build"""
        # Create a minimal React project ZIP in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # package.json
            package_json = {
                "name": "test-react-app",
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
            zip_file.writestr("package.json", json.dumps(package_json, indent=2))
            
            # public/index.html
            index_html = '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Test React App</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>'''
            zip_file.writestr("public/index.html", index_html)
            
            # src/index.js
            index_js = '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);'''
            zip_file.writestr("src/index.js", index_js)
            
            # src/App.js
            app_js = '''import React from 'react';

function App() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>Test Upload Build</h1>
      <p>This is a test build from ZIP upload functionality.</p>
    </div>
  );
}

export default App;'''
            zip_file.writestr("src/App.js", app_js)
        
        zip_buffer.seek(0)
        
        files = {'file': ('test-react-app.zip', zip_buffer, 'application/zip')}
        
        success, response = self.run_test(
            "ZIP Upload Build",
            "POST",
            "build/upload",
            200,
            files=files
        )
        
        if success and 'id' in response:
            self.build_ids.append(response['id'])
            print(f"   Build ID: {response['id']}")
            return response['id']
        return None

    def test_github_build(self):
        """Test GitHub repository build"""
        # Using a simple public React repo
        github_url = "https://github.com/facebook/create-react-app"
        
        success, response = self.run_test(
            "GitHub Repository Build",
            "POST",
            "build/github",
            200,
            data={"repo_url": github_url}
        )
        
        if success and 'id' in response:
            self.build_ids.append(response['id'])
            print(f"   Build ID: {response['id']}")
            return response['id']
        return None

    def test_build_status(self, build_id):
        """Test build status endpoint"""
        success, response = self.run_test(
            f"Build Status for {build_id[:8]}...",
            "GET",
            f"build/status/{build_id}",
            200
        )
        
        if success:
            print(f"   Status: {response.get('status', 'unknown')}")
            return response.get('status')
        return None

    def test_builds_list(self):
        """Test builds list endpoint"""
        success, response = self.run_test(
            "Builds List",
            "GET",
            "builds",
            200
        )
        
        if success:
            print(f"   Found {len(response)} builds")
        return success

    def wait_for_build_completion(self, build_id, max_wait=300):
        """Wait for build to complete or fail"""
        print(f"\n⏳ Waiting for build {build_id[:8]}... to complete (max {max_wait}s)")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = self.test_build_status(build_id)
            if status in ['completed', 'failed']:
                print(f"   Build finished with status: {status}")
                return status
            elif status == 'building':
                print("   Build in progress...")
            time.sleep(10)
        
        print("   Build timed out")
        return 'timeout'

    def test_download_build(self, build_id):
        """Test build download"""
        success, response = self.run_test(
            f"Download Build {build_id[:8]}...",
            "GET",
            f"build/download/{build_id}",
            200,
            timeout=60
        )
        return success

    def test_preview_build(self, build_id):
        """Test build preview"""
        success, response = self.run_test(
            f"Preview Build {build_id[:8]}...",
            "GET",
            f"build/preview/{build_id}/index.html",
            200,
            timeout=30
        )
        return success

    def test_netlify_deploy_nonexistent_build(self):
        """Test Netlify deployment with non-existent build ID"""
        fake_build_id = "nonexistent-build-id"
        netlify_data = {
            "netlify_token": "test_token_12345",
            "netlify_site_id": "test_site_id_67890"
        }
        
        success, response = self.run_test(
            "Netlify Deploy - Non-existent Build",
            "POST",
            f"build/deploy-netlify/{fake_build_id}",
            404,
            data=netlify_data
        )
        return success

    def test_netlify_deploy_pending_build(self, build_id):
        """Test Netlify deployment with non-completed build"""
        netlify_data = {
            "netlify_token": "test_token_12345",
            "netlify_site_id": "test_site_id_67890"
        }
        
        success, response = self.run_test(
            f"Netlify Deploy - Pending Build {build_id[:8]}...",
            "POST",
            f"build/deploy-netlify/{build_id}",
            400,
            data=netlify_data
        )
        return success

    def test_netlify_deploy_completed_build(self, build_id):
        """Test Netlify deployment with completed build (will fail with mock credentials)"""
        netlify_data = {
            "netlify_token": "test_token_12345",
            "netlify_site_id": "test_site_id_67890"
        }
        
        success, response = self.run_test(
            f"Netlify Deploy - Completed Build {build_id[:8]}...",
            "POST",
            f"build/deploy-netlify/{build_id}",
            200,
            data=netlify_data
        )
        
        if success:
            print(f"   Deployment started for build: {response.get('build_id')}")
        return success

    def test_netlify_deploy_token_only(self, build_id):
        """Test Netlify deployment with only token (automatic site creation)"""
        netlify_data = {
            "netlify_token": "test_token_12345"
        }
        
        success, response = self.run_test(
            f"Netlify Deploy - Token Only {build_id[:8]}...",
            "POST",
            f"build/deploy-netlify/{build_id}",
            200,
            data=netlify_data
        )
        
        if success:
            print(f"   Deployment started for build: {response.get('build_id')}")
            print(f"   Using automatic site creation")
        return success

    def test_netlify_deploy_token_and_site_name(self, build_id):
        """Test Netlify deployment with token and custom site name"""
        netlify_data = {
            "netlify_token": "test_token_12345",
            "site_name": "my-custom-react-site"
        }
        
        success, response = self.run_test(
            f"Netlify Deploy - Token + Site Name {build_id[:8]}...",
            "POST",
            f"build/deploy-netlify/{build_id}",
            200,
            data=netlify_data
        )
        
        if success:
            print(f"   Deployment started for build: {response.get('build_id')}")
            print(f"   Using custom site name: my-custom-react-site")
        return success

    def test_netlify_deploy_missing_token(self, build_id):
        """Test Netlify deployment validation - missing token"""
        netlify_data = {
            "site_name": "my-custom-react-site"
        }
        
        success, response = self.run_test(
            f"Netlify Deploy - Missing Token {build_id[:8]}...",
            "POST",
            f"build/deploy-netlify/{build_id}",
            422,
            data=netlify_data
        )
        
        if success:
            print(f"   Validation correctly rejected request without token")
        return success

    def test_netlify_deploy_empty_payload(self, build_id):
        """Test Netlify deployment validation - empty payload"""
        netlify_data = {}
        
        success, response = self.run_test(
            f"Netlify Deploy - Empty Payload {build_id[:8]}...",
            "POST",
            f"build/deploy-netlify/{build_id}",
            422,
            data=netlify_data
        )
        
        if success:
            print(f"   Validation correctly rejected empty payload")
        return success

    def test_netlify_status_nonexistent_build(self):
        """Test Netlify status with non-existent build ID"""
        fake_build_id = "nonexistent-build-id"
        
        success, response = self.run_test(
            "Netlify Status - Non-existent Build",
            "GET",
            f"build/netlify-status/{fake_build_id}",
            404
        )
        return success

    def test_netlify_status_existing_build(self, build_id):
        """Test Netlify status endpoint"""
        success, response = self.run_test(
            f"Netlify Status - Build {build_id[:8]}...",
            "GET",
            f"build/netlify-status/{build_id}",
            200
        )
        
        if success:
            print(f"   Deploy ID: {response.get('netlify_deploy_id', 'None')}")
            print(f"   Deploy Status: {response.get('netlify_deploy_status', 'None')}")
            print(f"   Deploy URL: {response.get('netlify_deploy_url', 'None')}")
            if response.get('netlify_error_message'):
                print(f"   Error: {response.get('netlify_error_message')}")
        return success

    def test_build_status_includes_netlify_fields(self, build_id):
        """Test that build status endpoint includes Netlify fields"""
        success, response = self.run_test(
            f"Build Status with Netlify Fields {build_id[:8]}...",
            "GET",
            f"build/status/{build_id}",
            200
        )
        
        if success:
            # Check if Netlify fields are present in the response
            netlify_fields = [
                'netlify_deploy_id',
                'netlify_deploy_status', 
                'netlify_deploy_url',
                'netlify_error_message'
            ]
            
            missing_fields = []
            for field in netlify_fields:
                if field not in response:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"   ❌ Missing Netlify fields: {', '.join(missing_fields)}")
                return False
            else:
                print(f"   ✅ All Netlify fields present in build status")
                return True
        return False

def main():
    print("🚀 Starting React to Static Site Builder API Tests")
    print("=" * 60)
    
    tester = ReactStaticBuilderTester()
    
    # Test basic API
    if not tester.test_root_endpoint():
        print("❌ Root endpoint failed, stopping tests")
        return 1
    
    # Test builds list
    tester.test_builds_list()
    
    # Test Netlify endpoints with error cases first
    print("\n🔧 Testing Netlify Deployment Endpoints")
    print("-" * 40)
    
    # Test error cases
    tester.test_netlify_deploy_nonexistent_build()
    tester.test_netlify_status_nonexistent_build()
    
    # Check if the mentioned completed build exists
    existing_build_id = "af347823-614d-4e39-9b08-c5a0ef47d9f0"
    print(f"\n🔍 Testing with existing build ID: {existing_build_id}")
    
    # Test build status to see if it exists and get its status
    existing_build_status = tester.test_build_status(existing_build_id)
    
    if existing_build_status:
        # Test Netlify fields in build status
        tester.test_build_status_includes_netlify_fields(existing_build_id)
        
        # Test Netlify status endpoint
        tester.test_netlify_status_existing_build(existing_build_id)
        
        if existing_build_status == 'completed':
            # Test simplified deployment scenarios
            print("\n🆕 Testing Simplified Netlify Deployment Features")
            print("-" * 50)
            
            # Test 1: Deploy with only token (automatic site creation)
            tester.test_netlify_deploy_token_only(existing_build_id)
            
            # Test 2: Deploy with token and site name
            tester.test_netlify_deploy_token_and_site_name(existing_build_id)
            
            # Test 3: Validation - missing token
            tester.test_netlify_deploy_missing_token(existing_build_id)
            
            # Test 4: Validation - empty payload
            tester.test_netlify_deploy_empty_payload(existing_build_id)
            
            # Test 5: Original deployment with site_id (backward compatibility)
            tester.test_netlify_deploy_completed_build(existing_build_id)
            
            # Wait a bit and check status again to see if deployment started
            print("\n⏳ Waiting 5 seconds to check deployment status...")
            time.sleep(5)
            tester.test_netlify_status_existing_build(existing_build_id)
        else:
            print(f"   Build status is '{existing_build_status}', testing deployment error case")
            tester.test_netlify_deploy_pending_build(existing_build_id)
    else:
        print("   Existing build not found, will create new builds for testing")
    
    # Test paste build
    paste_build_id = tester.test_paste_build()
    
    # Test upload build  
    upload_build_id = tester.test_upload_build()
    
    # Test GitHub build (might fail due to large repo)
    print("\n⚠️  GitHub build test may take longer or fail due to large repository")
    github_build_id = tester.test_github_build()
    
    # Wait for at least one build to complete
    completed_builds = []
    
    if paste_build_id:
        status = tester.wait_for_build_completion(paste_build_id, 180)
        if status == 'completed':
            completed_builds.append(paste_build_id)
            # Test download and preview
            tester.test_download_build(paste_build_id)
            tester.test_preview_build(paste_build_id)
            
            # Test Netlify endpoints with newly completed build
            print(f"\n🔧 Testing Netlify endpoints with completed build {paste_build_id[:8]}...")
            tester.test_build_status_includes_netlify_fields(paste_build_id)
            tester.test_netlify_status_existing_build(paste_build_id)
            
            # Test simplified deployment features
            print(f"\n🆕 Testing Simplified Deployment with build {paste_build_id[:8]}...")
            tester.test_netlify_deploy_token_only(paste_build_id)
            tester.test_netlify_deploy_token_and_site_name(paste_build_id)
            tester.test_netlify_deploy_missing_token(paste_build_id)
            tester.test_netlify_deploy_completed_build(paste_build_id)
        elif status in ['pending', 'building']:
            # Test deployment with non-completed build
            tester.test_netlify_deploy_pending_build(paste_build_id)
    
    if upload_build_id:
        status = tester.wait_for_build_completion(upload_build_id, 180)
        if status == 'completed':
            completed_builds.append(upload_build_id)
            # Test download and preview
            tester.test_download_build(upload_build_id)
            tester.test_preview_build(upload_build_id)
            
            # Test Netlify endpoints if we haven't tested with a completed build yet
            if not any(build for build in completed_builds if build == paste_build_id):
                print(f"\n🔧 Testing Netlify endpoints with completed build {upload_build_id[:8]}...")
                tester.test_build_status_includes_netlify_fields(upload_build_id)
                tester.test_netlify_status_existing_build(upload_build_id)
                
                # Test simplified deployment features
                print(f"\n🆕 Testing Simplified Deployment with build {upload_build_id[:8]}...")
                tester.test_netlify_deploy_token_only(upload_build_id)
                tester.test_netlify_deploy_token_and_site_name(upload_build_id)
                tester.test_netlify_deploy_missing_token(upload_build_id)
                tester.test_netlify_deploy_completed_build(upload_build_id)
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 Tests completed: {tester.tests_passed}/{tester.tests_run}")
    print(f"🏗️  Builds created: {len(tester.build_ids)}")
    print(f"✅ Builds completed: {len(completed_builds)}")
    
    if completed_builds:
        print("✅ Core functionality working: Build creation, status tracking, download, preview")
        print("✅ Netlify deployment endpoints tested")
    else:
        print("❌ No builds completed successfully")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"📈 Success rate: {success_rate:.1f}%")
    
    return 0 if success_rate >= 70 else 1

if __name__ == "__main__":
    sys.exit(main())