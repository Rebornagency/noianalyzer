#!/usr/bin/env python3
"""
Comprehensive test script to verify all data extraction and calculation improvements.
"""

import sys
import os
import logging
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_comprehensive_validation():
    """Test comprehensive validation of data extraction and calculations."""
    print("Testing comprehensive validation of data extraction and calculations...")
    
    try:
        from utils.helpers import format_for_noi_comparison
        from utils.common import safe_float
        from noi_calculations import validate_comparison_results
        from constants import MAIN_METRICS, OPEX_COMPONENTS, INCOME_COMPONENTS
        
        # Test case 1: Complete data with all field variations
        print("\n--- Test Case 1: Complete data with field variations ---")
        api_response_1 = {
            "file_name": "test_financial_statement.pdf",
            "gross_rental_income": 100000,  # GPR variation
            "vacancy_and_credit_loss": 5000,  # Vacancy loss variation
            "concessions": 2000,
            "bad_debt": 1000,
            "other_income": 15000,
            "effective_income": 97000,  # EGI variation
            "operating_costs": 51000,  # OpEx variation
            "net_operating_earnings": 46000,  # NOI variation
            "property_taxes": 15000,
            "insurance": 8000,
            "repairs_and_maintenance": 12000,
            "utilities": 6000,
            "property_management": 10000,  # Management fees variation
            "parking_income": 5000,  # Parking income variation
            "laundry_income": 2000,  # Laundry income variation
            "late_fee_income": 1000,  # Late fees variation
            "pet_rent": 2000,  # Pet fees variation
            "application_fee_income": 1500,  # Application fees variation
            "storage_income": 1000,  # Storage fees variation
            "amenity_income": 2500,  # Amenity fees variation
            "utility_reimbursement_income": 2000,  # Utility reimbursements variation
            "cleaning_income": 1000,  # Cleaning fees variation
            "cancellation_fee_income": 500,  # Cancellation fees variation
            "misc": 2000  # Miscellaneous variation
        }
        
        # Format the data
        formatted_data_1 = format_for_noi_comparison(api_response_1)
        
        # Check that all fields are properly extracted
        assert formatted_data_1["gpr"] == 100000, f"Expected GPR=100000, got {formatted_data_1['gpr']}"
        assert formatted_data_1["vacancy_loss"] == 5000, f"Expected Vacancy Loss=5000, got {formatted_data_1['vacancy_loss']}"
        assert formatted_data_1["concessions"] == 2000, f"Expected Concessions=2000, got {formatted_data_1['concessions']}"
        assert formatted_data_1["bad_debt"] == 1000, f"Expected Bad Debt=1000, got {formatted_data_1['bad_debt']}"
        assert formatted_data_1["other_income"] == 15000, f"Expected Other Income=15000, got {formatted_data_1['other_income']}"
        assert formatted_data_1["egi"] == 97000, f"Expected EGI=97000, got {formatted_data_1['egi']}"
        assert formatted_data_1["opex"] == 51000, f"Expected OpEx=51000, got {formatted_data_1['opex']}"
        assert formatted_data_1["noi"] == 46000, f"Expected NOI=46000, got {formatted_data_1['noi']}"
        
        # Check that all income components are captured
        assert formatted_data_1["parking"] == 5000, f"Expected Parking=5000, got {formatted_data_1['parking']}"
        assert formatted_data_1["laundry"] == 2000, f"Expected Laundry=2000, got {formatted_data_1['laundry']}"
        assert formatted_data_1["late_fees"] == 1000, f"Expected Late Fees=1000, got {formatted_data_1['late_fees']}"
        assert formatted_data_1["pet_fees"] == 2000, f"Expected Pet Fees=2000, got {formatted_data_1['pet_fees']}"
        assert formatted_data_1["application_fees"] == 1500, f"Expected Application Fees=1500, got {formatted_data_1['application_fees']}"
        assert formatted_data_1["storage_fees"] == 1000, f"Expected Storage Fees=1000, got {formatted_data_1['storage_fees']}"
        assert formatted_data_1["amenity_fees"] == 2500, f"Expected Amenity Fees=2500, got {formatted_data_1['amenity_fees']}"
        assert formatted_data_1["utility_reimbursements"] == 2000, f"Expected Utility Reimbursements=2000, got {formatted_data_1['utility_reimbursements']}"
        assert formatted_data_1["cleaning_fees"] == 1000, f"Expected Cleaning Fees=1000, got {formatted_data_1['cleaning_fees']}"
        assert formatted_data_1["cancellation_fees"] == 500, f"Expected Cancellation Fees=500, got {formatted_data_1['cancellation_fees']}"
        assert formatted_data_1["miscellaneous"] == 2000, f"Expected Miscellaneous=2000, got {formatted_data_1['miscellaneous']}"
        
        # Check that all expense components are captured
        assert formatted_data_1["property_taxes"] == 15000, f"Expected Property Taxes=15000, got {formatted_data_1['property_taxes']}"
        assert formatted_data_1["insurance"] == 8000, f"Expected Insurance=8000, got {formatted_data_1['insurance']}"
        assert formatted_data_1["repairs_maintenance"] == 12000, f"Expected Repairs & Maintenance=12000, got {formatted_data_1['repairs_maintenance']}"
        assert formatted_data_1["utilities"] == 6000, f"Expected Utilities=6000, got {formatted_data_1['utilities']}"
        assert formatted_data_1["management_fees"] == 10000, f"Expected Management Fees=10000, got {formatted_data_1['management_fees']}"
        
        print("✓ Test Case 1 passed: Complete data with field variations")
        
        # Test case 2: Data with missing EGI and NOI (should be calculated)
        print("\n--- Test Case 2: Data with missing EGI and NOI ---")
        api_response_2 = {
            "file_name": "test_financial_statement_2.pdf",
            "gross_potential_rent": 120000,
            "vacancy_loss": 6000,
            "concessions": 2500,
            "bad_debt": 1200,
            "other_income": 18000,
            "operating_expenses": 55000,
            "property_taxes": 16000,
            "insurance": 9000,
            "repairs_maintenance": 14000,
            "utilities": 7000,
            "management_fees": 11000,
            "parking": 6000,
            "laundry": 2500,
            "late_fees": 1200,
            "pet_fees": 2500,
            "application_fees": 1800,
            "storage_fees": 1200,
            "amenity_fees": 3000,
            "utility_reimbursements": 2500,
            "cleaning_fees": 1200,
            "cancellation_fees": 600,
            "miscellaneous": 2500
        }
        
        # Format the data
        formatted_data_2 = format_for_noi_comparison(api_response_2)
        
        # Calculate expected values
        expected_egi_2 = 120000 - 6000 - 2500 - 1200 + 18000  # 126300
        expected_noi_2 = expected_egi_2 - 55000  # 71300
        
        # Check that EGI and NOI are calculated correctly
        assert formatted_data_2["egi"] == expected_egi_2, f"Expected EGI={expected_egi_2}, got {formatted_data_2['egi']}"
        assert formatted_data_2["noi"] == expected_noi_2, f"Expected NOI={expected_noi_2}, got {formatted_data_2['noi']}"
        
        print("✓ Test Case 2 passed: Data with missing EGI and NOI")
        
        # Test case 3: Validation of comparison results
        print("\n--- Test Case 3: Validation of comparison results ---")
        comparison_data = {
            "current": {
                "gpr": 100000,
                "vacancy_loss": 5000,
                "concessions": 2000,
                "bad_debt": 1000,
                "other_income": 5000,
                "egi": 95000,  # Incorrect value, should be 97000
                "opex": 51000,
                "noi": 44000,  # Incorrect value, should be 46000
                "property_taxes": 15000,
                "insurance": 8000,
                "repairs_maintenance": 12000,
                "utilities": 6000,
                "management_fees": 10000,
                "parking": 2000,
                "laundry": 1000,
                "late_fees": 500,
                "pet_fees": 1000,
                "application_fees": 750,
                "storage_fees": 500,
                "amenity_fees": 1250,
                "utility_reimbursements": 1000,
                "cleaning_fees": 500,
                "cancellation_fees": 250,
                "miscellaneous": 1000
            }
        }
        
        # Validate the comparison results (this should correct the values)
        validate_comparison_results(comparison_data)
        
        # Check that values were corrected
        current_data = comparison_data["current"]
        assert current_data["egi"] == 97000, f"Expected corrected EGI=97000, got {current_data['egi']}"
        assert current_data["noi"] == 46000, f"Expected corrected NOI=46000, got {current_data['noi']}"
        
        print("✓ Test Case 3 passed: Validation of comparison results")
        
        # Test case 4: Edge case with zero values
        print("\n--- Test Case 4: Edge case with zero values ---")
        api_response_4 = {
            "file_name": "test_financial_statement_4.pdf",
            "gross_potential_rent": 0,
            "vacancy_loss": 0,
            "concessions": 0,
            "bad_debt": 0,
            "other_income": 0,
            "operating_expenses": 0,
            "property_taxes": 0,
            "insurance": 0,
            "repairs_maintenance": 0,
            "utilities": 0,
            "management_fees": 0
        }
        
        # Format the data
        formatted_data_4 = format_for_noi_comparison(api_response_4)
        
        # Check that all values are zero
        assert formatted_data_4["gpr"] == 0, f"Expected GPR=0, got {formatted_data_4['gpr']}"
        assert formatted_data_4["egi"] == 0, f"Expected EGI=0, got {formatted_data_4['egi']}"
        assert formatted_data_4["opex"] == 0, f"Expected OpEx=0, got {formatted_data_4['opex']}"
        assert formatted_data_4["noi"] == 0, f"Expected NOI=0, got {formatted_data_4['noi']}"
        
        print("✓ Test Case 4 passed: Edge case with zero values")
        
        print("\n✅ All comprehensive validation tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Comprehensive validation test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Run the comprehensive validation test
    success = test_comprehensive_validation()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)