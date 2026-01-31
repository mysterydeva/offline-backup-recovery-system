# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Enterprise Backup System Backend
Creates a standalone executable for the FastAPI backend service
"""

import os
import sys
from pathlib import Path

# Get the current directory
SPEC_DIR = Path(SPECPATH).resolve()
APP_DIR = SPEC_DIR.parent / "app"

# Configuration
APP_NAME = "BackupBackend"
MAIN_SCRIPT = str(APP_DIR / "main_fixed.py")
ICON_PATH = str(SPEC_DIR / "assets" / "icon.ico") if (SPEC_DIR / "assets" / "icon.ico").exists() else None

# Analysis configuration
a = Analysis(
    [MAIN_SCRIPT],
    pathex=[str(APP_DIR), str(SPEC_DIR)],
    binaries=[],
    datas=[
        # Include templates directory
        (str(APP_DIR / "templates"), "templates"),
        
        # Include configuration files
        (str(APP_DIR / "config_phase3.json"), "."),
        (str(APP_DIR / "config.json"), ".") if (APP_DIR / "config.json").exists() else None,
        
        # Include security directory if exists
        (str(APP_DIR / "security"), "security") if (APP_DIR / "security").exists() else None,
        
        # Include plugins directory if exists
        (str(APP_DIR / "plugins"), "plugins") if (APP_DIR / "plugins").exists() else None,
    ],
    hiddenimports=[
        # FastAPI and related
        "uvicorn",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.websockets",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "fastapi",
        "fastapi.staticfiles",
        "fastapi.templating",
        "fastapi.responses",
        "fastapi.middleware",
        "fastapi.middleware.cors",
        "fastapi.middleware.gzip",
        
        # Jinja2 templates
        "jinja2",
        "jinja2.ext",
        "jinja2.ext.autoescape",
        "jinja2.ext.with_",
        "jinja2.ext.do",
        "jinja2.ext.loopcontrols",
        "jinja2.ext.i18n",
        
        # Database and ORM
        "sqlite3",
        "sqlite3.dump",
        
        # Cryptography
        "cryptography",
        "cryptography.fernet",
        "cryptography.hazmat",
        "cryptography.hazmat.primitives",
        "cryptography.hazmat.backends",
        "cryptography.hazmat.backends.openssl",
        "bcrypt",
        
        # Scheduling
        "apscheduler",
        "apscheduler.schedulers",
        "apscheduler.schedulers.background",
        "apscheduler.triggers",
        "apscheduler.triggers.cron",
        "apscheduler.triggers.interval",
        "apscheduler.jobstores",
        "apscheduler.jobstores.sqlalchemy",
        
        # Reports and PDF
        "reportlab",
        "reportlab.pdfgen",
        "reportlab.lib",
        "reportlab.platypus",
        
        # System monitoring
        "psutil",
        "psutil._psutil_windows" if sys.platform == "win32" else "psutil._psutil_linux",
        
        # HTTP and networking
        "urllib3",
        "certifi",
        "charset_normalizer",
        
        # JSON and data handling
        "pydantic",
        "pydantic.main",
        "pydantic.fields",
        "pydantic.validators",
        
        # Multipart form data
        "python-multipart",
        "multipart",
        
        # Additional modules that might be imported dynamically
        "email.utils",
        "datetime",
        "threading",
        "asyncio",
        "concurrent.futures",
        "queue",
        "logging.handlers",
        "socket",
        "ssl",
        "hashlib",
        "hmac",
        "base64",
        "uuid",
        "json",
        "os",
        "sys",
        "pathlib",
        "shutil",
        "tempfile",
        "zipfile",
        "tarfile",
        "gzip",
        "bz2",
        "lzma",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude development and testing modules
        "pytest",
        "unittest",
        "doctest",
        "pdb",
        "IPython",
        "jupyter",
        "notebook",
        
        # Exclude GUI frameworks (not needed for backend)
        "tkinter",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "wx",
        
        # Exclude scientific computing (not needed)
        "numpy",
        "scipy",
        "matplotlib",
        "pandas",
        
        # Exclude web frameworks not used
        "django",
        "flask",
        "tornado",
        "cherrypy",
        
        # Exclude database drivers not used
        "psycopg2",
        "pymysql",
        "cx_Oracle",
        " pymongo",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove None entries from datas
a.datas = [item for item in a.datas if item is not None]

# PYZ configuration
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# EXE configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Run silently without console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH,
    version="version_info.txt" if (SPEC_DIR / "version_info.txt").exists() else None,
)

# Create version info file for Windows
if sys.platform == "win32":
    version_info = """# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Enterprise Software Solutions'),
        StringStruct(u'FileDescription', u'Enterprise Backup System Backend'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'BackupBackend'),
        StringStruct(u'LegalCopyright', u'Copyright © 2024 Enterprise Software Solutions'),
        StringStruct(u'OriginalFilename', u'BackupBackend.exe'),
        StringStruct(u'ProductName', u'Enterprise Backup System'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    
    with open(SPEC_DIR / "version_info.txt", "w", encoding="utf-8") as f:
        f.write(version_info)

print(f"PyInstaller spec file configured for {APP_NAME}")
print(f"Main script: {MAIN_SCRIPT}")
print(f"Output directory: {SPEC_DIR / 'dist'}")
