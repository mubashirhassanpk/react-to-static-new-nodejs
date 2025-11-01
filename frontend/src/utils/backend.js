/**
 * Backend URL configuration for web and Electron environments
 */

/**
 * Get the backend URL based on the environment
 * @returns {string} The backend URL
 */
export function getBackendUrl() {
  // Check if running in Electron
  if (window.electronAPI) {
    // Try to get from localStorage first (set by Electron main process)
    const electronBackendUrl = localStorage.getItem('BACKEND_URL');
    if (electronBackendUrl) {
      return electronBackendUrl;
    }
    
    // Fallback to default port
    return 'http://127.0.0.1:8000';
  }
  
  // Web environment - use environment variable
  return process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
}

/**
 * Get the API base URL
 * @returns {string} The API base URL
 */
export function getApiUrl() {
  return `${getBackendUrl()}/api`;
}

/**
 * Check if running in Electron
 * @returns {boolean} True if running in Electron
 */
export function isElectron() {
  return !!(window.electronAPI);
}

/**
 * Get app version (works in both web and Electron)
 * @returns {Promise<string>} The app version
 */
export async function getAppVersion() {
  if (window.electronAPI) {
    return await window.electronAPI.getAppVersion();
  }
  return process.env.REACT_APP_VERSION || '1.0.0';
}
