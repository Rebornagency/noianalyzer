"""
Test script to verify assistant integration with existing API key setup
"""

import os
from config import get_openai_api_key
from assistant_based_extraction import AssistantBasedExtractor

def test_assistant_integration():
    """Test that the assistant integrates properly with existing API key setup"""
    print("Testing assistant integration with existing API key setup...")
    
    # Step 1: Verify API key is available
    print("\n1. Checking API key configuration...")
    api_key = get_openai_api_key()
    
    if not api_key:
        print("❌ No API key found!")
        print("Please set your OpenAI API key in one of these ways:")
        print("   - Environment variable: OPENAI_API_KEY=sk-...")
        print("   - In your .env file")
        return False
    
    if len(api_key) < 20:
        print("❌ API key appears to be invalid (too short)")
        return False
    
    print(f"✅ API key found: {api_key[:8]}...{api_key[-4:]}")
    
    # Step 2: Test assistant initialization
    print("\n2. Testing assistant initialization...")
    try:
        extractor = AssistantBasedExtractor()
        print(f"✅ Assistant initialized successfully")
        print(f"   Assistant ID: {extractor.assistant_id}")
    except Exception as e:
        print(f"❌ Failed to initialize assistant: {e}")
        return False
    
    # Step 3: Test basic connectivity
    print("\n3. Testing basic connectivity...")
    try:
        # Just test that we can make a simple API call
        client = extractor.client
        # Get the current model list as a simple connectivity test
        models = client.models.list()
        if models:
            print("✅ API connectivity test successful")
        else:
            print("⚠️  API connectivity test returned no models")
    except Exception as e:
        print(f"❌ API connectivity test failed: {e}")
        return False
    
    print("\n🎉 All integration tests passed!")
    print("The assistant is properly connected to your API key setup.")
    return True

def show_api_key_setup_instructions():
    """Show instructions for setting up the API key"""
    print("\n" + "="*60)
    print("API KEY SETUP INSTRUCTIONS")
    print("="*60)
    print("\nTo use the assistant-based extraction, you need a valid OpenAI API key.")
    print("\nOption 1: Environment Variable")
    print("Add this line to your .env file or set as environment variable:")
    print("   OPENAI_API_KEY=sk-your-actual-api-key-here")
    print("\nOption 2: Manual Test")
    print("For testing purposes, you can set it directly:")
    print("   export OPENAI_API_KEY=sk-your-actual-api-key-here")
    print("\nOption 3: Check Existing Setup")
    print("If you're already using the tool, your API key might be:")
    print("   - In your .env file")
    print("   - Set in the application UI")
    print("   - In your config.py file")

if __name__ == "__main__":
    success = test_assistant_integration()
    
    if not success:
        show_api_key_setup_instructions()