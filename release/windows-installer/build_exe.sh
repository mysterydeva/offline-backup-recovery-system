#!/bin/bash
# Enterprise Backup System - PyInstaller Build Script for Linux
# This script builds the standalone executable using PyInstaller

echo "========================================"
echo "Enterprise Backup System - EXE Builder"
echo "========================================"
echo

# Check if virtual environment exists
if [ ! -d "../../app/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "../../app/venv"
fi

# Activate virtual environment
source "../../app/venv/bin/activate"

# Install requirements
echo "Installing requirements..."
pip install -r "../../app/requirements.txt"
pip install pyinstaller

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Create package directory structure
echo "Creating package directory..."
mkdir -p package/{templates,storage/backups,logs,restored,sandbox_restore,config}

# Copy configuration files
echo "Copying configuration files..."
cp "../../app/config_phase3.json" package/
cp "../../app/config.json" package/ 2>/dev/null || true
cp "../../app/requirements.txt" package/

# Copy templates directory
cp -r "../../app/templates" package/

# Build the executable
echo "Building executable with PyInstaller..."
pyinstaller --onefile --noconsole --name "BackupSystem" --add-data "package:package" run_app.py

# Check if build was successful
if [ -f "dist/BackupSystem" ]; then
    echo
    echo "========================================"
    echo "BUILD SUCCESSFUL!"
    echo "========================================"
    echo
    echo "Copying executable to package directory..."
    cp "dist/BackupSystem" package/
    
    echo
    echo "Package contents:"
    ls -la package/
    
    echo
    echo "Executable created: package/BackupSystem"
    echo "Package directory: $(pwd)/package"
    echo
    echo "Note: This is a Linux build. For Windows deployment,"
    echo "run build_exe.bat on a Windows machine."
    echo
else
    echo
    echo "========================================"
    echo "BUILD FAILED!"
    echo "========================================"
    echo
    echo "Please check the error messages above."
fi

echo "Press Enter to continue..."
read
