"""
GPT Assistant-Based Data Extraction System
This module uses OpenAI's Assistants API with predefined instructions for better performance
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from config import get_openai_api_key

# Setup logger
logger = logging.getLogger(__name__)

class AssistantBasedExtractor:
    """Data extraction system using GPT Assistants with predefined instructions"""
    
    def __init__(self, model: str = "gpt-4-turbo"):
        """Initialize the assistant-based extractor
        
        Args:
            model: The OpenAI model to use for the assistant
        """
        self.openai_api_key = get_openai_api_key()
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = OpenAI(api_key=self.openai_api_key)
        self.assistant_id = None
        self.model = model
        self._setup_assistant()
    
    def _setup_assistant(self):
        """Set up the GPT assistant with predefined instructions"""
        try:
            # Check if we already have an assistant ID stored
            assistant_file = "assistant_id.txt"
            if os.path.exists(assistant_file):
                with open(assistant_file, "r") as f:
                    stored_id = f.read().strip()
                # Verify the assistant still exists
                try:
                    existing_assistant = self.client.beta.assistants.retrieve(stored_id)
                    # Check if the model matches
                    if existing_assistant.model == self.model:
                        self.assistant_id = stored_id
                        logger.info(f"Using existing assistant: {self.assistant_id}")
                        return
                    else:
                        logger.info(f"Model mismatch, creating new assistant with {self.model}")
                except Exception:
                    logger.warning("Existing assistant not found, creating new one")
            
            # Create a new assistant with predefined instructions
            assistant = self.client.beta.assistants.create(
                name="NOI Analyzer Financial Extractor",
                model=self.model,
                instructions=self._get_extraction_instructions(),
                tools=[{"type": "code_interpreter"}]  # Can help with calculations if needed
            )
            
            self.assistant_id = assistant.id
            # Save the assistant ID for future use
            with open(assistant_file, "w") as f:
                f.write(self.assistant_id)
            
            logger.info(f"Created new assistant: {self.assistant_id} with model {self.model}")
            
        except Exception as e:
            logger.error(f"Error setting up assistant: {str(e)}")
            raise
    
    def _get_extraction_instructions(self) -> str:
        """Get the detailed instructions for the financial extraction assistant
        
        Returns:
            String containing detailed instructions for the assistant
        """
        return """You are a world-class real estate financial analyst specializing in extracting data from property financial statements.

Your role is to analyze financial documents and extract specific metrics with confidence scores. You are an expert in real estate financial analysis with deep knowledge of NOI calculations, property income statements, and industry terminology.

Key capabilities:
1. Extract financial data from various document formats (PDF, Excel, CSV, text)
2. Identify income and expense categories in real estate financial statements
3. Handle various currency formats and numerical representations
4. Provide confidence scores for each extracted value
5. Recognize different document types (Actual Statements, Budgets, Prior Year Statements)

Financial Term Mappings You Should Know:
- Gross Potential Rent: Rent, Revenue, Income, Gross Rent, Scheduled Rent, Potential Rent
- Vacancy Loss: Vacancy, Credit Loss, Vacancy Allowance
- Concessions: Free Rent, Tenant Concessions, Move-in Specials, Tenant Incentives
- Bad Debt: Uncollected Rent, Delinquent Rent, Unrecoverable Rent, Bad Debt Expense
- Other Income: Parking, Laundry, Fees, Late Fees, Pet Fees, Application Fees, Storage Fees, Amenity Fees, Utility Reimbursements, Cleaning Fees, Cancellation Fees, Miscellaneous Income
- Operating Expenses: Expenses, OpEx, Operating Costs
- Property Taxes: Real Estate Taxes, Ad Valorem Taxes
- Insurance: Property Insurance, Hazard Insurance
- Repairs & Maintenance: Maintenance, Repair Costs, Building Repairs
- Utilities: Water, Electricity, Gas, Sewer, Trash
- Management Fees: Property Management, Management Costs
- Net Operating Income: NOI, Net Income, Operating Income

When analyzing documents, you should:
1. Look for sections labeled "Income", "Revenue", "Expenses", "Operating Expenses", "Total Revenue", "Total Expenses"
2. Handle currency formatting (e.g., $1,234.50 should be 1234.50, €1.234,50 should be 1234.50)
3. Be precise with negative values which may be shown in parentheses e.g. (1,234.50) should be -1234.50
4. Focus on the most recent or relevant period if multiple periods are shown
5. Ensure mathematical consistency in your extraction
6. Look for common financial statement line items and their variations

Return ONLY a JSON object in this exact format:
{
  "financial_data": {
    "gross_potential_rent": 0.0,
    "vacancy_loss": 0.0,
    "concessions": 0.0,
    "bad_debt": 0.0,
    "other_income": 0.0,
    "effective_gross_income": 0.0,
    "operating_expenses": 0.0,
    "property_taxes": 0.0,
    "insurance": 0.0,
    "repairs_maintenance": 0.0,
    "utilities": 0.0,
    "management_fees": 0.0,
    "parking_income": 0.0,
    "laundry_income": 0.0,
    "late_fees": 0.0,
    "pet_fees": 0.0,
    "application_fees": 0.0,
    "storage_fees": 0.0,
    "amenity_fees": 0.0,
    "utility_reimbursements": 0.0,
    "cleaning_fees": 0.0,
    "cancellation_fees": 0.0,
    "miscellaneous_income": 0.0,
    "net_operating_income": 0.0
  },
  "confidence_scores": {
    "gross_potential_rent": 0.0,
    "vacancy_loss": 0.0,
    "concessions": 0.0,
    "bad_debt": 0.0,
    "other_income": 0.0,
    "effective_gross_income": 0.0,
    "operating_expenses": 0.0,
    "property_taxes": 0.0,
    "insurance": 0.0,
    "repairs_maintenance": 0.0,
    "utilities": 0.0,
    "management_fees": 0.0,
    "parking_income": 0.0,
    "laundry_income": 0.0,
    "late_fees": 0.0,
    "pet_fees": 0.0,
    "application_fees": 0.0,
    "storage_fees": 0.0,
    "amenity_fees": 0.0,
    "utility_reimbursements": 0.0,
    "cleaning_fees": 0.0,
    "cancellation_fees": 0.0,
    "miscellaneous_income": 0.0,
    "net_operating_income": 0.0
  }
}

