#!/usr/bin/env python3
"""
Test script to check Python environment and package locations
"""

import sys
import os
import subprocess

def test_python_environment():
    """Test Python environment details"""
    print("Python Environment Test")
    print("=" * 30)
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.path}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if we're in a virtual environment
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    print(f"In virtual environment: {in_venv}")
    
    # Check site packages
    import site
    print(f"Site packages: {site.getsitepackages()}")
    if hasattr(site, 'getusersitepackages'):
        print(f"User site packages: {site.getusersitepackages()}")

def test_package_location():
    """Test where packages are installed"""
    print("\nPackage Location Test")
    print("=" * 30)
    
    packages = ['stripe', 'fastapi', 'uvicorn']
    for package in packages:
        try:
            module = __import__(package)
            if hasattr(module, '__file__'):
                print(f"{package}: {module.__file__}")
            else:
                print(f"{package}: Built-in or special module")
        except ImportError as e:
            print(f"{package}: Not found - {e}")

def test_pip_show():
    """Test pip show for stripe package"""
    print("\nPip Show Test")
    print("=" * 30)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "show", "stripe"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("Stripe package info:")
            print(result.stdout)
        else:
            print("Failed to get stripe package info:")
            print(result.stderr)
    except Exception as e:
        print(f"Error running pip show: {e}")

if __name__ == "__main__":
    test_python_environment()
    test_package_location()
    test_pip_show()