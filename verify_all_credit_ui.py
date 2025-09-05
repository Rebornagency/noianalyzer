import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_credit_ui_modules():
    """Test that all credit UI modules can be imported without errors"""
    modules_to_test = [
        ("utils.credit_ui", "Main credit UI"),
        ("utils.credit_ui_minimal", "Minimal credit UI"),
        ("utils.credit_ui_fresh", "Fresh credit UI"),
        ("utils.credit_ui_robust", "Robust credit UI"),
        ("utils.credit_ui_simple", "Simple credit UI"),
    ]
    
    results = []
    for module_path, description in modules_to_test:
        try:
            # Import the module
            module = __import__(module_path, fromlist=['display_credit_store'])
            # Check if display_credit_store function exists
            if hasattr(module, 'display_credit_store'):
                results.append(f"✅ {description}: Successfully imported display_credit_store")
            else:
                results.append(f"❌ {description}: Module imported but display_credit_store function not found")
        except Exception as e:
            results.append(f"❌ {description}: Failed to import - {e}")
    
    return results

def check_syntax_errors():
    """Check for syntax errors in credit UI files"""
    import ast
    
    files_to_check = [
        "utils/credit_ui.py",
        "utils/credit_ui_minimal.py",
        "utils/credit_ui_fresh.py",
        "utils/credit_ui_robust.py",
        "utils/credit_ui_simple.py",
    ]
    
    results = []
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            results.append(f"✅ No syntax errors in {file_path}")
        except SyntaxError as e:
            results.append(f"❌ Syntax error in {file_path}: {e}")
        except Exception as e:
            results.append(f"❌ Error reading {file_path}: {e}")
    
    return results

if __name__ == "__main__":
    print("🔍 Verifying All Credit UI Modules...")
    print("=" * 50)
    
    # Check syntax errors first
    print("Checking syntax errors:")
    syntax_results = check_syntax_errors()
    for result in syntax_results:
        print(f"  {result}")
    print()
    
    # Test imports
    print("Testing module imports:")
    import_results = test_credit_ui_modules()
    for result in import_results:
        print(f"  {result}")
    print()
    
    # Summary
    all_good = all("✅" in result for result in syntax_results) and all("✅" in result for result in import_results)
    
    if all_good:
        print("🎉 All credit UI modules are working correctly!")
        sys.exit(0)
    else:
        print("❌ Some credit UI modules have issues. Please check the errors above.")
        sys.exit(1)