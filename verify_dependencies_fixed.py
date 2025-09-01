#!/usr/bin/env python3
"""
Verification script to check that dependency warnings are fixed
"""

import subprocess
import sys
import re

def check_email_validator():
    """Check if email-validator warning is fixed"""
    print("Checking email-validator...")
    try:
        # Try to import email-validator
        import email_validator
        print(f"✅ email-validator imported successfully (version {email_validator.__version__})")
        return True
    except ImportError as e:
        print(f"❌ Failed to import email-validator: {e}")
        return False

def check_sentry_sdk():
    """Check if sentry-sdk warning is fixed"""
    print("Checking sentry-sdk...")
    try:
        # Try to import sentry-sdk
        import sentry_sdk
        print(f"✅ sentry-sdk imported successfully (version {sentry_sdk.VERSION})")
        
        # Try to import streamlit integration
        try:
            from sentry_sdk.integrations.streamlit import StreamlitIntegration
            print("✅ sentry-sdk streamlit integration available")
        except ImportError:
            print("⚠️ sentry-sdk streamlit integration not available (this is OK for newer versions)")
            
        return True
    except ImportError as e:
        print(f"❌ Failed to import sentry-sdk: {e}")
        return False

def check_requirements_files():
    """Check if requirements files have been updated correctly"""
    print("Checking requirements files...")
    
    requirements_files = [
        "requirements.txt",
        "requirements-api.txt",
        "requirements-render.txt"
    ]
    
    all_good = True
    
    for req_file in requirements_files:
        try:
            with open(req_file, 'r') as f:
                content = f.read()
                
            # Check for email-validator version
            email_validator_match = re.search(r'email-validator==(\d+\.\d+\.\d+)', content)
            if email_validator_match:
                version = email_validator_match.group(1)
                if version >= "2.3.0":
                    print(f"✅ {req_file}: email-validator version {version} (fixed)")
                else:
                    print(f"⚠️ {req_file}: email-validator version {version} (still has warning)")
                    all_good = False
            else:
                print(f"⚠️ {req_file}: email-validator not found or not pinned")
                all_good = False
                
            # Check for sentry-sdk version
            sentry_sdk_match = re.search(r'sentry-sdk==(\d+\.\d+\.\d+)', content)
            if sentry_sdk_match:
                version = sentry_sdk_match.group(1)
                if version >= "2.0.0":
                    print(f"✅ {req_file}: sentry-sdk version {version} (fixed)")
                else:
                    print(f"⚠️ {req_file}: sentry-sdk version {version} (may still have warning)")
                    all_good = False
            else:
                # Check if it has the streamlit extra which causes the warning
                if 'sentry-sdk[streamlit]' in content:
                    print(f"❌ {req_file}: sentry-sdk still has [streamlit] extra (causes warning)")
                    all_good = False
                else:
                    print(f"✅ {req_file}: sentry-sdk properly formatted")
                    
        except FileNotFoundError:
            print(f"⚠️ {req_file}: File not found")
            all_good = False
            
    return all_good

def main():
    """Main verification function"""
    print("Starting dependency verification...")
    print("=" * 50)
    
    # Check imports
    email_validator_ok = check_email_validator()
    sentry_sdk_ok = check_sentry_sdk()
    
    print()
    
    # Check requirements files
    requirements_ok = check_requirements_files()
    
    print("=" * 50)
    
    if email_validator_ok and sentry_sdk_ok and requirements_ok:
        print("✅ All dependency warnings should be fixed!")
        print("You can now deploy without the previous warnings.")
        return True
    else:
        print("⚠️ Some issues remain. Please check the warnings above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)