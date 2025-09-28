"""
Script to verify API key configuration for assistant-based extraction
"""

import os
from config import get_openai_api_key

def verify_api_key():
    """Verify that the OpenAI API key is properly configured"""
    print("Verifying OpenAI API key configuration...")
    
    # Method 1: Check environment variable
    env_key = os.getenv("OPENAI_API_KEY")
    print(f"Environment variable OPENAI_API_KEY: {'SET' if env_key else 'NOT SET'}")
    if env_key:
        print(f"  Key preview: {env_key[:8]}...{env_key[-4:] if len(env_key) > 12 else ''}")
    
    # Method 2: Check through config system
    try:
        config_key = get_openai_api_key()
        print(f"Config system API key: {'SET' if config_key else 'NOT SET'}")
        if config_key:
            print(f"  Key preview: {config_key[:8]}...{config_key[-4:] if len(config_key) > 12 else ''}")
    except Exception as e:
        print(f"Error getting key from config: {e}")
    
    # Summary
    api_key = get_openai_api_key()
    if api_key and len(api_key) > 20:  # Basic validation
        print("\n✅ API key is properly configured!")
        print("You're ready to use assistant-based extraction.")
        return True
    else:
        print("\n❌ API key is not properly configured!")
        print("Please set your OpenAI API key in one of these ways:")
        print("1. Environment variable: OPENAI_API_KEY=sk-...")
        print("2. In your .env file")
        print("3. In your config.py file")
        return False

if __name__ == "__main__":
    verify_api_key()