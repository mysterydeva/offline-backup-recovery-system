# Enterprise Backup System - Windows Installer Guide

## Overview

The Enterprise Backup System is a professional offline backup and recovery solution that can be deployed as a standalone Windows application. This guide covers building, packaging, and deploying the system for client delivery.

## System Requirements

### Target Client Environment
- **Operating System**: Windows 7 SP1 or later (Windows 10/11 recommended)
- **Architecture**: x64 or x86
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 500MB free space for application + backup storage space
- **Network**: None required (fully offline operation)

### Developer Build Environment
- **Python 3.8+** with pip
- **PyInstaller** for EXE creation
- **Inno Setup 6.0+** for installer creation
- Administrative privileges for installer creation

## Quick Start for Clients

### Installation
1. Download `BackupSystem_Setup.exe` from your provider
2. Right-click and select "Run as administrator"
3. Follow the installation wizard
4. Launch from Start Menu or Desktop shortcut

### First Time Use
1. Double-click the **Enterprise Backup System** icon
2. Wait 2-3 seconds for the server to start
3. Browser automatically opens to `http://127.0.0.1:8001`
4. **Default Login**: 
   - Username: `admin`
   - Password: `admin123`

### Basic Operation
- **Dashboard**: View system status and recent backups
- **Backup**: Create new backup jobs manually
- **Restore**: Recover files from existing backups
- **Settings**: Configure backup schedules and destinations

## Developer Build Instructions

### Step 1: Prepare the Environment

```batch
REM Navigate to installer directory
cd backup_system\release\windows-installer

REM Ensure Python is installed
python --version
pip --version
```

### Step 2: Build the Executable

#### Option A: Using the Automated Script (Recommended)
```batch
REM Run the build script
build_exe.bat
```

#### Option B: Manual Build Process
```batch
REM Create and activate virtual environment
python -m venv ..\..\app\venv
..\..\app\venv\Scripts\activate.bat

REM Install dependencies
pip install -r ..\..\app\requirements.txt
pip install pyinstaller

REM Create package structure
mkdir package
xcopy /e /i ..\..\app\templates package\templates
mkdir package\storage\backups
mkdir package\logs
mkdir package\restored
mkdir package\sandbox_restore
mkdir package\config

REM Copy configuration files
copy ..\..\app\config_phase3.json package\
copy ..\..\app\requirements.txt package\

REM Build executable
pyinstaller --onefile --noconsole --name "BackupSystem" --add-data "package;package" run_app.py

REM Copy to package directory
copy dist\BackupSystem.exe package\
```

### Step 3: Create the Installer

