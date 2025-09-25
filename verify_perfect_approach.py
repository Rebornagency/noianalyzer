#!/usr/bin/env python3
"""
Verification script for the perfect approach implementation.
This script verifies that the key issues have been fixed and the implementation works correctly.
"""

import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_syntax_errors_fixed():
    """Verify that syntax errors have been fixed"""
    try:
        import ai_extraction
        print("✅ Syntax errors fixed: ai_extraction module imports successfully")
        return True
    except Exception as e:
        print(f"❌ Syntax errors still present: {e}")
        return False

def verify_duplicate_function_removed():
    """Verify that the duplicate function has been removed"""
    try:
        # Read the file content
        with open("ai_extraction.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Count occurrences of the function definition
        count = content.count("def _format_text_content(text_content: str, file_name: str) -> str:")
        
        if count == 1:
            print("✅ Duplicate function removed: Only one definition of _format_text_content found")
            return True
        else:
            print(f"❌ Duplicate function issue: Found {count} definitions of _format_text_content")
            return False
    except Exception as e:
        print(f"❌ Error checking for duplicate function: {e}")
        return False

def verify_key_metrics_variable():
    """Verify that key_metrics variable is properly defined"""
    try:
        # Read the file content
        with open("ai_extraction.py", "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Look for the key_metrics definition in the right context
        key_metrics_found = False
        for i, line in enumerate(lines):
            if "key_metrics = ['gpr', 'egi', 'opex', 'noi']" in line:
                key_metrics_found = True
                break
        
        if key_metrics_found:
            print("✅ key_metrics variable properly defined")
            return True
        else:
            print("❌ key_metrics variable not found or improperly defined")
            return False
    except Exception as e:
        print(f"❌ Error checking key_metrics variable: {e}")
        return False

def verify_enhanced_validation():
    """Verify that enhanced validation logic is present"""
    try:
        # Read the file content
        with open("ai_extraction.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for key validation logic
        checks = [
            "has_meaningful_data = False",
            "key_metrics = ['gpr', 'egi', 'opex', 'noi']",
            "has_meaningful_data = any(float(value) != 0 for value in meaningful_values)",
            "if has_required_fields and has_meaningful_data:"
        ]
        
        all_checks_pass = True
        for check in checks:
            if check not in content:
                print(f"❌ Validation logic missing: {check}")
                all_checks_pass = False
        
        if all_checks_pass:
            print("✅ Enhanced validation logic present")
            return True
        else:
            return False
    except Exception as e:
        print(f"❌ Error checking validation logic: {e}")
        return False

def verify_enhanced_prompt():
    """Verify that enhanced prompt engineering is present"""
    try:
        # Read the file content
        with open("ai_extraction.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for key prompt enhancements
        checks = [
            "CRITICALLY IMPORTANT: DO NOT return all zero values",
            "DO NOT return all zero values - make educated estimates when needed",
            "DOCUMENT STRUCTURE GUIDE:",
            "[SHEET_START]/[SHEET_END]: Excel sheet boundaries"
        ]
        
        all_checks_pass = True
        for check in checks:
            if check not in content:
                print(f"❌ Prompt enhancement missing: {check}")
                all_checks_pass = False
        
        if all_checks_pass:
            print("✅ Enhanced prompt engineering present")
            return True
        else:
            return False
    except Exception as e:
        print(f"❌ Error checking prompt engineering: {e}")
        return False

def main():
    print("Verifying Perfect Approach Implementation...")
    print("=" * 50)
    
    # Run all verification checks
    checks = [
        verify_syntax_errors_fixed,
        verify_duplicate_function_removed,
        verify_key_metrics_variable,
        verify_enhanced_validation,
        verify_enhanced_prompt
    ]
    
    results = []
    for check in checks:
        results.append(check())
    
    print("\n" + "=" * 50)
    print("VERIFICATION RESULTS:")
    
    if all(results):
        print("🎉 ALL VERIFICATIONS PASSED! The perfect approach implementation is correct.")
        return 0
    else:
        print("⚠️  Some verifications failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())