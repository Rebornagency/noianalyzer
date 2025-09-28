"""
Test script to demonstrate proper financial data extraction with actual data
"""

import pandas as pd
import json
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocessing_module import preprocess_file
from document_classifier import DocumentClassifier
from gpt_data_extractor import GPTDataExtractor
from config import get_openai_api_key

def create_sample_excel_file():
    """Create a sample Excel file with actual financial data"""
    data = {
        'Category': [
            'Property: Example Commercial Property',
            'Period: September 1, 2025 - September 30, 2025',
            'Category',
            'Rental Income - Commercial',
            'Rental Income - Residential',
            'Parking Fees',
            'Laundry Income',
            'Application Fees',
            'Late Fees',
            'Other Income',
            'Total Revenue',
            '',
            'Operating Expenses',
            'Property Management Fees',
            'Utilities',
            'Property Taxes',
            'Property Insurance',
            'Repairs & Maintenance',
            'Cleaning & Janitorial',
            'Landscaping & Grounds',
            'Security',
            'Marketing & Advertising',
            'Administrative Expenses',
            'HOA Fees (if applicable)',
            'Pest Control',
            'Supplies',
            'Total Operating Expenses',
            '',
            'Net Operating Income (NOI)',
            'Net Operating Income (NOI)'
        ],
        'Amount': [
            '',
            '',
            '',
            30000.0,
            20000.0,
            2000.0,
            500.0,
            300.0,
            150.0,
            5000.0,
            57950.0,
            '',
            '',
            4000.0,
            3000.0,
            2000.0,
            1500.0,
            2500.0,
            1000.0,
            500.0,
            1000.0,
            500.0,
            300.0,
            200.0,
            100.0,
            100.0,
            16000.0,
            '',
            41950.0,
            41950.0
        ]
    }
    
    df = pd.DataFrame(data)
    file_path = 'sample_financial_statement.xlsx'
    df.to_excel(file_path, index=False, sheet_name='Real Estate Financial Statement')
    return file_path

def test_financial_extraction():
    """Test the complete financial data extraction pipeline"""
    print("Creating sample financial document with actual data...")
    excel_file_path = create_sample_excel_file()
    
    try:
        print(f"Created sample Excel file: {excel_file_path}")
        
        # Step 1: Preprocess the file
        print("\n1. Preprocessing file...")
        preprocessed_data = preprocess_file(excel_file_path)
        print("Preprocessing completed successfully")
        print(f"File type: {preprocessed_data['metadata']['file_type']}")
        print(f"Content length: {len(preprocessed_data['content'].get('combined_text', ''))} characters")
        
        # Step 2: Classify the document
        print("\n2. Classifying document...")
        classifier = DocumentClassifier()
        classification_result = classifier.classify(preprocessed_data, "current_month_actuals")
        print(f"Document type: {classification_result['document_type']}")
        print(f"Period: {classification_result['period']}")
        print(f"Method: {classification_result['method']}")
        
        # Step 3: Extract financial data (only if OpenAI API key is available)
        openai_api_key = get_openai_api_key()
        if openai_api_key:
            print("\n3. Extracting financial data with GPT...")
            extractor = GPTDataExtractor(openai_api_key)
            extracted_data = extractor.extract(preprocessed_data, classification_result['document_type'])
            print("Financial data extraction completed")
            
            # Display key financial metrics
            print("\n4. Extracted Financial Data:")
            print("-" * 50)
            financial_keys = [
                'gross_potential_rent', 'vacancy_loss', 'other_income', 'effective_gross_income',
                'operating_expenses', 'property_taxes', 'insurance', 'repairs_maintenance',
                'utilities', 'management_fees', 'parking_income', 'laundry_income',
                'net_operating_income'
            ]
            
            for key in financial_keys:
                value = extracted_data.get('financial_data', {}).get(key, 0.0)
                confidence = extracted_data.get('confidence_scores', {}).get(key, 0.0)
                print(f"{key:25}: ${value:>12,.2f} (confidence: {confidence:.2f})")
        else:
            print("\n3. Skipping GPT extraction (OpenAI API key not configured)")
            print("To test full extraction, set the OPENAI_API_KEY environment variable")
            
        print("\nTest completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        if os.path.exists(excel_file_path):
            os.unlink(excel_file_path)
            print(f"\nCleaned up temporary file: {excel_file_path}")

if __name__ == "__main__":
    test_financial_extraction()