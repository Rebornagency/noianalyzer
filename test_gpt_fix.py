"""
Test file to verify the GPT extraction fix
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that we can import the classes without syntax errors"""
    try:
        from world_class_extraction import WorldClassExtractor
        print("✅ WorldClassExtractor imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import WorldClassExtractor: {e}")
        return False

def test_method_structure():
    """Test that the fixed methods have the correct structure"""
    try:
        from world_class_extraction import WorldClassExtractor
        
        # Check that the class has the expected methods
        methods = [method for method in dir(WorldClassExtractor) if not method.startswith('_')]
        expected_methods = ['extract_data']
        
        for method in expected_methods:
            if method not in methods:
                print(f"❌ Missing expected method: {method}")
                return False
                
        print("✅ WorldClassExtractor has expected method structure")
        return True
    except Exception as e:
        print(f"❌ Error checking method structure: {e}")
        return False

def test_gpt_method_fix():
    """Test that the _extract_with_gpt method no longer passes client parameter"""
    try:
        # Read the file and check that it doesn't contain the problematic code
        with open("world_class_extraction.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        # Check that we're not passing client parameter to chat_completion
        if "client=self.client" in content and "chat_completion" in content:
            # But make sure it's in the right context (the old broken version)
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "client=self.client" in line and "chat_completion" in line:
                    print(f"❌ Found problematic client parameter in world_class_extraction.py at line {i+1}: {line.strip()}")
                    return False
                    
        print("✅ _extract_with_gpt method fix verified")
        return True
    except Exception as e:
        print(f"❌ Error checking _extract_with_gpt method: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("TESTING GPT EXTRACTION FIX")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_method_structure,
        test_gpt_method_fix
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"❌ {test.__name__} failed")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("\nThe GPT extraction fix has been successfully implemented:")
        print("✅ Removed problematic 'client' parameter from chat_completion calls")
        print("✅ WorldClassExtractor imports correctly")
        print("✅ Method structure is intact")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("Please review the errors above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)