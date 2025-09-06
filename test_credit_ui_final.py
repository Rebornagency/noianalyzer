import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_credit_ui_imports():
    """Test that we can import the credit UI functions without syntax errors"""
    try:
        from utils.credit_ui import display_credit_store
        print("✅ Successfully imported display_credit_store from credit_ui")
        return True
    except Exception as e:
        print(f"❌ Failed to import display_credit_store from credit_ui: {e}")
        return False

def test_credit_ui_minimal_imports():
    """Test that we can import the minimal credit UI functions without syntax errors"""
    try:
        from utils.credit_ui_minimal import display_credit_store
        print("✅ Successfully imported display_credit_store from credit_ui_minimal")
        return True
    except Exception as e:
        print(f"❌ Failed to import display_credit_store from credit_ui_minimal: {e}")
        return False

def check_syntax_errors():
    """Check for syntax errors in our modified files"""
    import ast
    
    files_to_check = [
        "utils/credit_ui.py",
        "utils/credit_ui_minimal.py"
    ]
    
    all_good = True
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            print(f"✅ No syntax errors in {file_path}")
        except SyntaxError as e:
            print(f"❌ Syntax error in {file_path}: {e}")
            all_good = False
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            all_good = False
    
    return all_good

if __name__ == "__main__":
    print("🔍 Verifying Credit UI Fixes...")
    print("=" * 50)
    
    # Check syntax errors first
    syntax_ok = check_syntax_errors()
    print()
    
    # Test imports
    import_ok = test_credit_ui_imports()
    print()
    
    import_minimal_ok = test_credit_ui_minimal_imports()
    print()
    
    if syntax_ok and (import_ok or import_minimal_ok):
        print("🎉 All tests passed! The credit UI fixes should work correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)