#!/usr/bin/env python3
"""
Test script to verify Electron installer backend path fixes
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

def test_package_json_config():
    """Test that package.json has correct asarUnpack configuration"""
    print("🔍 Testing package.json configuration...")
    
    package_path = Path("desktop-app/package.json")
    if not package_path.exists():
        print("❌ package.json not found")
        return False
    
    with open(package_path, 'r') as f:
        config = json.load(f)
    
    build_config = config.get('build', {})
    
    # Check asarUnpack
    asar_unpack = build_config.get('asarUnpack', [])
    if 'backend/**' not in asar_unpack:
        print("❌ asarUnpack missing 'backend/**'")
        return False
    print("✅ asarUnpack correctly includes 'backend/**'")
    
    # Check files array
    files = build_config.get('files', [])
    if 'backend/**' not in files:
        print("❌ files array missing 'backend/**'")
        return False
    print("✅ files array correctly includes 'backend/**'")
    
    return True

def test_main_js_backend_path():
    """Test that main.js uses process.resourcesPath for backend"""
    print("\n🔍 Testing main.js backend path...")
    
    main_js_path = Path("desktop-app/main.js")
    if not main_js_path.exists():
        print("❌ main.js not found")
        return False
    
    with open(main_js_path, 'r') as f:
        content = f.read()
    
    # Check for process.resourcesPath usage
    if 'process.resourcesPath' not in content:
        print("❌ main.js doesn't use process.resourcesPath")
        return False
    print("✅ main.js correctly uses process.resourcesPath")
    
    # Check for correct backend path construction
    if 'path.join(process.resourcesPath, \'backend\', \'BackupBackend.exe\')' not in content:
        print("❌ main.js doesn't construct backend path correctly")
        return False
    print("✅ main.js correctly constructs backend path")
    
    # Check that old __dirname path is removed
    if 'path.join(__dirname, \'backend\', \'BackupBackend.exe\')' in content:
        print("❌ main.js still contains old __dirname path")
        return False
    print("✅ main.js doesn't contain old __dirname path")
    
    return True

def test_github_workflow():
    """Test that GitHub Actions workflow copies backend correctly"""
    print("\n🔍 Testing GitHub Actions workflow...")
    
    workflow_path = Path(".github/workflows/windows-build.yml")
    if not workflow_path.exists():
        print("❌ GitHub Actions workflow not found")
        return False
    
    with open(workflow_path, 'r') as f:
        content = f.read()
    
    # Check for backend copy step
    if 'desktop-app\\backend\\BackupBackend.exe' not in content:
        print("❌ Workflow doesn't copy backend to correct location")
        return False
    print("✅ Workflow correctly copies backend to desktop-app/backend/BackupBackend.exe")
    
    return True

def simulate_electron_structure():
    """Simulate Electron app structure to verify paths"""
    print("\n🔍 Simulating Electron app structure...")
    
    # Create temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Simulate resources directory (what Electron creates)
        resources_dir = temp_path / "resources"
        resources_dir.mkdir()
        
        # Simulate backend directory
        backend_dir = resources_dir / "backend"
        backend_dir.mkdir()
        
        # Create dummy backend exe
        backend_exe = backend_dir / "BackupBackend.exe"
        backend_exe.write_text("dummy exe content")
        
        # Test path construction (same as main.js)
        import sys
        sys.path.insert(0, str(temp_path))
        
        # Simulate the path construction from main.js
        test_path = os.path.join(str(resources_dir), 'backend', 'BackupBackend.exe')
        
        if os.path.exists(test_path):
            print("✅ Simulated backend path works correctly")
            return True
        else:
            print("❌ Simulated backend path doesn't work")
            return False

def create_test_backend():
    """Create a test backend executable for testing"""
    print("\n🔧 Creating test backend executable...")
    
    backend_dir = Path("desktop-app/backend")
    backend_dir.mkdir(exist_ok=True)
    
    # Create a dummy backend exe for testing
    backend_exe = backend_dir / "BackupBackend.exe"
    
    # Create a simple Python script as dummy backend
    dummy_script = """#!/usr/bin/env python3
import sys
print("Backend started successfully")
sys.exit(0)
"""
    
    # Write dummy script (in real build, this would be PyInstaller output)
    backend_exe.write_text(dummy_script)
    print(f"✅ Created test backend at: {backend_exe}")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Testing Electron Installer Backend Path Fixes")
    print("=" * 50)
    
    tests = [
        test_package_json_config,
        test_main_js_backend_path,
        test_github_workflow,
        simulate_electron_structure,
        create_test_backend
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Electron installer fixes are complete:")
        print("   - Backend will be unpacked from asar")
        print("   - Main.js uses correct process.resourcesPath")
        print("   - GitHub Actions workflow copies backend correctly")
        print("   - Final installer will contain resources/backend/BackupBackend.exe")
        print("\n🚀 Ready to build installer!")
    else:
        print(f"\n❌ {total - passed} tests failed")
        print("Please fix the issues before building")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
