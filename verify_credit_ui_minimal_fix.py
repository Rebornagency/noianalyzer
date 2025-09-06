import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_credit_ui_minimal_import():
    """Test that we can import the minimal credit UI functions without syntax errors"""
    try:
        from utils.credit_ui_minimal import display_credit_store
        print("✅ Successfully imported display_credit_store from credit_ui_minimal")
        return True
    except Exception as e:
        print(f"❌ Failed to import display_credit_store from credit_ui_minimal: {e}")
        return False

def check_syntax_errors():
    """Check for syntax errors in our modified file"""
    import ast
    
    file_path = "utils/credit_ui_minimal.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print(f"✅ No syntax errors in {file_path}")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Verifying Credit UI Minimal Fix...")
    print("=" * 50)
    
    # Check syntax errors first
    syntax_ok = check_syntax_errors()
    print()
    
    # Test imports
    import_ok = test_credit_ui_minimal_import()
    print()
    
    if syntax_ok and import_ok:
        print("🎉 Credit UI Minimal fix is working correctly!")
        sys.exit(0)
    else:
        print("❌ Credit UI Minimal fix has issues.")
        sys.exit(1)