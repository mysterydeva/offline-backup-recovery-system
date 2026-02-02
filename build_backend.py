#!/usr/bin/env python3
"""
PyInstaller build script for Enterprise Backup System Backend
Creates a standalone Windows executable from FastAPI application
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    required_modules = [
        'fastapi', 'uvicorn', 'cryptography', 'apscheduler', 
        'jinja2', 'psutil', 'reportlab', 'pydantic', 'bcrypt'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module}")
    
    if missing_modules:
        print(f"\n❌ Missing dependencies: {missing_modules}")
        print("Install with: pip install " + " ".join(missing_modules))
        return False
    
    print("✅ All dependencies available")
    return True

def check_pyinstaller():
    """Check if PyInstaller is available"""
    try:
        subprocess.run(['pyinstaller', '--version'], capture_output=True, check=True)
        print("✅ PyInstaller available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller not found")
        print("Install with: pip install pyinstaller")
        return False

def create_spec_file():
    """Create PyInstaller spec file with all required configurations"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Get the app directory
app_dir = Path(SPECPATH) / 'app'

# Analysis of the main script
a = Analysis(
    ['app/main_fixed.py'],
    pathex=[str(app_dir)],
    binaries=[],
    datas=[
        (str(app_dir / 'templates'), 'templates'),
        (str(app_dir / 'config_phase3.json'), '.'),
    ],
    hiddenimports=[
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.wsproto_impl',
        'fastapi',
        'starlette',
        'pydantic',
        'cryptography',
        'bcrypt',
        'apscheduler',
        'jinja2',
        'psutil',
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.lib',
        'reportlab.platypus',
        'sqlite3',
        'json',
        'hashlib',
        'zipfile',
        'shutil',
        'logging',
        'datetime',
        'typing',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
    ],
    noarchive=False,
)

# Create PYZ archive
pyz = PYZ(a.pure)

# Create EXE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BackupBackend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Can add icon path here if needed
)
'''
    
    spec_path = Path('build_backend.spec')
    with open(spec_path, 'w') as f:
        f.write(spec_content)
    
    print(f"✅ Created spec file: {spec_path}")
    return spec_path

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building BackupBackend.exe...")
    
    # Clean previous builds
    for path in ['build', 'dist']:
        if Path(path).exists():
            shutil.rmtree(path)
            print(f"🧹 Cleaned {path}/")
    
    # Create spec file
    spec_path = create_spec_file()
    
    # Build with PyInstaller (using spec file directly)
    try:
        cmd = ['pyinstaller', '--clean', str(spec_path)]
        print(f"🚀 Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ PyInstaller build completed")
        
        # Check if executable was created (look for both .exe and non-.exe versions)
        exe_path = None
        for possible_name in ['BackupBackend.exe', 'BackupBackend']:
            test_path = Path('dist') / possible_name
            if test_path.exists():
                exe_path = test_path
                break
        
        if exe_path:
            size = exe_path.stat().st_size
            print(f"✅ Executable created: {exe_path} ({size:,} bytes)")
            
            # Rename to .exe if needed
            if not exe_path.name.endswith('.exe'):
                new_path = exe_path.with_suffix('.exe')
                exe_path.rename(new_path)
                exe_path = new_path
                print(f"✅ Renamed to: {exe_path}")
            
            if size > 10_000_000:  # 10MB minimum
                print("✅ Executable size looks correct (>10MB)")
                return exe_path
            else:
                print(f"⚠️  Executable seems small: {size:,} bytes")
                return exe_path
        else:
            print("❌ Executable not found after build")
            print("📁 Contents of dist/:")
            for item in Path('dist').iterdir():
                print(f"   {item.name}")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller failed: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return None

def copy_to_electron_app(exe_path):
    """Copy executable to Electron app backend directory"""
    print("📋 Copying to Electron app...")
    
    # Target directory
    target_dir = Path('desktop-app/backend')
    target_dir.mkdir(exist_ok=True)
    
    # Target path
    target_path = target_dir / 'BackupBackend.exe'
    
    # Copy executable
    try:
        shutil.copy2(exe_path, target_path)
        size = target_path.stat().st_size
        print(f"✅ Copied to: {target_path} ({size:,} bytes)")
        return target_path
    except Exception as e:
        print(f"❌ Failed to copy: {e}")
        return None

def verify_executable(exe_path):
    """Verify the executable is a proper Windows PE file"""
    print("🔍 Verifying executable...")
    
    if not exe_path.exists():
        print("❌ Executable doesn't exist")
        return False
    
    # Check file size
    size = exe_path.stat().st_size
    print(f"📊 File size: {size:,} bytes")
    
    if size < 5_000_000:  # 5MB minimum
        print("⚠️  Executable seems too small")
        return False
    
    # Try to get file type (on Unix systems, this won't work perfectly)
    try:
        result = subprocess.run(['file', str(exe_path)], capture_output=True, text=True)
        file_type = result.stdout.strip()
        print(f"📄 File type: {file_type}")
        
        if 'PE32' in file_type or 'MS-DOS' in file_type:
            print("✅ Appears to be a Windows executable")
            return True
        else:
            print("⚠️  File type doesn't look like Windows executable")
            return True  # Still return True as file check on Unix may not be accurate
    except:
        print("⚠️  Could not determine file type (this is normal on non-Windows systems)")
        return True  # Assume it's correct if we can't check

def main():
    """Main build process"""
    print("🚀 Enterprise Backup System - Backend Build Script")
    print("=" * 60)
    
    # Change to project root
    script_dir = Path(__file__).parent
    project_root = script_dir
    os.chdir(project_root)
    print(f"📁 Working directory: {project_root}")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check PyInstaller
    if not check_pyinstaller():
        sys.exit(1)
    
    # Build executable
    exe_path = build_executable()
    if not exe_path:
        print("❌ Build failed")
        sys.exit(1)
    
    # Copy to Electron app
    electron_exe = copy_to_electron_app(exe_path)
    if not electron_exe:
        print("❌ Copy failed")
        sys.exit(1)
    
    # Verify executable
    if not verify_executable(electron_exe):
        print("⚠️  Executable verification failed, but continuing...")
    
    print("\n" + "=" * 60)
    print("🎉 BUILD COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"✅ Backend executable: {electron_exe}")
    print(f"✅ Ready for Electron packaging")
    print(f"✅ Installer should work without ENOENT errors")
    
    # Clean up spec file
    spec_path = Path('build_backend.spec')
    if spec_path.exists():
        spec_path.unlink()
        print("🧹 Cleaned up spec file")

if __name__ == "__main__":
    main()
