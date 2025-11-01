const { app, BrowserWindow, Tray, Menu, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const axios = require('axios');

let mainWindow = null;
let tray = null;
let backendProcess = null;
let backendPort = null;
let backendUrl = null;

// Determine if running in development or production
const isDev = !app.isPackaged;

// Paths configuration
const PYTHON_PATH = isDev
  ? 'python'  // Use system Python in dev
  : path.join(process.resourcesPath, 'python', 'python-embed', 'python.exe');

const BACKEND_SCRIPT = isDev
  ? path.join(__dirname, '..', 'backend', 'server_standalone.py')
  : path.join(process.resourcesPath, 'python', 'server_standalone.py');

const BACKEND_DIR = isDev
  ? path.join(__dirname, '..', 'backend')
  : path.join(process.resourcesPath, 'python');

const FRONTEND_PATH = isDev
  ? path.join(__dirname, '..', 'frontend', 'build', 'index.html')
  : path.join(process.resourcesPath, 'frontend', 'index.html');

// Logging helper
function log(message) {
  console.log(`[Electron Main] ${message}`);
}

// Find available port
function findAvailablePort(startPort = 8000, endPort = 9000) {
  const net = require('net');
  
  return new Promise((resolve, reject) => {
    function tryPort(port) {
      if (port > endPort) {
        reject(new Error('No available ports found'));
        return;
      }
      
      const server = net.createServer();
      
      server.once('error', (err) => {
        if (err.code === 'EADDRINUSE') {
          tryPort(port + 1);
        } else {
          reject(err);
        }
      });
      
      server.once('listening', () => {
        server.close();
        resolve(port);
      });
      
      server.listen(port, '127.0.0.1');
    }
    
    tryPort(startPort);
  });
}

// Start Python backend server
async function startBackend() {
  return new Promise(async (resolve, reject) => {
    try {
      log('Starting Python backend...');
      
      // Find available port
      backendPort = await findAvailablePort(8000, 9000);
      backendUrl = `http://127.0.0.1:${backendPort}`;
      log(`Using port: ${backendPort}`);
      
      // Set environment variables
      const env = {
        ...process.env,
        BACKEND_PORT: backendPort.toString(),
        CORS_ORIGINS: '*'
      };
      
      // Start Python process
      backendProcess = spawn(PYTHON_PATH, [BACKEND_SCRIPT], {
        cwd: BACKEND_DIR,
        env: env,
        stdio: ['ignore', 'pipe', 'pipe']
      });
      
      // Handle backend output
      backendProcess.stdout.on('data', (data) => {
        log(`Backend stdout: ${data.toString().trim()}`);
      });
      
      backendProcess.stderr.on('data', (data) => {
        log(`Backend stderr: ${data.toString().trim()}`);
      });
      
      backendProcess.on('error', (error) => {
        log(`Backend process error: ${error.message}`);
        reject(error);
      });
      
      backendProcess.on('exit', (code, signal) => {
        log(`Backend process exited with code ${code} and signal ${signal}`);
        if (code !== 0 && code !== null) {
          reject(new Error(`Backend exited with code ${code}`));
        }
      });
      
      // Wait for backend to be ready
      let attempts = 0;
      const maxAttempts = 30;
      
      const checkBackend = async () => {
        try {
          const response = await axios.get(`${backendUrl}/api/`, { timeout: 1000 });
          if (response.status === 200) {
            log('Backend is ready!');
            resolve(backendUrl);
            return;
          }
        } catch (error) {
          // Backend not ready yet
        }
        
        attempts++;
        if (attempts >= maxAttempts) {
          reject(new Error('Backend failed to start within timeout'));
          return;
        }
        
        setTimeout(checkBackend, 1000);
      };
      
      // Start checking after 2 seconds
      setTimeout(checkBackend, 2000);
      
    } catch (error) {
      log(`Failed to start backend: ${error.message}`);
      reject(error);
    }
  });
}

// Stop backend server
function stopBackend() {
  if (backendProcess) {
    log('Stopping Python backend...');
    backendProcess.kill();
    backendProcess = null;
  }
}

// Create main window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    icon: path.join(__dirname, 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });
  
  // Load frontend
  if (isDev) {
    // In development, load from local file but inject backend URL
    mainWindow.loadFile(FRONTEND_PATH);
  } else {
    mainWindow.loadFile(FRONTEND_PATH);
  }
  
  // Inject backend URL into frontend
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.webContents.executeJavaScript(`
      window.BACKEND_URL = '${backendUrl}';
      localStorage.setItem('BACKEND_URL', '${backendUrl}');
    `);
  });
  
  // Open DevTools in development
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }
  
  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
  
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Create system tray
function createTray() {
  // For now, use a simple icon (you can replace with a proper icon later)
  const iconPath = path.join(__dirname, 'icon.png');
  
  tray = new Tray(iconPath);
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Reactly',
      enabled: false
    },
    {
      type: 'separator'
    },
    {
      label: 'Show App',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
        } else {
          createWindow();
        }
      }
    },
    {
      label: 'Hide App',
      click: () => {
        if (mainWindow) {
          mainWindow.hide();
        }
      }
    },
    {
      type: 'separator'
    },
    {
      label: `Backend: Running on port ${backendPort || 'N/A'}`,
      enabled: false
    },
    {
      label: 'Restart Backend',
      click: async () => {
        stopBackend();
        try {
          await startBackend();
          dialog.showMessageBox({
            type: 'info',
            title: 'Backend Restarted',
            message: `Backend successfully restarted on port ${backendPort}`
          });
        } catch (error) {
          dialog.showErrorBox('Backend Error', `Failed to restart backend: ${error.message}`);
        }
      }
    },
    {
      type: 'separator'
    },
    {
      label: 'Quit',
      click: () => {
        app.isQuitting = true;
        app.quit();
      }
    }
  ]);
  
  tray.setToolTip('React Static Builder');
  tray.setContextMenu(contextMenu);
  
  tray.on('double-click', () => {
    if (mainWindow) {
      mainWindow.show();
    } else {
      createWindow();
    }
  });
}

// App lifecycle
app.whenReady().then(async () => {
  try {
    log('App is ready, starting backend...');
    await startBackend();
    log('Backend started successfully');
    
    createWindow();
    createTray();
    
    log('App initialization complete');
  } catch (error) {
    log(`Failed to initialize app: ${error.message}`);
    dialog.showErrorBox(
      'Startup Error',
      `Failed to start the application:\n${error.message}\n\nPlease check the logs and try again.`
    );
    app.quit();
  }
});

app.on('window-all-closed', () => {
  // Don't quit on window close - keep running in tray
  // Only quit if explicitly requested
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  log('App is quitting...');
  stopBackend();
});

// Handle IPC messages from renderer
ipcMain.handle('get-backend-url', () => {
  return backendUrl;
});

ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  log(`Uncaught exception: ${error.message}`);
  console.error(error);
});

process.on('unhandledRejection', (reason, promise) => {
  log(`Unhandled rejection at: ${promise}, reason: ${reason}`);
  console.error(reason);
});
