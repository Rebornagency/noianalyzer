#!/usr/bin/env python3
"""
Test script to check if all required packages can be imported
"""

required_packages = [
    'fastapi',
    'uvicorn',
    'stripe',
    'python_dotenv',
    'email_validator',
    'python_multipart',
    'pandas',
    'sentry_sdk'
]

print("Checking required packages...")
print("=" * 40)

for package in required_packages:
    try:
        __import__(package)
        print(f"✅ {package} - OK")
    except ImportError as e:
        print(f"❌ {package} - FAILED: {e}")
    except Exception as e:
        print(f"❌ {package} - ERROR: {e}")

print("=" * 40)
print("Test completed.")