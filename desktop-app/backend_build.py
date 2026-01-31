#!/usr/bin/env python3
"""
Backend build script for Enterprise Backup System
Automates the PyInstaller build process for the FastAPI backend
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    """Build the backend executable using PyInstaller"""
    
    # Configuration
    script_dir = Path(__file__).parent
    app_dir = script_dir.parent / "app"
    backend_dir = script_dir / "backend"
    dist_dir = script_dir / "dist"
    
    print("🔧 Enterprise Backup System - Backend Builder")
    print("=" * 50)
    
    # Check if app directory exists
    if not app_dir.exists():
        print(f"❌ App directory not found: {app_dir}")
        return 1
    
    # Check if main_fixed.py exists
    main_script = app_dir / "main_fixed.py"
    if not main_script.exists():
        print(f"❌ Main script not found: {main_script}")
        return 1
    
    print(f"📁 App directory: {app_dir}")
    print(f"📄 Main script: {main_script}")
    print(f"📦 Output directory: {dist_dir}")
    
    # Clean previous builds
    print("\n🧹 Cleaning previous builds...")
    for cleanup_dir in [dist_dir, backend_dir, script_dir / "build"]:
        if cleanup_dir.exists():
            shutil.rmtree(cleanup_dir)
            print(f"   Removed: {cleanup_dir}")
    
    # Create backend directory
    backend_dir.mkdir(parents=True, exist_ok=True)
    
    # Run PyInstaller
    print("\n🏗️ Building backend executable...")
    try:
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            str(script_dir / "backend_build.spec"),
            "--noconfirm"
        ]
        
        print(f"🚀 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=script_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ PyInstaller failed:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return 1
        
        print("✅ PyInstaller completed successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return 1
    except FileNotFoundError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("🔄 Retrying build...")
        return main()  # Retry after installation
    
    # Check if executable was created
    exe_path = dist_dir / "BackupBackend.exe"
    if not exe_path.exists():
        print(f"❌ Executable not found: {exe_path}")
        return 1
    
    print(f"✅ Backend executable created: {exe_path}")
    print(f"📊 Size: {exe_path.stat().st_size:,} bytes")
    
    # Copy to backend directory
    backend_exe = backend_dir / "BackupBackend.exe"
    shutil.copy2(exe_path, backend_exe)
    print(f"📋 Copied to: {backend_exe}")
    
    # Test the executable (basic check)
    print("\n🧪 Testing executable...")
    try:
        # Just check if it runs without errors for a short time
        process = subprocess.Popen([str(backend_exe)], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  text=True)
        
        # Wait a bit to see if it starts
        try:
            stdout, stderr = process.communicate(timeout=3)
            print(f"📝 STDOUT: {stdout[:200]}...")
            if stderr:
                print(f"⚠️ STDERR: {stderr[:200]}...")
        except subprocess.TimeoutExpired:
            process.terminate()
            print("✅ Executable starts successfully (terminated after test)")
        
    except Exception as e:
        print(f"⚠️ Could not test executable: {e}")
    
    print("\n🎉 Backend build completed successfully!")
    print(f"📦 Executable: {backend_exe}")
    print(f"🚀 Ready for Electron integration")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
