#!/usr/bin/env python3
"""
Comprehensive test to verify all data extraction improvements
"""

import io
import os
import tempfile
import pandas as pd
import json
from typing import Dict, Any

# Import the modules we want to test
from world_class_extraction import WorldClassExtractor, ExtractionResult, DocumentType, ExtractionConfidence
from preprocessing_module import FilePreprocessor
from ai_extraction import extract_noi_data, validate_and_enrich_extraction_result

def create_test_excel_file() -> bytes:
    """Create a test Excel file with financial data"""
    data = {
        'Category': [
            'Gross Potential Rent',
            'Vacancy Loss',
            'Concessions',
            'Bad Debt',
            'Other Income',
            'Effective Gross Income',
            'Operating Expenses',
            'Property Taxes',
            'Insurance',
            'Repairs & Maintenance',
            'Utilities',
            'Management Fees',
            'Parking',
            'Laundry',
            'Late Fees',
            'Total Operating Expenses',
            'Net Operating Income'
        ],
        'Amount': [
            80000.0,    # Gross Potential Rent
            -2000.0,    # Vacancy Loss
            -1000.0,    # Concessions
            -500.0,     # Bad Debt
            3950.0,     # Other Income
            80450.0,    # Effective Gross Income
            '',         # Operating Expenses header
            -3000.0,    # Property Taxes
            -1500.0,    # Insurance
            -2500.0,    # Repairs & Maintenance
            -2000.0,    # Utilities
            -4000.0,    # Management Fees
            2000.0,     # Parking
            500.0,      # Laundry
            150.0,      # Late Fees
            -16250.0,   # Total Operating Expenses
            64200.0     # Net Operating Income
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Create a temporary file to write the Excel content
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
        df.to_excel(tmp_filename, sheet_name='Financial Statement', index=False)
    
    # Read the file content
    with open(tmp_filename, 'rb') as f:
        excel_content = f.read()
    
    # Clean up the temporary file
    os.unlink(tmp_filename)
    
    return excel_content

def create_test_csv_file() -> bytes:
    """Create a test CSV file with financial data"""
    csv_content = """Category,Amount
Gross Potential Rent,80000.00
Vacancy Loss,-2000.00
Concessions,-1000.00
Bad Debt,-500.00
Other Income,3950.00
Effective Gross Income,80450.00
Property Taxes,-3000.00
Insurance,-1500.00
Repairs & Maintenance,-2500.00
Utilities,-2000.00
Management Fees,-4000.00
Parking,2000.00
Laundry,500.00
Late Fees,150.00
Total Operating Expenses,-16250.00
Net Operating Income,64200.00"""
    
    return csv_content.encode('utf-8')

def create_test_text_file() -> bytes:
    """Create a test text file with financial data"""
    text_content = """
REAL ESTATE FINANCIAL STATEMENT
SEPTEMBER 2025 (ACTUAL)

PROPERTY: Example Commercial/Residential Property
PERIOD: September 1, 2025 - September 30, 2025

REVENUE:
Gross Potential Rent: $80,000.00
Vacancy Loss: ($2,000.00)
Concessions: ($1,000.00)
Bad Debt: ($500.00)
Other Income: $3,950.00
Effective Gross Income: $80,450.00

EXPENSES:
Property Taxes: ($3,000.00)
Insurance: ($1,500.00)
Repairs & Maintenance: ($2,500.00)
Utilities: ($2,000.00)
Management Fees: ($4,000.00)
Parking: $2,000.00
Laundry: $500.00
Late Fees: $150.00
Total Operating Expenses: ($16,250.00)

NET OPERATING INCOME: $64,200.00
"""
    
    return text_content.encode('utf-8')

class MockFile:
    """Mock file object for testing"""
    def __init__(self, content: bytes, name: str = "test_file.xlsx", file_type: str = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
        self.content = content
        self.name = name
        self.type = file_type
    
    def getvalue(self):
        return self.content

def test_world_class_extractor():
    """Test the WorldClassExtractor functionality"""
    print("1. Testing WorldClassExtractor...")
    
    # Create test data
    excel_content = create_test_excel_file()
    
    # Test extraction
    extractor = WorldClassExtractor()
    result = extractor.extract_data(excel_content, "test_financials.xlsx", "current_month_actuals")
    
    # Check result type
    assert isinstance(result, ExtractionResult), "Result should be an ExtractionResult"
    
    # Check data fields
    assert "gross_potential_rent" in result.data, "Should contain gross_potential_rent field"
    assert "net_operating_income" in result.data, "Should contain net_operating_income field"
    
    # Check confidence
    assert result.confidence in ExtractionConfidence, "Should have valid confidence level"
    
    # Check processing time
    assert result.processing_time > 0, "Should have positive processing time"
    
    # Check document type
    assert result.document_type in DocumentType, "Should have valid document type"
    
    print("   ✅ WorldClassExtractor test passed")
    return True

def test_preprocessing_module():
    """Test the preprocessing module functionality"""
    print("2. Testing preprocessing module...")
    
    # Create test data
    excel_content = create_test_excel_file()
    
    # Create temporary file for preprocessing
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        tmp_filename = tmp_file.name
        tmp_file.write(excel_content)
    
    try:
        # Test preprocessing
        preprocessor = FilePreprocessor()
        result = preprocessor.preprocess(tmp_filename, filename="test_financials.xlsx")
        
        # Check result structure
        assert "metadata" in result, "Should contain metadata"
        assert "content" in result, "Should contain content"
        assert "combined_text" in result["content"], "Should contain combined_text"
        
        # Check metadata
        metadata = result["metadata"]
        assert metadata["filename"] == "test_financials.xlsx", "Should have correct filename"
        assert metadata["extension"] == "xlsx", "Should have correct extension"
        
        print("   ✅ Preprocessing module test passed")
        return True
    finally:
        # Clean up temporary file
        os.unlink(tmp_filename)

def test_ai_extraction():
    """Test the AI extraction functionality"""
    print("3. Testing AI extraction...")
    
    # Create mock file
    excel_content = create_test_excel_file()
    mock_file = MockFile(excel_content, "test_financials.xlsx")
    
    # Test extraction
    result = extract_noi_data(mock_file, "current_month_actuals")
    
    # Check result structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "gpr" in result, "Should contain gpr field"
    assert "noi" in result, "Should contain noi field"
    assert result["gpr"] > 0, "GPR should be positive"
    assert result["noi"] > 0, "NOI should be positive"
    
    # Check validation
    validated_result = validate_and_enrich_extraction_result(result, "test_financials.xlsx", "current_month_actuals")
    assert "extraction_timestamp" in validated_result, "Should contain extraction_timestamp"
    assert "extraction_method" in validated_result, "Should contain extraction_method"
    
    print("   ✅ AI extraction test passed")
    return True

def test_zero_value_handling():
    """Test zero value handling in extraction results"""
    print("4. Testing zero value handling...")
    
    # Create test data with zero values
    test_data = {
        "gpr": 0.0,
        "egi": 0.0,
        "noi": 0.0,
        "opex": 5000.0
    }
    
    # Test validation
    validated_result = validate_and_enrich_extraction_result(test_data, "test_file.xlsx", "current_month_actuals")
    
    # Check that all required fields are present
    required_fields = ["gpr", "egi", "noi", "opex"]
    for field in required_fields:
        assert field in validated_result, f"Should contain {field} field"
    
    print("   ✅ Zero value handling test passed")
    return True

def test_consistency_checks():
    """Test consistency checks in financial calculations"""
    print("5. Testing consistency checks...")
    
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
    validated_result = validate_and_enrich_extraction_result(test_data, "test_file.xlsx", "current_month_actuals")
    
    # Check that calculations are corrected
    expected_egi = 80000.0 - 2000.0 - 1000.0 - 500.0 + 3950.0
    expected_noi = expected_egi - 16250.0
    
    # Allow for small floating point differences
    assert abs(validated_result["egi"] - expected_egi) < 1.0, f"EGI should be corrected to {expected_egi}"
    assert abs(validated_result["noi"] - expected_noi) < 1.0, f"NOI should be corrected to {expected_noi}"
    
    print("   ✅ Consistency checks test passed")
    return True

def main():
    """Run all tests"""
    print("Testing all data extraction improvements...")
    print("=" * 50)
    
    # Run individual tests
    tests = [
        test_world_class_extractor,
        test_preprocessing_module,
        test_ai_extraction,
        test_zero_value_handling,
        test_consistency_checks
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"   ❌ Test failed with error: {e}")
            results.append(False)
            print()
    
    # Summary
    print("=" * 50)
    print("SUMMARY:")
    test_names = [
        "WorldClassExtractor",
        "Preprocessing Module",
        "AI Extraction",
        "Zero Value Handling",
        "Consistency Checks"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        print(f"  {name}: {'✅ PASS' if result else '❌ FAIL'}")
    
    overall_success = all(results)
    print()
    if overall_success:
        print("🎉 ALL TESTS PASSED! Data extraction improvements are working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
    
    return overall_success

if __name__ == "__main__":
    main()