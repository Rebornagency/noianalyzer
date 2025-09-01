#!/usr/bin/env python3
"""
Test script to verify requirements installation
"""

import subprocess
import sys

def test_pip_install():
    """Test pip install command for requirements-api.txt"""
    try:
        # Run pip install command
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements-api.txt"
        ], capture_output=True, text=True, timeout=60)
        
        print("pip install command output:")
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ pip install completed successfully")
            return True
        else:
            print("❌ pip install failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ pip install timed out")
        return False
    except Exception as e:
        print(f"❌ Error running pip install: {e}")
        return False

def test_package_imports():
    """Test if packages can be imported after installation"""
    packages = [
        'fastapi',
        'uvicorn',
        'stripe',
        'python_dotenv',
        'email_validator',
        'python_multipart',
        'pandas',
        'sentry_sdk'
    ]
    
    print("\nTesting package imports:")
    print("=" * 30)
    
    success_count = 0
    for package in packages:
        try:
            __import__(package)
            print(f"✅ {package} - OK")
            success_count += 1
        except ImportError as e:
            print(f"❌ {package} - FAILED: {e}")
        except Exception as e:
            print(f"❌ {package} - ERROR: {e}")
    
    print(f"\nImport test results: {success_count}/{len(packages)} packages imported successfully")
    return success_count == len(packages)

if __name__ == "__main__":
    print("Testing requirements installation...")
    print("=" * 40)
    
    # Test pip install
    install_success = test_pip_install()
    
    # Test package imports
    if install_success:
        import_success = test_package_imports()
        if import_success:
            print("\n🎉 All tests passed!")
        else:
            print("\n⚠️  Installation succeeded but some packages could not be imported")
    else:
        print("\n❌ Installation failed")