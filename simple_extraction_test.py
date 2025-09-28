#!/usr/bin/env python3
"""
Simple test to verify key data extraction improvements
"""

import pandas as pd
import tempfile
import os

# Import the modules we want to test
from world_class_extraction import WorldClassExtractor
from ai_extraction import validate_and_enrich_extraction_result

def test_world_class_extractor():
    """Test the WorldClassExtractor functionality"""
    print("Testing WorldClassExtractor...")
    
    # Create simple test data
    test_data = {
        "gross_potential_rent": 80000.0,
        "vacancy_loss": 2000.0,
        "concessions": 1000.0,
        "bad_debt": 500.0,
        "other_income": 3950.0,
        "effective_gross_income": 80450.0,
        "operating_expenses": 16250.0,
        "net_operating_income": 64200.0
    }
    
    # Test validation function
    result = validate_and_enrich_extraction_result(test_data, "test_file.xlsx", "current_month_actuals")
    
    # Check that result contains expected fields
    expected_fields = ["gpr", "egi", "opex", "noi", "extraction_timestamp", "extraction_method"]
    for field in expected_fields:
        assert field in result, f"Result should contain {field}"
    
    print("✅ WorldClassExtractor validation test passed")
    return True

def test_consistency_checks():
    """Test consistency checks in financial calculations"""
    print("Testing consistency checks...")
    
    # Create test data with inconsistent calculations
    test_data = {
        "gpr": 80000.0,
        "vacancy_loss": 2000.0,
        "concessions": 1000.0,
        "bad_debt": 500.0,
        "other_income": 3950.0,
        "egi": 50000.0,  # Incorrect EGI (should be 80000 - 2000 - 1000 - 500 + 3950 = 80450)
        "opex": 16250.0,
        "noi": 30000.0   # Incorrect NOI (should be 80450 - 16250 = 64200)
    }
    
    # Test validation
    result = validate_and_enrich_extraction_result(test_data, "test_file.xlsx", "current_month_actuals")
    
    # Check that calculations are corrected
    expected_egi = 80000.0 - 2000.0 - 1000.0 - 500.0 + 3950.0
    expected_noi = expected_egi - 16250.0
    
    # Allow for small floating point differences
    assert abs(result["egi"] - expected_egi) < 1.0, f"EGI should be corrected to {expected_egi}"
    assert abs(result["noi"] - expected_noi) < 1.0, f"NOI should be corrected to {expected_noi}"
    
    print("✅ Consistency checks test passed")
    return True

def test_zero_value_handling():
    """Test zero value handling in extraction results"""
    print("Testing zero value handling...")
    
    # Create test data with zero values
    test_data = {
        "gpr": 0.0,
        "egi": 0.0,
        "noi": 0.0,
        "opex": 5000.0
    }
    
    # Test validation
    result = validate_and_enrich_extraction_result(test_data, "test_file.xlsx", "current_month_actuals")
    
    # Check that all required fields are present
    required_fields = ["gpr", "egi", "noi", "opex"]
    for field in required_fields:
        assert field in result, f"Result should contain {field}"
    
    print("✅ Zero value handling test passed")
    return True

def main():
    """Run all tests"""
    print("Testing key data extraction improvements...")
    print("=" * 40)
    
    # Run individual tests
    tests = [
        test_world_class_extractor,
        test_consistency_checks,
        test_zero_value_handling
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    # Summary
    print("=" * 40)
    overall_success = all(results)
    if overall_success:
        print("🎉 ALL TESTS PASSED! Key data extraction improvements are working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
    
    return overall_success

if __name__ == "__main__":
    main()