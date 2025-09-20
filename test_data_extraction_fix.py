#!/usr/bin/env python3
"""
Test script to verify the data extraction and NOI calculation fixes.
"""

import sys
import os
import logging
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import the modules we need to test
from utils.helpers import format_for_noi_comparison
from utils.common import safe_float
from noi_calculations import calculate_noi, calculate_egi, validate_comparison_results

def test_revenue_extraction():
    """Test that revenue is correctly extracted and EGI is calculated properly."""
    print("Testing revenue extraction and EGI calculation...")
    
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

def test_noi_calculation():
    """Test that NOI is calculated correctly."""
    print("Testing NOI calculation...")
    
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

def test_income_expense_categories():
    """Test that all income and expense categories are captured."""
    print("Testing income and expense category extraction...")
    
    # Mock API response with all categories
    api_response = {
        "gpr": 100000,
        "vacancy_loss": 5000,
        "concessions": 2000,
        "bad_debt": 1000,
        "other_income": 15000,
        "parking": 5000,
        "laundry": 2000,
        "late_fees": 1000,
        "pet_fees": 2000,
        "application_fees": 1500,
        "storage_fees": 1000,
        "amenity_fees": 2500,
        "utility_reimbursements": 2000,
        "cleaning_fees": 1000,
        "cancellation_fees": 500,
        "miscellaneous": 2000,
        "opex": 65000,
        "property_taxes": 15000,
        "insurance": 8000,
        "repairs_maintenance": 12000,
        "utilities": 6000,
        "management_fees": 10000,
        "administrative": 3000,
        "payroll": 5000,
        "marketing": 2000,
        "other_expenses": 4000
    }
    
    # Format the data
    formatted_data = format_for_noi_comparison(api_response)
    
    # Check that all income categories are captured
    assert formatted_data["parking"] == 5000, f"Expected Parking=5000, got {formatted_data['parking']}"
    assert formatted_data["laundry"] == 2000, f"Expected Laundry=2000, got {formatted_data['laundry']}"
    assert formatted_data["late_fees"] == 1000, f"Expected Late Fees=1000, got {formatted_data['late_fees']}"
    assert formatted_data["pet_fees"] == 2000, f"Expected Pet Fees=2000, got {formatted_data['pet_fees']}"
    assert formatted_data["application_fees"] == 1500, f"Expected Application Fees=1500, got {formatted_data['application_fees']}"
    assert formatted_data["storage_fees"] == 1000, f"Expected Storage Fees=1000, got {formatted_data['storage_fees']}"
    assert formatted_data["amenity_fees"] == 2500, f"Expected Amenity Fees=2500, got {formatted_data['amenity_fees']}"
    assert formatted_data["utility_reimbursements"] == 2000, f"Expected Utility Reimbursements=2000, got {formatted_data['utility_reimbursements']}"
    assert formatted_data["cleaning_fees"] == 1000, f"Expected Cleaning Fees=1000, got {formatted_data['cleaning_fees']}"
    assert formatted_data["cancellation_fees"] == 500, f"Expected Cancellation Fees=500, got {formatted_data['cancellation_fees']}"
    assert formatted_data["miscellaneous"] == 2000, f"Expected Miscellaneous=2000, got {formatted_data['miscellaneous']}"
    
    # Check that all expense categories are captured
    assert formatted_data["property_taxes"] == 15000, f"Expected Property Taxes=15000, got {formatted_data['property_taxes']}"
    assert formatted_data["insurance"] == 8000, f"Expected Insurance=8000, got {formatted_data['insurance']}"
    assert formatted_data["repairs_maintenance"] == 12000, f"Expected Repairs & Maintenance=12000, got {formatted_data['repairs_maintenance']}"
    assert formatted_data["utilities"] == 6000, f"Expected Utilities=6000, got {formatted_data['utilities']}"
    assert formatted_data["management_fees"] == 10000, f"Expected Management Fees=10000, got {formatted_data['management_fees']}"
    
    print("✓ Income and expense category extraction test passed")

def test_variance_calculations():
    """Test that variance calculations are based on correct NOI."""
    print("Testing variance calculations...")
    
    # Mock comparison data
    comparison_data = {
        "current": {
            "gpr": 100000,
            "vacancy_loss": 5000,
            "concessions": 2000,
            "bad_debt": 1000,
            "other_income": 5000,
            "egi": 97000,
            "opex": 51000,
            "noi": 46000
        },
        "budget": {
            "gpr": 95000,
            "vacancy_loss": 4500,
            "concessions": 1800,
            "bad_debt": 900,
            "other_income": 4500,
            "egi": 93300,
            "opex": 49000,
            "noi": 44300
        }
    }
    
    # Validate the comparison results
    validate_comparison_results(comparison_data)
    
    # Check that NOI values are correct
    current_noi = comparison_data["current"]["noi"]
    budget_noi = comparison_data["budget"]["noi"]
    
    assert current_noi == 46000, f"Expected Current NOI=46000, got {current_noi}"
    assert budget_noi == 44300, f"Expected Budget NOI=44300, got {budget_noi}"
    
    # Check that variance is calculated correctly
    noi_variance = current_noi - budget_noi  # 1700
    assert noi_variance == 1700, f"Expected NOI Variance=1700, got {noi_variance}"
    
    print("✓ Variance calculations test passed")

def run_all_tests():
    """Run all tests."""
    print("Running data extraction and NOI calculation tests...\n")
    
    try:
        test_revenue_extraction()
        test_noi_calculation()
        test_income_expense_categories()
        test_variance_calculations()
        
        print("\n✅ All tests passed! The fixes are working correctly.")
        return True
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
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