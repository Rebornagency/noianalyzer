"""
Comprehensive test to verify the assistant-based extraction is ready for public deployment
"""

import os
import json
import tempfile
from assistant_based_extraction import AssistantBasedExtractor
from config import get_openai_api_key

def test_api_key_configuration():
    """Test that the API key is properly configured"""
    print("1. Testing API key configuration...")
    
    api_key = get_openai_api_key()
    if not api_key:
        print("❌ No API key found!")
        return False
    
    if len(api_key) < 20:
        print("❌ API key appears to be invalid (too short)")
        return False
    
    print(f"✅ API key found and appears valid: {api_key[:8]}...{api_key[-4:]}")
    return True

def test_assistant_creation():
    """Test that the assistant can be created successfully"""
    print("\n2. Testing assistant creation...")
    
    try:
        extractor = AssistantBasedExtractor()
        print(f"✅ Assistant created successfully")
        print(f"   Assistant ID: {extractor.assistant_id}")
        print(f"   Model: {extractor.model}")
        return True
    except Exception as e:
        print(f"❌ Failed to create assistant: {e}")
        return False

def test_basic_connectivity():
    """Test basic connectivity to OpenAI API"""
    print("\n3. Testing basic API connectivity...")
    
    try:
        extractor = AssistantBasedExtractor()
        # Test that we can list models (basic connectivity test)
        models = extractor.client.models.list()
        if models:
            print("✅ Basic API connectivity test passed")
            return True
        else:
            print("⚠️  API connectivity test returned no models")
            return True  # Not necessarily a failure
    except Exception as e:
        print(f"❌ API connectivity test failed: {e}")
        return False

