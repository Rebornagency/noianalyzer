import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Test the PDF validation function
    from api_server import validate_pdf_file
    print("SUCCESS: Imported validate_pdf_file function")
    
    # Test with empty content (should fail)
    result = validate_pdf_file(b"")
    print(f"Empty content validation result: {result} (should be False)")
    
    # Test with invalid PDF magic bytes (should fail)
    result = validate_pdf_file(b"NOT A PDF FILE")
    print(f"Invalid magic bytes validation result: {result} (should be False)")
    
    # Test with valid PDF magic bytes but invalid content (should fail)
    result = validate_pdf_file(b"%PDF-1.4\nNOT A VALID PDF")
    print(f"Valid magic bytes but invalid content validation result: {result} (should be False)")
    
    print("SUCCESS: All PDF validation tests completed")
    
except Exception as e:
    print(f"ERROR: Failed to test PDF validation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)