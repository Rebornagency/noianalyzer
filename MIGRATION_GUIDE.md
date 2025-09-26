# Migration Guide: World-Class Data Extraction System

This guide explains how to migrate from the existing data extraction system to the new world-class extraction system.

## Key Improvements

The new world-class extraction system provides several significant improvements over the previous implementation:

1. **Enhanced Preprocessing**: Better handling of all document types with improved structure detection
2. **Confidence Scoring**: Each extracted value now has a confidence score (0.0 to 1.0)
3. **Audit Trail**: Complete logging of all processing steps for transparency
4. **Robust Error Handling**: Improved fallback mechanisms and error recovery
5. **GPT-4 Integration**: Uses the more capable GPT-4 model for better accuracy
6. **Structured Output**: Consistent JSON format with all required financial metrics
7. **Backward Compatibility**: Maintains compatibility with existing code through wrapper functions

## Migration Path

### Option 1: Direct Replacement (Recommended)

Replace imports of the old extraction functions with the new world-class extraction:

**Before:**
```python
from ai_extraction import extract_noi_data

result = extract_noi_data(file, document_type_hint)
```

**After:**
```python
from world_class_extraction import WorldClassExtractor

extractor = WorldClassExtractor()
extraction_result = extractor.extract_data(file_content, file_name, document_type_hint)

# Access the data
result = extraction_result.data

# Access additional information
confidence = extraction_result.confidence
processing_time = extraction_result.processing_time
audit_trail = extraction_result.audit_trail
```

### Option 2: Backward Compatible Wrapper

Use the backward compatible function that maintains the same interface:

```python
# This function has the same signature as the old extract_noi_data
from world_class_extraction import extract_financial_data

result = extract_financial_data(file_content, file_name, document_type_hint)
```

## New Features and Capabilities

### Confidence Scoring

Each extracted value now has a confidence score:

```python
extractor = WorldClassExtractor()
result = extractor.extract_data(file_content, file_name, document_type_hint)

# Access confidence scores
gpr_confidence = result.confidence_scores.get("gross_potential_rent", 0.0)
noi_confidence = result.confidence_scores.get("net_operating_income", 0.0)

# Overall confidence level
overall_confidence = result.confidence  # HIGH, MEDIUM, LOW, or UNCERTAIN
```

### Audit Trail

Complete logging of all processing steps:

```python
# Access the audit trail
for step in result.audit_trail:
    print(f"Processing step: {step}")

# Example audit trail:
# - Starting extraction for financial_statement.xlsx
# - Preprocessing document
# - Preprocessing completed. Content length: 12345
# - Determining document type
# - Document type determined: Actual Income Statement
# - Extracting structured text
# - Structured text extracted. Length: 2345
# - Extracting financial data with GPT-4
# - GPT-4 extraction completed
# - Validating and enriching extracted data
# - Data validation and enrichment completed
# - Overall confidence calculated: high
```

### Enhanced Error Handling

Better error recovery and fallback mechanisms:

```python
extractor = WorldClassExtractor()
result = extractor.extract_data(file_content, file_name, document_type_hint)

# Check if extraction was successful
if result.confidence != "uncertain":
    # Process the data normally
    noi = result.data["net_operating_income"]
else:
    # Handle low-confidence extraction
    print("Low confidence in extraction results")
    print("Audit trail:", result.audit_trail)
```

## Required Configuration

The new system requires the OpenAI API key to be configured:

1. Ensure `OPENAI_API_KEY` is set in your environment variables or config
2. The system will automatically use GPT-4 for better accuracy

## Performance Considerations

- The new system uses GPT-4, which may have higher latency than GPT-3.5
- Processing time is tracked and available in `result.processing_time`
- For high-volume processing, consider implementing rate limiting

## Testing

The migration includes comprehensive test files:

1. `test_world_class_extraction.py` - Tests the new extraction system
2. `integration_test.py` - Verifies compatibility with existing code

Run these tests to ensure the migration was successful:

```bash
python test_world_class_extraction.py
python integration_test.py
```

## Rollback Plan

If issues are encountered, you can rollback to the previous system by:

1. Reverting imports to use `ai_extraction` module
2. Removing the `world_class_extraction.py` file
3. Ensuring all dependencies are properly configured

## Support

For any issues during migration, please refer to:

- The detailed documentation in `world_class_extraction.py`
- The test files for usage examples
- The audit trail feature for debugging extraction issues