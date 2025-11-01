#!/bin/bash
# Build script for React Static Builder Desktop Application
# This script builds the complete Windows installer

set -e  # Exit on error

echo "========================================"
echo "React Static Builder - Desktop Build"
echo "========================================"
echo ""

# Check if we're in the correct directory
if [ ! -d "backend" ]; then
    echo "Error: Please run this script from the /app directory"
    exit 1
fi

echo "Step 1: Building React Frontend..."
echo "========================================"
cd frontend
yarn install
yarn build
cd ..
echo "Frontend build complete!"
echo ""

echo "Step 2: Preparing Python Backend..."
echo "========================================"
# Copy standalone files to ensure they're up to date
cp -f backend/server_standalone.py backend/server.py.bak 2>/dev/null || true
cp -f backend/json_storage.py backend/ 2>/dev/null || true
cp -f backend/port_utils.py backend/ 2>/dev/null || true
echo "Python backend files prepared!"
echo ""

echo "Step 3: Installing Electron Dependencies..."
echo "========================================"
cd electron
yarn install
echo "Electron dependencies installed!"
echo ""

echo "Step 4: Building Windows Installer..."
echo "========================================"
yarn build
cd ..
echo ""

echo "========================================"
echo "Build Complete!"
echo "========================================"
echo ""
echo "Installer location: electron/dist/"
echo ""
echo "To test the application:"
echo "  1. Navigate to electron/dist/win-unpacked/"
echo "  2. Run 'React Static Builder.exe'"
echo ""
echo "To distribute:"
echo "  Use the .exe installer in electron/dist/"
echo ""
