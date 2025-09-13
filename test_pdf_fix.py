import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test the PDF generation fix
try:
    # Import the app module
    import app
    
    # Test if the WEASYPRINT_AVAILABLE flag is correctly set
    print(f"WEASYPRINT_AVAILABLE: {app.WEASYPRINT_AVAILABLE}")
    
    # Test the create_printable_html_report function
    if not app.WEASYPRINT_AVAILABLE:
        test_html = "<!DOCTYPE html><html><head><title>Test</title></head><body><h1>Test Report</h1><p>This is a test report.</p></body></html>"
        html_bytes = app.create_printable_html_report(test_html)
        print(f"HTML report generated: {len(html_bytes)} bytes")
        print("PDF generation fallback is working correctly!")
    else:
        print("WeasyPrint is available, PDF generation should work normally.")
        
    print("Test completed successfully!")
    
except Exception as e:
    print(f"Error during test: {e}")
    import traceback
    traceback.print_exc()