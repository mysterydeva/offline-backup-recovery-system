#!/usr/bin/env python3
"""
Comprehensive diagnosis script for Electron + FastAPI desktop application
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

def diagnose_step1_build_output():
    """STEP 1: Inspect Build Output"""
    print("🔍 STEP 1: Inspect Build Output")
    print("=" * 40)
    
    findings = {}
    
    # Check for backend executable
    backend_paths = [
        "desktop-app/backend/BackupBackend.exe",
        "app/dist/BackupBackend.exe",
        "dist/desktop-app/backend/BackupBackend.exe"
    ]
    
    for path in backend_paths:
        if os.path.exists(path):
            size = os.path.getsize(path)
            findings['backend_location'] = path
            findings['backend_size'] = size
            print(f"✅ Backend found: {path} ({size} bytes)")
            
            # Check if it's a real executable or dummy
            if size < 1000:
                print("⚠️  Backend appears to be a dummy file (< 1KB)")
            else:
                print("✅ Backend appears to be a real executable")
        else:
            print(f"❌ Backend not found: {path}")
    
    # Check for dist folder
    dist_paths = [
        "desktop-app/dist",
        "dist"
    ]
    
    for path in dist_paths:
        if os.path.exists(path):
            print(f"✅ Dist folder found: {path}")
            try:
                contents = list(Path(path).rglob("*"))
                print(f"   📁 Contains {len(contents)} files/directories")
            except:
                pass
        else:
            print(f"❌ Dist folder not found: {path}")
    
    return findings

def diagnose_step2_packaging():
    """STEP 2: Verify Installer Packaging"""
    print("\n🔍 STEP 2: Verify Installer Packaging")
    print("=" * 40)
    
    findings = {}
    
    # Check package.json
    package_json = "desktop-app/package.json"
    if os.path.exists(package_json):
        with open(package_json, 'r') as f:
            config = json.load(f)
        
        build_config = config.get('build', {})
        
        # Check files array
        files = build_config.get('files', [])
        print(f"📋 Files array: {files}")
        if 'backend/**' in files:
            print("✅ backend/** included in files")
            findings['files_includes_backend'] = True
        else:
            print("❌ backend/** missing from files")
        
        # Check asarUnpack
        asar_unpack = build_config.get('asarUnpack', [])
        print(f"📋 asarUnpack: {asar_unpack}")
        if 'backend/**' in asar_unpack:
            print("✅ backend/** will be unpacked from asar")
            findings['asar_unpack_backend'] = True
        else:
            print("❌ backend/** missing from asarUnpack")
        
        # Check extraResources
        extra_files = build_config.get('extraFiles', [])
        print(f"📋 extraFiles: {extra_files}")
        
    else:
        print("❌ package.json not found")
    
    return findings

def diagnose_step3_startup_logic():
    """STEP 3: Test Backend Startup Logic"""
    print("\n🔍 STEP 3: Test Backend Startup Logic")
    print("=" * 40)
    
    findings = {}
    
    # Check main.js
    main_js = "desktop-app/main.js"
    if os.path.exists(main_js):
        with open(main_js, 'r') as f:
            content = f.read()
        
        # Check for process.resourcesPath
        if 'process.resourcesPath' in content:
            print("✅ Uses process.resourcesPath")
            findings['uses_resources_path'] = True
        else:
            print("❌ Missing process.resourcesPath")
        
        # Check backend path construction
        if 'path.join(process.resourcesPath, \'backend\', \'BackupBackend.exe\')' in content:
            print("✅ Correct backend path construction")
            findings['correct_backend_path'] = True
        else:
            print("❌ Incorrect backend path construction")
        
        # Check for old __dirname usage
        if 'path.join(__dirname, \'backend\', \'BackupBackend.exe\')' in content:
            print("❌ Still uses old __dirname path")
            findings['uses_old_dirname'] = True
        else:
            print("✅ No old __dirname usage")
        
        # Check for debug logging
        if 'console.log("Backend Path"' in content:
            print("✅ Has debug logging for backend path")
            findings['has_debug_logging'] = True
        else:
            print("⚠️  Missing debug logging")
    
    else:
        print("❌ main.js not found")
    
    return findings

def diagnose_step4_backend_executable():
    """STEP 4: Test Backend Executable"""
    print("\n🔍 STEP 4: Test Backend Executable")
    print("=" * 40)
    
    findings = {}
    
    backend_exe = "desktop-app/backend/BackupBackend.exe"
    if os.path.exists(backend_exe):
        # Check file type
        try:
            result = subprocess.run(['file', backend_exe], capture_output=True, text=True)
            print(f"📄 File type: {result.stdout.strip()}")
            findings['file_type'] = result.stdout.strip()
        except:
            print("⚠️  Could not determine file type")
        
        # Check file size
        size = os.path.getsize(backend_exe)
        print(f"📊 File size: {size} bytes")
        findings['file_size'] = size
        
        # Check if it's a Python script
        if size < 1000:
            try:
                with open(backend_exe, 'r') as f:
                    content = f.read()
                if 'python' in content.lower():
                    print("❌ Backend is a Python script, not compiled executable")
                    findings['is_python_script'] = True
            except:
                pass
        else:
            print("✅ Backend appears to be compiled executable")
    
    else:
        print("❌ Backend executable not found")
    
    return findings

def diagnose_step5_dependencies():
    """STEP 5: Check Dependencies"""
    print("\n🔍 STEP 5: Check Dependencies")
    print("=" * 40)
    
    findings = {}
    
    # Check requirements.txt
    requirements_txt = "app/requirements.txt"
    if os.path.exists(requirements_txt):
        with open(requirements_txt, 'r') as f:
            requirements = f.read().strip().split('\n')
        print(f"📋 Requirements: {requirements}")
        findings['requirements'] = requirements
    else:
        print("❌ requirements.txt not found")
    
    # Check if PyInstaller spec exists
    spec_files = list(Path("app").glob("*.spec"))
    if spec_files:
        print(f"✅ Found PyInstaller spec: {spec_files}")
        findings['has_spec_file'] = True
    else:
        print("⚠️  No PyInstaller spec found")
    
    return findings

def diagnose_step6_github_actions():
    """STEP 6: Check GitHub Actions"""
    print("\n🔍 STEP 6: Check GitHub Actions")
    print("=" * 40)
    
    findings = {}
    
    workflow = ".github/workflows/windows-build.yml"
    if os.path.exists(workflow):
        with open(workflow, 'r') as f:
            content = f.read()
        
        # Check for PyInstaller step
        if 'pyinstaller' in content.lower():
            print("✅ Has PyInstaller build step")
            findings['has_pyinstaller_step'] = True
        else:
            print("❌ Missing PyInstaller build step")
        
        # Check for backend copy step
        if 'desktop-app\\backend\\BackupBackend.exe' in content:
            print("✅ Has backend copy step")
            findings['has_backend_copy'] = True
        else:
            print("❌ Missing backend copy step")
        
        # Check for electron-builder step
        if 'npm run build-win' in content:
            print("✅ Has electron-builder step")
            findings['has_electron_build'] = True
        else:
            print("❌ Missing electron-builder step")
    
    else:
        print("❌ GitHub Actions workflow not found")
    
    return findings

def generate_diagnosis_report():
    """Generate comprehensive diagnosis report"""
    print("\n" + "=" * 60)
    print("🏥 COMPREHENSIVE DIAGNOSIS REPORT")
    print("=" * 60)
    
    all_findings = {}
    
    # Run all diagnostic steps
    all_findings.update(diagnose_step1_build_output())
    all_findings.update(diagnose_step2_packaging())
    all_findings.update(diagnose_step3_startup_logic())
    all_findings.update(diagnose_step4_backend_executable())
    all_findings.update(diagnose_step5_dependencies())
    all_findings.update(diagnose_step6_github_actions())
    
    # Generate root cause analysis
    print("\n🎯 ROOT CAUSE ANALYSIS")
    print("=" * 30)
    
    issues = []
    
    # Check for critical issues
    if not all_findings.get('backend_location'):
        issues.append("❌ CRITICAL: No backend executable found")
    
    if all_findings.get('file_size', 0) < 1000:
        issues.append("❌ CRITICAL: Backend is not a compiled executable")
    
    if not all_findings.get('asar_unpack_backend'):
        issues.append("❌ CRITICAL: Backend not unpacked from asar")
    
    if not all_findings.get('uses_resources_path'):
        issues.append("❌ CRITICAL: Main.js doesn't use process.resourcesPath")
    
    if not all_findings.get('has_pyinstaller_step'):
        issues.append("❌ CRITICAL: GitHub Actions missing PyInstaller step")
    
    if not all_findings.get('has_backend_copy'):
        issues.append("❌ CRITICAL: GitHub Actions missing backend copy step")
    
    if issues:
        print("CRITICAL ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ No critical issues detected")
    
    # Generate recommendations
    print("\n🔧 RECOMMENDED FIXES")
    print("=" * 25)
    
    recommendations = []
    
    if not all_findings.get('backend_location') or all_findings.get('file_size', 0) < 1000:
        recommendations.append("1. Build real backend executable with PyInstaller")
    
    if not all_findings.get('asar_unpack_backend'):
        recommendations.append("2. Add 'asarUnpack': ['backend/**'] to package.json")
    
    if not all_findings.get('uses_resources_path'):
        recommendations.append("3. Update main.js to use process.resourcesPath")
    
    if not all_findings.get('has_pyinstaller_step'):
        recommendations.append("4. Add PyInstaller build step to GitHub Actions")
    
    if not all_findings.get('has_backend_copy'):
        recommendations.append("5. Add backend copy step to GitHub Actions")
    
    for rec in recommendations:
        print(f"  {rec}")
    
    return all_findings, issues

if __name__ == "__main__":
    findings, issues = generate_diagnosis_report()
    
    print(f"\n📊 SUMMARY: {len(issues)} critical issues found")
    
    if len(issues) > 0:
        print("❌ APPLICATION WILL FAIL ON INSTALLATION")
        sys.exit(1)
    else:
        print("✅ APPLICATION SHOULD WORK CORRECTLY")
        sys.exit(0)
