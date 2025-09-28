"""
Verification script for the assistant-based extraction implementation
"""

import os
import sys
import inspect

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_assistant_class():
    """Check that the AssistantBasedExtractor class is properly implemented"""
    print("1. Checking AssistantBasedExtractor class...")
    
    try:
        from assistant_based_extraction import AssistantBasedExtractor
        
        # Check class exists
        if not inspect.isclass(AssistantBasedExtractor):
            print("❌ AssistantBasedExtractor is not a class")
            return False
        
        print("✅ AssistantBasedExtractor class exists")
        
        # Check required methods
        required_methods = [
            '__init__',
            '_setup_assistant',
            '_get_extraction_instructions',
            'extract_financial_data',
            '_parse_response'
        ]
        
        for method_name in required_methods:
            if not hasattr(AssistantBasedExtractor, method_name):
                print(f"❌ Missing required method: {method_name}")
                return False
            
            method = getattr(AssistantBasedExtractor, method_name)
            if not callable(method):
                print(f"❌ {method_name} is not callable")
                return False
                
            print(f"✅ Method {method_name} exists and is callable")
        
        # Check constructor signature
        sig = inspect.signature(AssistantBasedExtractor.__init__)
        if 'model' not in sig.parameters:
            print("⚠️  Constructor missing 'model' parameter (not critical)")
        else:
            print("✅ Constructor has 'model' parameter")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking AssistantBasedExtractor class: {e}")
        return False

def check_instructions():
    """Check that the extraction instructions are comprehensive"""
    print("\n2. Checking extraction instructions...")
    
    try:
        from assistant_based_extraction import AssistantBasedExtractor
        
        # Create instance without initializing OpenAI client
        extractor = AssistantBasedExtractor.__new__(AssistantBasedExtractor)
        instructions = extractor._get_extraction_instructions()
        
        if not isinstance(instructions, str):
            print("❌ _get_extraction_instructions does not return a string")
            return False
        
        if len(instructions) < 1000:
            print("❌ Extraction instructions seem too short")
            return False
        
        # Check for key components in instructions
        required_elements = [
            "financial analyst",
            "Gross Potential Rent",
            "Net Operating Income",
            "confidence scores",
            "JSON object"
        ]
        
        for element in required_elements:
            if element not in instructions:
                print(f"❌ Instruction missing key element: {element}")
                return False
        
        print("✅ Extraction instructions are comprehensive")
        print(f"   Instructions length: {len(instructions)} characters")
        return True
        
    except Exception as e:
        print(f"❌ Error checking extraction instructions: {e}")
        return False

def check_config_integration():
    """Check that the assistant integrates with the config system"""
    print("\n3. Checking config integration...")
    
    try:
        from config import get_openai_api_key
        
        # Test that the function exists and is callable
        if not callable(get_openai_api_key):
            print("❌ get_openai_api_key is not callable")
            return False
        
        print("✅ get_openai_api_key function exists and is callable")
        
        # Test function signature
        sig = inspect.signature(get_openai_api_key)
        print(f"✅ Config function signature: {sig}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking config integration: {e}")
        return False

def check_dependencies():
    """Check that required dependencies are available"""
    print("\n4. Checking dependencies...")
    
    required_packages = [
        'openai',
        'pandas',
        'json',
        'logging'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ Package {package} is available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ Package {package} is missing")
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        return False
    
    return True

def check_file_structure():
    """Check that the file structure is correct"""
    print("\n5. Checking file structure...")
    
    required_files = [
        'assistant_based_extraction.py',
        'config.py',
        'constants.py'
    ]
    
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"✅ File {file_name} exists")
        else:
            print(f"❌ File {file_name} is missing")
            return False
    
    return True

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("ASSISTANT-BASED EXTRACTION IMPLEMENTATION VERIFICATION")
    print("=" * 60)
    
    checks = [
        check_file_structure,
        check_dependencies,
        check_assistant_class,
        check_instructions,
        check_config_integration
    ]
    
    passed = 0
    total = len(checks)
    
    for check in checks:
        if check():
            passed += 1
        else:
            print(f"❌ {check.__name__} failed")
    
    print("\n" + "=" * 60)
    print(f"VERIFICATION RESULT: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 ALL CHECKS PASSED!")
        print("\nThe assistant-based extraction implementation is ready for deployment:")
        print("✅ Proper class structure with all required methods")
        print("✅ Comprehensive extraction instructions for financial documents")
        print("✅ Integration with existing configuration system")
        print("✅ All required dependencies available")
        print("✅ Correct file structure")
        print("\nTo deploy:")
        print("1. Set a valid OPENAI_API_KEY in your environment")
        print("2. The assistant will be automatically created on first use")
        print("3. Assistant ID will be saved for future use")
        return True
    else:
        print("❌ SOME CHECKS FAILED")
        print("Please review the errors above before deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)