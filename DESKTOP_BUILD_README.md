# React Static Builder - Desktop Application

A standalone Windows desktop application for building React projects into static sites without requiring any external dependencies.

## Features

- ✅ **No Database Required**: Uses JSON file storage
- ✅ **Pre-bundled Python**: Python runtime included in the installer
- ✅ **Auto-port Detection**: Automatically finds available ports
- ✅ **System Tray Integration**: Start/stop controls from system tray
- ✅ **Completely Offline**: Works without internet connection (except for building React apps and Netlify deployment)
- ✅ **Windows Installer**: Easy-to-use `.exe` installer

## Project Structure

```
/app/
├── backend/                    # Python FastAPI backend
│   ├── server_standalone.py   # Standalone server with JSON storage
│   ├── json_storage.py        # JSON-based database replacement
│   ├── port_utils.py          # Port auto-detection utilities
│   └── requirements_standalone.txt  # Python dependencies (no MongoDB)
│
├── electron/                   # Electron desktop app
│   ├── main.js                # Main Electron process
│   ├── preload.js             # Preload script for security
│   ├── package.json           # Electron dependencies and build config
│   └── icon.png               # App icon (to be added)
│
└── frontend/                   # React frontend
    └── src/
        └── utils/
            └── backend.js     # Backend URL configuration utility
```

## Building the Desktop Application

### Prerequisites

1. **Node.js and Yarn** (for building React app and Electron)
2. **Python 3.9+** (for development only)
3. **Git** (for cloning repositories in the app)

### Step 1: Build the Frontend

```bash
cd /app/frontend
yarn install
yarn build
```

This creates an optimized production build in `/app/frontend/build/`.

### Step 2: Prepare Python Backend

#### Option A: Using Python Embeddable Package (Recommended for Windows)

1. Download Python embeddable package:
   ```bash
   # Download from https://www.python.org/downloads/windows/
   # Look for "Windows embeddable package (64-bit)"
   # Example: python-3.11.7-embed-amd64.zip
   ```

2. Extract to `/app/electron/python-embed/`

3. Install dependencies:
   ```bash
   cd /app/backend
   pip install -r requirements_standalone.txt -t ../electron/python-embed/Lib/site-packages
   ```

#### Option B: Using PyInstaller (Alternative)

```bash
cd /app/backend
pip install pyinstaller
pyinstaller --onefile --add-data "netlify_deployer.py;." --add-data "json_storage.py;." --add-data "port_utils.py;." server_standalone.py
```

### Step 3: Install Electron Dependencies

```bash
cd /app/electron
yarn install
```

### Step 4: Build the Windows Installer

```bash
cd /app/electron
yarn build
```

This creates:
- Windows installer (`.exe`) in `/app/electron/dist/`
- Unpacked application in `/app/electron/dist/win-unpacked/`

### Step 5: Test the Build

Before distributing, test the packaged application:

```bash
cd /app/electron
yarn build:dir  # Build without creating installer
# Then run the app from dist/win-unpacked/
```

## Development Mode

To run in development mode without building:

### Terminal 1: Start Backend
```bash
cd /app/backend
python server_standalone.py
```

### Terminal 2: Start Frontend (if needed)
```bash
cd /app/frontend
yarn start
```

### Terminal 3: Start Electron
```bash
cd /app/electron
yarn start
```

## Configuration

### Port Configuration

The app automatically detects available ports between 8000-9000. The port is stored in:
- `server_port.txt` (created by backend)
- `localStorage` (in Electron renderer process)

### Data Storage

All data is stored in JSON format:
- **Builds Database**: `/app/backend/data/builds.json`
- **Build Files**: `/app/backend/builds/`

### System Tray

The app runs in the system tray with the following options:
- **Show App**: Opens the main window
- **Hide App**: Hides the main window
- **Restart Backend**: Restarts the Python backend server
- **Quit**: Completely exits the application

## Distribution

### Installer Size

Expected installer size: ~60-150 MB depending on Python bundling method

- Python embeddable: ~60-80 MB
- PyInstaller: ~50-70 MB  
- Electron app base: ~120-150 MB
- **Total**: ~150-200 MB

### What's Included

- ✅ Python runtime
- ✅ All Python dependencies
- ✅ React frontend (built)
- ✅ Electron runtime
- ✅ Node modules (for Electron only)

### What's NOT Included (External Requirements)

- ❌ Git (required for GitHub cloning feature)
- ❌ Yarn (required for building React apps)
- ❌ Internet connection (for NPM installs and Netlify deployment)

## Troubleshooting

### Backend Won't Start

1. Check if port is available
2. Look at logs in console
3. Try restarting from system tray

### Build Fails

1. Ensure Yarn is installed globally
2. Check Git is installed for GitHub repos
3. Verify internet connection for NPM installs

### Electron Build Issues

1. Make sure frontend is built first (`cd frontend && yarn build`)
2. Verify Python backend files are present
3. Check `electron/package.json` build configuration

## Future Enhancements

- [ ] Mac and Linux support
- [ ] Auto-updates
- [ ] Build notifications
- [ ] Build history management
- [ ] Custom build configurations
- [ ] Integrated Git installation
- [ ] Bundled Yarn for offline builds

## Technical Details

### Technologies Used

- **Frontend**: React 19, Tailwind CSS, Radix UI
- **Backend**: FastAPI, Python 3.9+
- **Desktop**: Electron 28
- **Storage**: JSON file-based
- **Build Tool**: electron-builder

### Architecture

```
User Interface (Electron BrowserWindow)
    ↓
Frontend (React) ← reads backend URL from Electron
    ↓
Backend API (FastAPI) ← auto-detected port
    ↓
JSON Storage (builds.json) + File System (build files)
```

### Security

- Context isolation enabled
- Node integration disabled
- Preload script for secure IPC
- CORS configured for local access only

## License

MIT License - Feel free to use and modify as needed.

## Support

For issues and questions, please open an issue on GitHub.
