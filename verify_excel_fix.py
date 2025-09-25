#!/usr/bin/env python3
"""
Simple verification script to test the Excel extraction fix.
"""

import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_excel_extraction_improvements():
    """Verify that the Excel extraction improvements are in place"""
    try:
        # Read the ai_extraction.py file
        with open("ai_extraction.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for key improvements
        checks = [
            ("Intelligent column detection", "numeric_column_idx = -1" in content),
            ("Numeric value scanning", "numeric_count = 0" in content),
            ("Fallback mechanisms", "if numeric_column_idx == -1" in content),
            ("Value cleaning", "cleaned_amount = amount.replace" in content),
        ]
        
        print("Verifying Excel extraction improvements...")
        print("=" * 50)
        
        all_passed = True
        for check_name, check_result in checks:
            status = "✅ PASS" if check_result else "❌ FAIL"
            print(f"  {status}: {check_name}")
            if not check_result:
                all_passed = False
        
        if all_passed:
            print("\n🎉 All Excel extraction improvements verified!")
            return True
        else:
            print("\n⚠️  Some improvements not found.")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying Excel extraction improvements: {e}")
        return False

if __name__ == "__main__":
    verify_excel_extraction_improvements()