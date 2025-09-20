#!/usr/bin/env python3
"""
Simple test script to verify the data extraction and NOI calculation fixes.
"""

import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_imports():
    """Test that we can import the necessary modules."""
    print("Testing imports...")
    
    try:
        from utils.helpers import format_for_noi_comparison
        print("✓ format_for_noi_comparison imported successfully")
    except Exception as e:
        print(f"✗ Failed to import format_for_noi_comparison: {e}")
        return False
    
    try:
        from utils.common import safe_float
        print("✓ safe_float imported successfully")
    except Exception as e:
        print(f"✗ Failed to import safe_float: {e}")
        return False
    
    try:
        from noi_calculations import calculate_noi, calculate_egi, validate_comparison_results
        print("✓ NOI calculation functions imported successfully")
    except Exception as e:
        print(f"✗ Failed to import NOI calculation functions: {e}")
        return False
    
    return True

def test_revenue_extraction():
    """Test that revenue is correctly extracted and EGI is calculated properly."""
    print("Testing revenue extraction and EGI calculation...")
    
    try:
        from utils.helpers import format_for_noi_comparison
        from utils.common import safe_float
        
        # Mock API response with various field name variations
        api_response = {
            "gross_potential_rent": 100000,
            "vacancy_loss": 5000,
            "concessions": 2000,
            "bad_debt": 1000,
            "other_income": 5000,
            "property_taxes": 15000,
            "insurance": 8000,
            "repairs_maintenance": 12000,
            "utilities": 6000,
            "management_fees": 10000
        }
        
        # Format the data
        formatted_data = format_for_noi_comparison(api_response)
        
        # Check that all fields are properly extracted
        assert formatted_data["gpr"] == 100000, f"Expected GPR=100000, got {formatted_data['gpr']}"
        assert formatted_data["vacancy_loss"] == 5000, f"Expected Vacancy Loss=5000, got {formatted_data['vacancy_loss']}"
        assert formatted_data["concessions"] == 2000, f"Expected Concessions=2000, got {formatted_data['concessions']}"
        assert formatted_data["bad_debt"] == 1000, f"Expected Bad Debt=1000, got {formatted_data['bad_debt']}"
        assert formatted_data["other_income"] == 5000, f"Expected Other Income=5000, got {formatted_data['other_income']}"
        
        # Check that EGI is calculated correctly
        expected_egi = 100000 - 5000 - 2000 - 1000 + 5000  # 97000
        assert formatted_data["egi"] == expected_egi, f"Expected EGI={expected_egi}, got {formatted_data['egi']}"
        
        # Check that OpEx is calculated correctly
        expected_opex = 15000 + 8000 + 12000 + 6000 + 10000  # 51000
        assert formatted_data["opex"] == expected_opex, f"Expected OpEx={expected_opex}, got {formatted_data['opex']}"
        
        print("✓ Revenue extraction and EGI calculation test passed")
        return True
    except Exception as e:
        print(f"✗ Revenue extraction test failed: {e}")
        return False

def test_noi_calculation():
    """Test that NOI is calculated correctly."""
    print("Testing NOI calculation...")
    
    try:
        from utils.helpers import format_for_noi_comparison
        from utils.common import safe_float
        from noi_calculations import calculate_noi, calculate_egi
        
        # Mock API response
        api_response = {
            "gpr": 100000,
            "vacancy_loss": 5000,
            "concessions": 2000,
            "bad_debt": 1000,
            "other_income": 5000,
            "opex": 51000
        }
        
        # Format the data
        formatted_data = format_for_noi_comparison(api_response)
        
        # Check that NOI is calculated correctly
        expected_egi = 100000 - 5000 - 2000 - 1000 + 5000  # 97000
        expected_noi = expected_egi - 51000  # 46000
        assert formatted_data["noi"] == expected_noi, f"Expected NOI={expected_noi}, got {formatted_data['noi']}"
        
        print("✓ NOI calculation test passed")
        return True
    except Exception as e:
        print(f"✗ NOI calculation test failed: {e}")
        return False

def run_all_tests():
    """Run all tests."""
    print("Running simple data extraction and NOI calculation tests...\n")
    
    tests = [
        test_imports,
        test_revenue_extraction,
        test_noi_calculation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add a blank line between tests
    
    if passed == total:
        print(f"✅ All {total} tests passed! The fixes are working correctly.")
        return True
    else:
        print(f"❌ {passed}/{total} tests passed. Some fixes may not be working correctly.")
        return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Run the tests
    success = run_all_tests()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)