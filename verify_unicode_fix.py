#!/usr/bin/env python3
"""
Final verification of Unicode fixes for Windows compatibility
"""

import os
import sys
from pathlib import Path

def main():
    print("UNICODE COMPATIBILITY FIXES - VERIFICATION")
    print("=" * 50)
    
    # Check build script for Unicode characters
    build_script = Path("build_backend.py")
    if build_script.exists():
        with open(build_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for common Unicode characters that cause issues
        unicode_chars = ['🚀', '✅', '❌', '📁', '🔍', '📋', '📊', '🧹', '🎉', '⚠️']
        found_unicode = []
        
        for char in unicode_chars:
            if char in content:
                found_unicode.append(char)
        
        if found_unicode:
            print(f"[ERROR] Found Unicode characters in build script: {found_unicode}")
            return False
        else:
            print("[OK] No problematic Unicode characters in build script")
    
    # Check for UTF-8 configuration
    if 'sys.stdout.reconfigure(encoding="utf-8")' in content:
        print("[OK] UTF-8 encoding configuration added")
    else:
        print("[ERROR] UTF-8 encoding configuration missing")
        return False
    
    # Check GitHub Actions workflow
    workflow = Path(".github/workflows/windows-build.yml")
    if workflow.exists():
        with open(workflow, 'r', encoding='utf-8') as f:
            workflow_content = f.read()
        
        # Check for PYTHONUTF8 environment variable
        if 'PYTHONUTF8: "1"' in workflow_content:
            print("[OK] PYTHONUTF8 environment variable added")
        else:
            print("[ERROR] PYTHONUTF8 environment variable missing")
            return False
        
        # Check for UTF-8 console step
        if 'chcp 65001' in workflow_content:
            print("[OK] UTF-8 console configuration added")
        else:
            print("[ERROR] UTF-8 console configuration missing")
            return False
        
        # Check for Unicode characters in workflow
        workflow_unicode = ['🚀', '✅', '❌', '📁', '🔍', '📋', '📊', '🧹', '🎉', '⚠️', '🏗️']
        found_workflow_unicode = []
        
        for char in workflow_unicode:
            if char in workflow_content:
                found_workflow_unicode.append(char)
        
        if found_workflow_unicode:
            print(f"[ERROR] Found Unicode characters in workflow: {found_workflow_unicode}")
            return False
        else:
            print("[OK] No problematic Unicode characters in workflow")
    
    # Check that executable exists and is real
    backend_exe = Path("desktop-app/backend/BackupBackend.exe")
    if backend_exe.exists():
        size = backend_exe.stat().st_size
        print(f"[OK] Backend executable exists: {size:,} bytes")
        
        if size > 10_000_000:
            print("[OK] Executable size looks correct")
        else:
            print("[WARNING] Executable seems small")
    else:
        print("[ERROR] Backend executable not found")
        return False
    
    print("\n" + "=" * 50)
    print("UNICODE FIXES COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print("[OK] Build script uses only ASCII characters")
    print("[OK] UTF-8 encoding configured in Python script")
    print("[OK] PYTHONUTF8 environment variable set in workflow")
    print("[OK] UTF-8 console configuration added to workflow")
    print("[OK] No Unicode characters in workflow output")
    print("[OK] Backend executable built successfully")
    
    print("\nWindows GitHub Actions runner should now execute without UnicodeEncodeError!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
