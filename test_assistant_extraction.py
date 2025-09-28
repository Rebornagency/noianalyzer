"""
Test script for assistant-based data extraction
"""

import os
from assistant_based_extraction import AssistantBasedExtractor

def test_assistant_extraction():
    """Test the assistant-based extraction approach"""
    print("Testing assistant-based financial data extraction...")
    
    # Sample financial document content (similar to what we saw in logs)
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
        # Initialize the assistant-based extractor
        print("Initializing assistant-based extractor...")
        extractor = AssistantBasedExtractor()
        
        print(f"Using assistant ID: {extractor.assistant_id}")
        
        # Extract financial data
        print("Extracting financial data...")
        result = extractor.extract_financial_data(
            document_content=sample_content,
            document_name="financial_statement_september_2025_actual.xlsx",
            document_type="Actual Income Statement"
        )
        
        print("Extraction completed successfully!")
        print("\nExtracted financial data:")
        print("=" * 50)
        if 'financial_data' in result:
            financial_data = result['financial_data']
            confidence_scores = result.get('confidence_scores', {})
            
            # Show key metrics
            key_metrics = [
                'gross_potential_rent', 
                'effective_gross_income', 
                'operating_expenses', 
                'net_operating_income'
            ]
            
            for metric in key_metrics:
                value = financial_data.get(metric, 0.0)
                confidence = confidence_scores.get(metric, 0.0)
                print(f"  {metric}: ${value:,.2f} (confidence: {confidence:.2f})")
        else:
            print("Financial data not found in response")
        
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set the OpenAI API key (you would normally get this from environment variables)
    os.environ["OPENAI_API_KEY"] = "your-openai-api-key-here"  # Replace with actual key
    
    success = test_assistant_extraction()
    
    if success:
        print("\n🎉 Assistant-based extraction test completed successfully!")
        print("\nBenefits of this approach:")
        print("- Predefined instructions ensure consistent behavior")
        print("- Faster processing (no need to resend instructions)")
        print("- Better performance (more tokens for actual content)")
        print("- Cost effective (reduced token usage)")
    else:
        print("\n❌ Assistant-based extraction test failed!")