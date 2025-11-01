#!/bin/bash
# Script to download and setup Python embeddable package for Windows

set -e

PYTHON_VERSION="3.11.7"
PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-embed-amd64.zip"
PYTHON_DIR="/app/electron/python-embed"

echo "========================================"
echo "Python Embeddable Setup"
echo "========================================"
echo ""

echo "Downloading Python ${PYTHON_VERSION} embeddable package..."
mkdir -p "$PYTHON_DIR"
cd "$PYTHON_DIR"

# Download Python embeddable
if command -v wget &> /dev/null; then
    wget "$PYTHON_URL" -O python-embed.zip
elif command -v curl &> /dev/null; then
    curl -L "$PYTHON_URL" -o python-embed.zip
else
    echo "Error: Neither wget nor curl is available"
    exit 1
fi

echo "Extracting Python..."
unzip -q python-embed.zip
rm python-embed.zip

echo "Setting up pip..."
# Download get-pip.py
if command -v wget &> /dev/null; then
    wget https://bootstrap.pypa.io/get-pip.py
elif command -v curl &> /dev/null; then
    curl -L https://bootstrap.pypa.io/get-pip.py -o get-pip.py
fi

# Install pip
./python.exe get-pip.py
rm get-pip.py

echo "Installing Python dependencies..."
cd /app/backend
./python-embed/python.exe -m pip install -r requirements_standalone.txt --target "$PYTHON_DIR/Lib/site-packages"

echo ""
echo "========================================"
echo "Python Setup Complete!"
echo "========================================"
echo ""
echo "Python location: $PYTHON_DIR"
echo ""
echo "You can now build the Electron app with:"
echo "  cd /app/electron"
echo "  yarn build"
echo ""
