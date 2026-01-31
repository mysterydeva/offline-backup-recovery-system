#!/usr/bin/env python3
"""
Enterprise Backup System - Application Launcher
Starts the FastAPI server and automatically opens the browser dashboard.
"""

import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

# Add the app directory to Python path
APP_DIR = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(APP_DIR))

def start_server():
    """Start the FastAPI server"""
    try:
        import uvicorn
        from main_fixed import app
        
        print("Starting Enterprise Backup System...")
        print("Server will be available at: http://127.0.0.1:8001")
        print("Dashboard will open automatically in your browser...")
        
        # Start server in the app directory
        os.chdir(APP_DIR)
        
        # Run uvicorn
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8001,
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        print(f"Error: Missing dependencies - {e}")
        print("Please ensure all requirements are installed:")
        print("pip install -r requirements.txt")
        input("Press Enter to exit...")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

def open_browser():
    """Open browser after 2 seconds"""
    time.sleep(2)
    try:
        webbrowser.open("http://127.0.0.1:8001")
    except Exception as e:
        print(f"Could not open browser automatically: {e}")
        print("Please manually open: http://127.0.0.1:8001")

if __name__ == "__main__":
    try:
        # Start browser opener in background
        import threading
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start server (this blocks)
        start_server()
        
    except KeyboardInterrupt:
        print("\nShutting down Enterprise Backup System...")
    except Exception as e:
        print(f"Fatal error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