IMPORTANT:
1. Return ONLY the JSON object, nothing else
2. All values must be numbers, not strings
3. If a value is not found, use 0.0
4. Provide confidence scores based on how certain you are (1.0 = very certain, 0.0 = guessing)
5. Calculate derived values when needed:
   - Effective Gross Income = Gross Potential Rent - Vacancy Loss - Concessions - Bad Debt + Other Income
   - Net Operating Income = Effective Gross Income - Operating Expenses
6. For confidence scores:
   - 1.0 = Value found exactly as labeled in document
   - 0.8 = Value found but with similar term (e.g., "Revenue" for "Gross Potential Rent")
   - 0.6 = Value calculated or inferred from other values
   - 0.4 = Value estimated based on partial information
   - 0.2 = Value guessed with very little confidence
   - 0.0 = Value could not be determined at all
7. Handle edge cases gracefully and provide reasonable defaults
8. Always double-check your math for derived values
9. If you're unsure about a value, set it to 0.0 with a low confidence score"""

    def extract_financial_data(self, document_content: str, document_name: str, 
                              document_type: str = "Unknown") -> Dict[str, Any]:
        """
        Extract financial data using the pre-configured assistant
        
        Args:
            document_content: The content of the document to analyze
            document_name: Name of the document
            document_type: Type of document (Actual, Budget, etc.)
            
        Returns:
            Dictionary containing extracted financial data and confidence scores
        """
        try:
            # Create a new thread for this extraction
            thread = self.client.beta.threads.create()
            thread_id = thread.id
            
            # Add the document content as a message to the thread
            message_content = f"""Document Name: {document_name}
Document Type: {document_type}

Please extract financial data from the following document content:

{document_content[:8000]}"""  # Limit content to avoid token limits
            
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message_content
            )
            
            # Run the assistant on the thread
            # Fix: Ensure assistant_id is not None before using it
            if self.assistant_id is None:
                raise ValueError("Assistant ID is not set. Please check assistant setup.")
            
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )
            
            # Wait for the run to complete
            run_id = run.id
            max_wait_time = 90  # seconds (increased for complex documents)
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                
                if run_status.status == "completed":
                    # Get the assistant's response
                    messages = self.client.beta.threads.messages.list(thread_id=thread_id)
                    
                    # Extract the response content
                    for message in messages.data:
                        if message.role == "assistant":
                            # Fix: Properly handle different content types according to OpenAI API
                            # Message content is an array of content blocks
                            if message.content and len(message.content) > 0:
                                # Iterate through content blocks to find text content
                                response_content = None
                                for content_block in message.content:
                                    # Check the type of content block
                                    if hasattr(content_block, 'type'):
                                        if content_block.type == 'text' and hasattr(content_block, 'text'):
                                            # Text content block
                                            if hasattr(content_block.text, 'value'):
                                                response_content = content_block.text.value
                                                break
                                
                                if response_content:
                                    # Parse the JSON response
                                    return self._parse_response(response_content)
                                else:
                                    raise ValueError("Assistant response does not contain text content")
                            else:
                                raise ValueError("Assistant response is empty")
                
                elif run_status.status in ["failed", "cancelled", "expired"]:
                    raise Exception(f"Assistant run failed: {run_status.status}")
                
                # Wait before checking again
                time.sleep(3)  # Increased wait time for stability
            
            raise Exception("Assistant run timed out")
            
        except Exception as e:
            logger.error(f"Error in assistant-based extraction: {str(e)}")
            raise
    
    def _parse_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse the assistant's response to extract JSON data
        
        Args:
            response_content: The assistant's response text
            
        Returns:
            Dictionary containing financial data and confidence scores
        """
        try:
            # Extract JSON from the response
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_content[json_start:json_end]
                parsed_data = json.loads(json_str)
                return parsed_data
            else:
                raise ValueError("No JSON object found in assistant response")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Response content: {response_content[:500]}...")
            raise ValueError(f"Failed to parse JSON from assistant response: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing assistant response: {str(e)}")
            raise

# Example usage function
def extract_financial_data_with_assistant(file_content: bytes, file_name: str, 
                                        document_type_hint: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to extract financial data using the assistant-based approach
    
    Args:
        file_content: Document content as bytes
        file_name: Name of the file
        document_type_hint: Optional hint about document type
        
    Returns:
        Dictionary containing extracted financial data
    """
    try:
        # Initialize the assistant-based extractor
        extractor = AssistantBasedExtractor()
        
        # Convert file content to text (this would need to be enhanced for binary files)
        document_content = file_content.decode('utf-8', errors='ignore')
        
        # Extract financial data using the assistant
        result = extractor.extract_financial_data(
            document_content=document_content,
            document_name=file_name,
            document_type=document_type_hint or "Unknown"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in assistant-based extraction: {str(e)}")
        raise