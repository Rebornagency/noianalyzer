# NOI Analyzer Integration Guide

## Overview

This guide explains how to integrate and use the assistant-based extraction system in the NOI Analyzer application.

## Integration Options

### Option 1: Enhanced Extraction System (Recommended)

Use the enhanced extraction system which provides both traditional GPT-4 extraction and assistant-based extraction:

```python
from enhanced_world_class_extraction import extract_financial_data

# Traditional GPT-4 extraction (default)
result = extract_financial_data(
    file_content=file_bytes,
    file_name="document.pdf",
    document_type_hint="Actual Income Statement"
)

# Assistant-based extraction (enhanced)
result = extract_financial_data(
    file_content=file_bytes,
    file_name="document.pdf",
    document_type_hint="Actual Income Statement",
    use_assistant_extraction=True  # Enable assistant-based extraction
)
```

### Option 2: Direct Assistant Usage

Use the assistant-based extractor directly:

```python
from assistant_based_extraction import extract_financial_data_with_assistant

result = extract_financial_data_with_assistant(
    file_content=file_bytes,
    file_name="document.pdf",
    document_type_hint="Actual Income Statement"
)
```

### Option 3: Class-Based Usage

Use the EnhancedWorldClassExtractor class directly:

```python
from enhanced_world_class_extraction import EnhancedWorldClassExtractor

# For traditional GPT-4 extraction
extractor = EnhancedWorldClassExtractor(use_assistant_extraction=False)
result = extractor.extract_data(file_bytes, "document.pdf", "Actual Income Statement")

# For assistant-based extraction
extractor = EnhancedWorldClassExtractor(use_assistant_extraction=True)
result = extractor.extract_data(file_bytes, "document.pdf", "Actual Income Statement")
```

## Configuration

### Environment Variables

The system uses the same configuration as the rest of the application:

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=sk-your-actual-api-key-here
```

### First Run Behavior

On first run with assistant-based extraction:
1. The system automatically creates a new assistant
2. Assistant ID is saved to `assistant_id.txt` for future use
3. Uses `gpt-4-turbo` model by default (configurable)

### Subsequent Runs

On subsequent runs:
1. Reuses existing assistant for better performance
2. Automatically verifies assistant exists and has correct model
3. Creates new assistant if model mismatch is detected

## Error Handling

The system includes comprehensive error handling:

```python
try:
    result = extract_financial_data(
        file_content=file_bytes,
        file_name="document.pdf",
        use_assistant_extraction=True
    )
    
    # Check extraction method used
    print(f"Extraction method: {result.extraction_method}")
    
    # Access financial data
    financial_data = result.data
    confidence_scores = result.confidence_scores
    
    # Check overall confidence
    print(f"Confidence level: {result.confidence.value}")
    
except Exception as e:
    print(f"Extraction failed: {e}")
```

## Response Format

The extraction result includes:

```python
{
    "data": {
        "gross_potential_rent": 100000.0,
        "vacancy_loss": 5000.0,
        "other_income": 10000.0,
        "effective_gross_income": 105000.0,
        "operating_expenses": 40000.0,
        "net_operating_income": 65000.0,
        # ... other financial metrics
    },
    "confidence_scores": {
        "gross_potential_rent": 0.9,
        "vacancy_loss": 0.8,
        "other_income": 0.7,
        # ... confidence scores for each metric
    },
    "confidence": "high",  # Overall confidence level
    "audit_trail": [...],  # Processing steps
    "processing_time": 15.2,  # Seconds
    "document_type": "Actual Income Statement",
    "extraction_method": "assistant-based-extraction"
}
```

## Best Practices

### 1. Choose the Right Method

- Use assistant-based extraction for better performance and cost efficiency
- Use traditional GPT-4 extraction when assistant is not available
- Consider document complexity when choosing method

### 2. Handle Errors Gracefully

```python
from enhanced_world_class_extraction import extract_financial_data

try:
    result = extract_financial_data(
        file_content=file_bytes,
        file_name="document.pdf",
        use_assistant_extraction=True
    )
except Exception as e:
    # Fallback to traditional extraction
    result = extract_financial_data(
        file_content=file_bytes,
        file_name="document.pdf",
        use_assistant_extraction=False
    )
```

### 3. Check Confidence Levels

```python
if result.confidence.value == "high":
    # Use the data directly
    pass
elif result.confidence.value == "medium":
    # Review the data before using
    pass
else:
    # Require manual review
    pass
```

## Testing

To verify the integration:

```bash
# Test the enhanced extraction system
python test_enhanced_extraction.py

# Test assistant deployment readiness
python test_assistant_deployment.py
```

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure `OPENAI_API_KEY` is set in environment variables
   - Check that the key is valid and has proper permissions

2. **Assistant Creation Failed**
   - Check API key permissions
   - Verify network connectivity
   - Check OpenAI service status

3. **Extraction Quality Issues**
   - Review document quality and format
   - Check if document contains actual financial data
   - Consider using traditional GPT-4 extraction for complex documents

### Getting Help

If you encounter issues:
1. Check the logs for detailed error messages
2. Verify environment configuration
3. Test with sample documents
4. Contact support with detailed error information