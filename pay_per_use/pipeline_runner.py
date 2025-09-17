"""
Pipeline runner module for NOI analysis.
This module provides the run_noi_pipeline function that processes financial documents
and generates a PDF report.
"""

import os
import tempfile
import logging
from typing import List

# Try to import the process_all_documents function
try:
    from ..noi_tool_batch_integration import process_all_documents
    HAS_NOI_TOOL = True
except ImportError:
    HAS_NOI_TOOL = False
    logging.warning("Could not import noi_tool_batch_integration. Using dummy implementation.")

def run_noi_pipeline(temp_dir: str) -> str:
    """
    Run the NOI analysis pipeline on documents in the specified directory.
    
    Args:
        temp_dir: Path to directory containing financial documents
        
    Returns:
        Path to generated PDF report
    """
    if HAS_NOI_TOOL:
        # In a real implementation, we would:
        # 1. Process all documents in the temp_dir
        # 2. Generate NOI calculations and insights
        # 3. Create a PDF report
        
        # For now, we'll create a simple PDF with basic information
        pdf_content = f"NOI Analysis Report\n\nDocuments processed from: {temp_dir}\n\n"
        pdf_content += "This is a placeholder report. In a full implementation, this would contain:\n"
        pdf_content += "- Financial data extraction\n- NOI calculations\n- Comparative analysis\n- AI-generated insights"
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(pdf_content.encode('utf-8'))
            return f.name
    else:
        # Fallback dummy implementation
        pdf_content = "Dummy PDF report content\n\nSystem is running in fallback mode."
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(pdf_content.encode('utf-8'))
            return f.name