#### Prerequisites
- Download and install [Inno Setup](https://jrsoftware.org/isinfo.php)
- Ensure Inno Setup is in your PATH

#### Build Installer
```batch
REM Compile the installer script
iscc installer.iss
```

The installer `BackupSystem_Setup.exe` will be created in the current directory.

## File Structure After Build

```
release/windows-installer/
├── BackupSystem_Setup.exe          # Final installer for clients
├── build_exe.bat                   # Windows build script
├── build_exe.sh                    # Linux build script (helper)
├── installer.iss                   # Inno Setup script
├── run_app.py                      # Application launcher
├── README_INSTALLER.md             # This file
└── package/                        # Temporary build folder
    ├── BackupSystem.exe            # Standalone executable
    ├── templates/                  # Web interface files
    ├── config_phase3.json          # Configuration
    ├── storage/                    # Backup storage
    ├── logs/                       # Application logs
    ├── restored/                   # Restore destination
    └── sandbox_restore/            # Sandbox for testing
```

## Deployment Options

### Option 1: Single EXE Installer (Recommended)
- **File**: `BackupSystem_Setup.exe`
- **Size**: ~50-100MB
- **Installation**: Standard Windows installer
- **Features**: 
  - Start Menu shortcuts
  - Desktop shortcut (optional)
  - Auto-launch after install
  - Proper Windows registration

### Option 2: Portable Version
- **Files**: Contents of `package/` directory
- **Usage**: Extract and run `BackupSystem.exe`
- **Features**: 
  - No installation required
  - Can run from USB drive
  - Manual shortcut creation

## Configuration

### Default Configuration
The system includes `config_phase3.json` with these defaults:
- **Server Port**: 8001
- **Bind Address**: 127.0.0.1 (localhost only)
- **Backup Storage**: `./storage/backups/`
- **Log Level**: INFO
- **Database**: `./backup_system.db`

### Post-Installation Configuration
1. Access the dashboard at `http://127.0.0.1:8001`
2. Login with default credentials
3. Navigate to **Settings** → **System Configuration**
4. Modify paths, schedules, and retention policies as needed

## Security Considerations

### Default Credentials
- **Important**: Change default admin password after first login
- Navigate to **Settings** → **User Management** → **Change Password**

### Network Access
- By default, the server only listens on localhost (127.0.0.1)
- This prevents external network access
- For network access, modify `config_phase3.json`:
  ```json
  {
    "server": {
      "host": "0.0.0.0",
      "port": 8001
    }
  }
  ```

### Data Encryption
- All backup data is encrypted using AES-256
- Encryption keys are stored in `config/secret.key`
- Keep this file secure and backed up separately

## Troubleshooting

### Common Issues

#### Application Won't Start
1. Check Windows Event Viewer for errors
2. Ensure antivirus is not blocking the executable
3. Run as administrator if permission errors occur
4. Check if port 8001 is already in use

#### Browser Won't Open
1. Manually open `http://127.0.0.1:8001`
2. Check if default browser is set
3. Try different browsers (Chrome, Firefox, Edge)

#### Backup Failures
1. Check disk space in backup destination
2. Verify file permissions
3. Review logs in `logs/backup.log`
4. Ensure source files are not locked by other applications

#### Performance Issues
1. Close unnecessary applications
2. Ensure adequate disk space
3. Consider excluding backup directory from antivirus scanning
4. Upgrade to SSD storage for better performance

### Log Files
- **Application Log**: `logs/backup.log`
- **System Log**: Windows Event Viewer → Application Logs
- **Error Details**: Check browser developer console (F12)

## Advanced Usage

### Silent Installation
```batch
BackupSystem_Setup.exe /VERYSILENT /DIR="C:\CustomPath"
```

### Uninstallation
- Use "Add or Remove Programs" in Windows Settings
- Or run `Uninstall Enterprise Backup System` from Start Menu

### Command Line Options
The executable supports these command line options:
```batch
BackupSystem.exe --help                    # Show help
BackupSystem.exe --port 8080              # Custom port
BackupSystem.exe --host 0.0.0.0           # Network access
BackupSystem.exe --no-browser             # Don't open browser
```

## Support and Maintenance

### Regular Maintenance Tasks
1. **Review Logs**: Check `logs/backup.log` weekly
2. **Monitor Storage**: Ensure adequate disk space
3. **Update Configuration**: Adjust retention policies as needed
4. **Test Restores**: Verify backup integrity monthly

### Backup Best Practices
1. **3-2-1 Rule**: 3 copies, 2 media types, 1 offsite
2. **Regular Testing**: Test restore procedures quarterly
3. **Documentation**: Keep backup procedures documented
4. **Monitoring**: Set up alerts for backup failures

### Getting Help
- **Documentation**: Check the in-app help section
- **Logs**: Review application logs for error details
- **Support**: Contact your system administrator or support provider

## Version Information

- **Current Version**: 1.0.0
- **Build Date**: [Automatically generated during build]
- **Python Version**: 3.8+
- **Framework**: FastAPI + Uvicorn
- **Database**: SQLite

## Legal and Licensing

This software is provided as-is for enterprise backup purposes. Please refer to your license agreement for usage terms and restrictions.

---

**Last Updated**: January 2026  
**Document Version**: 1.0.0  
**For**: Enterprise Backup System v1.0.0
