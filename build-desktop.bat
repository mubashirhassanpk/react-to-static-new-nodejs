@echo off
REM Build script for React Static Builder Desktop Application
REM This script builds the complete Windows installer

echo ========================================
echo React Static Builder - Desktop Build
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "backend" (
    echo Error: Please run this script from the /app directory
    exit /b 1
)

echo Step 1: Building React Frontend...
echo ========================================
cd frontend
call yarn install
if errorlevel 1 (
    echo Error: Failed to install frontend dependencies
    exit /b 1
)

call yarn build
if errorlevel 1 (
    echo Error: Failed to build frontend
    exit /b 1
)
cd ..
echo Frontend build complete!
echo.

echo Step 2: Preparing Python Backend...
echo ========================================
REM Copy standalone files to ensure they're up to date
copy /Y backend\server_standalone.py backend\server.py.bak 2>nul
copy /Y backend\json_storage.py backend\ 2>nul
copy /Y backend\port_utils.py backend\ 2>nul
echo Python backend files prepared!
echo.

echo Step 3: Installing Electron Dependencies...
echo ========================================
cd electron
call yarn install
if errorlevel 1 (
    echo Error: Failed to install Electron dependencies
    exit /b 1
)
echo Electron dependencies installed!
echo.

echo Step 4: Building Windows Installer...
echo ========================================
call yarn build
if errorlevel 1 (
    echo Error: Failed to build Windows installer
    exit /b 1
)
cd ..
echo.

echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Installer location: electron\dist\
echo.
echo To test the application:
echo   1. Navigate to electron\dist\win-unpacked\
echo   2. Run React Static Builder.exe
echo.
echo To distribute:
echo   Use the .exe installer in electron\dist\
echo.
pause
