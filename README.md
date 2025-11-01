# React Static Site Builder

A powerful desktop and web application for converting React projects into static sites with build, preview, and deployment capabilities.

## Features

- 🚀 **Multiple Input Methods**: Upload ZIP files, paste code, or clone from GitHub
- 🔨 **Automatic Building**: Supports both Create React App and Vite projects
- 👁️ **Live Preview**: Preview your built sites instantly
- 📦 **Download Builds**: Get your static files as ZIP archives
- ☁️ **Netlify Deployment**: Deploy directly to Netlify with your own credentials
- 💻 **Desktop & Web**: Available as both desktop application and web service

## Desktop Application

### Features
- ✅ **No Database Required**: Uses JSON file storage
- ✅ **Pre-bundled Python**: Python runtime included in installer
- ✅ **Auto-port Detection**: Automatically finds available ports (8000-9000)
- ✅ **System Tray**: Start/stop controls from Windows system tray
- ✅ **Offline Capable**: Works without internet (except for npm installs)
- ✅ **Windows Installer**: Easy-to-use `.exe` installer (~150MB)

### Desktop Build Instructions

See [DESKTOP_BUILD_README.md](DESKTOP_BUILD_README.md) for complete desktop build instructions.

**Quick Start:**
```bash
# Build frontend
cd frontend
yarn build

# Setup Python (optional - for bundling)
cd ..
./setup-python-embed.sh

# Build desktop installer
cd electron
yarn install
yarn build
```

The installer will be in `electron/dist/`.

## Documentation

- [Desktop Build Guide](DESKTOP_BUILD_README.md) - Complete desktop build instructions
- [Implementation Guide](DESKTOP_IMPLEMENTATION_GUIDE.md) - Technical implementation details
- [Branding Removal](BRANDING_REMOVAL_SUMMARY.md) - White-label customization

## Project Structure

```
/app/
├── backend/                    # Python FastAPI backend
│   ├── server.py              # Web version (MongoDB)
│   ├── server_standalone.py   # Desktop version (JSON)
│   ├── json_storage.py        # JSON database implementation
│   ├── port_utils.py          # Port auto-detection
│   └── netlify_deployer.py    # Netlify deployment handler
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── pages/             # Main pages (Home, BuildDetails)
│   │   ├── components/        # Reusable UI components
│   │   └── utils/             # Utility functions
│   └── public/                # Static assets
│
├── electron/                   # Electron desktop app
│   ├── main.js                # Main process
│   ├── preload.js             # Secure IPC bridge
│   └── package.json           # Electron build config
│
└── scripts/                    # Build and setup scripts
```

## System Requirements

### Desktop Version
- Windows 10/11 (64-bit)
- Git (for GitHub cloning)
- Yarn (for building React projects)
- ~200MB free disk space for installation

## License

MIT License - See LICENSE file for details

---

**Version**: 1.0.0  
**Status**: Production Ready