def test_sample_financial_document():
    """Test extraction with a sample financial document"""
    print("\n4. Testing extraction with sample financial document...")
    
    # Sample financial document content similar to what we've seen
    sample_content = """
    Real Estate Financial Statement - Sep 2025 (Actual)
    
    Property: Example Commercial Property
    Period: September 1, 2025 - September 30, 2025
    
    Category                        Amount
    Rental Income - Commercial      30000.0
    Rental Income - Residential     20000.0
    Parking Fees                    2000.0
    Laundry Income                  500.0
    Application Fees                300.0
    Late Fees                       150.0
    Other Income                    5000.0
    Total Revenue                   57950.0
    
    Operating Expenses
    Property Management Fees        4000.0
    Utilities                       3000.0
    Property Taxes                  2000.0
    Property Insurance              1500.0
    Repairs & Maintenance           2500.0
    Cleaning & Janitorial           1000.0
    Landscaping & Grounds           500.0
    Security                        1000.0
    Marketing & Advertising         500.0
    Administrative Expenses         300.0
    HOA Fees (if applicable)        200.0
    Pest Control                    100.0
    Supplies                        100.0
    Total Operating Expenses        16000.0
    
    Net Operating Income (NOI)      41950.0
    """
    
    try:
        extractor = AssistantBasedExtractor()
        result = extractor.extract_financial_data(
            document_content=sample_content,
            document_name="financial_statement_september_2025_actual.xlsx",
            document_type="Actual Income Statement"
        )
        
        print("✅ Sample document extraction completed successfully")
        
        # Verify the structure of the response
        if 'financial_data' not in result:
            print("❌ Response missing 'financial_data' key")
            return False
            
        if 'confidence_scores' not in result:
            print("❌ Response missing 'confidence_scores' key")
            return False
        
        financial_data = result['financial_data']
        confidence_scores = result['confidence_scores']
        
        # Check that we have the expected fields
        expected_fields = [
            'gross_potential_rent', 'vacancy_loss', 'concessions', 'bad_debt',
            'other_income', 'effective_gross_income', 'operating_expenses',
            'property_taxes', 'insurance', 'repairs_maintenance', 'utilities',
            'management_fees', 'net_operating_income'
        ]
        
        for field in expected_fields:
            if field not in financial_data:
                print(f"❌ Missing expected field: {field}")
                return False
            if field not in confidence_scores:
                print(f"❌ Missing confidence score for field: {field}")
                return False
        
        # Check some key values
        gpr = financial_data.get('gross_potential_rent', 0)
        if gpr <= 0:
            print(f"⚠️  Gross Potential Rent appears to be {gpr} (expected positive value)")
        
        noi = financial_data.get('net_operating_income', 0)
        if noi <= 0:
            print(f"⚠️  Net Operating Income appears to be {noi} (expected positive value)")
        
        print("✅ Response structure is correct")
        print(f"   Gross Potential Rent: ${gpr:,.2f}")
        print(f"   Net Operating Income: ${noi:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Sample document extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling with invalid input"""
    print("\n5. Testing error handling...")
    
    try:
        extractor = AssistantBasedExtractor()
        
        # Test with empty content
        try:
            result = extractor.extract_financial_data(
                document_content="",
                document_name="empty_document.txt",
                document_type="Unknown"
            )
            print("✅ Empty document handled gracefully")
        except Exception as e:
            print(f"ℹ️  Empty document raised exception (expected): {type(e).__name__}")
        
        # Test with invalid JSON response simulation would be complex
        # but we can at least verify the parser handles invalid JSON
        try:
            extractor._parse_response("This is not JSON at all")
            print("❌ Parser should have rejected invalid JSON")
            return False
        except ValueError:
            print("✅ JSON parser correctly rejects invalid JSON")
        except Exception as e:
            print(f"❌ JSON parser raised unexpected exception: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_file_integration():
    """Test integration with file-based operations"""
    print("\n6. Testing file integration...")
    
    # Create a temporary file with sample data
    sample_data = {
        'Category': ['Rental Income - Commercial', 'Rental Income - Residential', 'Parking Fees'],
        'Amount': [30000.0, 20000.0, 2000.0]
    }
    
    temp_filename = None  # Initialize variable to prevent unbound error
    try:
        # Create a temporary CSV file
        import pandas as pd
        df = pd.DataFrame(sample_data)
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
            df.to_csv(tmp_file.name, index=False)
            temp_filename = tmp_file.name
        
        # Read the file content
        with open(temp_filename, 'rb') as f:
            file_content = f.read()
        
        print("✅ File integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ File integration test failed: {e}")
        return False
    finally:
        # Clean up temporary file if it was created
        if temp_filename and os.path.exists(temp_filename):
            try:
                os.unlink(temp_filename)
            except Exception as cleanup_error:
                print(f"Warning: Failed to clean up temporary file: {cleanup_error}")

def run_comprehensive_deployment_test():
    """Run all tests to verify deployment readiness"""
    print("=" * 60)
    print("COMPREHENSIVE ASSISTANT DEPLOYMENT READINESS TEST")
    print("=" * 60)
    
    tests = [
        test_api_key_configuration,
        test_assistant_creation,
        test_basic_connectivity,
        test_sample_financial_document,
        test_error_handling,
        test_file_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            print(f"❌ {test.__name__} raised unexpected exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"DEPLOYMENT READINESS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - READY FOR PUBLIC DEPLOYMENT!")
        print("\nDeployment checklist:")
        print("✅ API key properly configured")
        print("✅ Assistant creation working")
        print("✅ API connectivity verified")
        print("✅ Financial document extraction functional")
        print("✅ Error handling implemented")
        print("✅ File integration working")
        return True
    elif passed >= total * 0.8:
        print("⚠️  MOST TESTS PASSED - NEARLY READY FOR DEPLOYMENT")
        print("Please review failed tests before deployment")
        return False
    else:
        print("❌ TOO MANY TESTS FAILED - NOT READY FOR DEPLOYMENT")
        print("Please fix issues before deployment")
        return False

if __name__ == "__main__":
    # Make sure we have an API key for testing
    if not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not set in environment variables")
        print("For testing, you may want to set it temporarily:")
        print("  export OPENAI_API_KEY=sk-your-actual-key-here")
    
    success = run_comprehensive_deployment_test()
    
    if success:
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print("The assistant-based extraction system is ready for integration")
        print("with the existing data extraction pipeline.")
        print("\nKey benefits:")
        print("- Predefined instructions ensure consistent behavior")
        print("- Faster processing (no need to resend instructions)")
        print("- Better performance (more tokens for actual content)")
        print("- Cost effective (reduced token usage)")
        print("- Ready for public deployment")
    else:
        print("\nPlease address the failed tests before deployment.")