@echo off
REM Enterprise Backup System - PyInstaller Build Script for Windows
REM This script builds the standalone executable using PyInstaller

echo ========================================
echo Enterprise Backup System - EXE Builder
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "..\..\app\venv" (
    echo Creating virtual environment...
    python -m venv "..\..\app\venv"
)

REM Activate virtual environment
call "..\..\app\venv\Scripts\activate.bat"

REM Install requirements
echo Installing requirements...
pip install -r "..\..\app\requirements.txt"
pip install pyinstaller

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Create package directory structure
echo Creating package directory...
if not exist "package" mkdir "package"
if not exist "package\templates" xcopy /e /i "..\..\app\templates" "package\templates"
if not exist "package\storage" mkdir "package\storage"
if not exist "package\storage\backups" mkdir "package\storage\backups"
if not exist "package\logs" mkdir "package\logs"
if not exist "package\restored" mkdir "package\restored"
if not exist "package\sandbox_restore" mkdir "package\sandbox_restore"
if not exist "package\config" mkdir "package\config"

REM Copy configuration files
echo Copying configuration files...
copy "..\..\app\config_phase3.json" "package\"
copy "..\..\app\config.json" "package\" 2>nul
copy "..\..\app\requirements.txt" "package\"

REM Build the executable
echo Building executable with PyInstaller...
pyinstaller --onefile --noconsole --name "BackupSystem" --add-data "package;package" run_app.py

REM Copy the executable to package directory
if exist "dist\BackupSystem.exe" (
    echo.
    echo ========================================
    echo BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Copying executable to package directory...
    copy "dist\BackupSystem.exe" "package\"
    
    echo.
    echo Package contents:
    dir "package" /b
    
    echo.
    echo Executable created: package\BackupSystem.exe
    echo Package directory: %cd%\package
    echo.
    echo You can now run the installer script to create Setup.exe
    echo.
) else (
    echo.
    echo ========================================
    echo BUILD FAILED!
    echo ========================================
    echo.
    echo Please check the error messages above.
)

pause
