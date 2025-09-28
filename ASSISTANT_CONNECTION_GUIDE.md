# Assistant Connection Guide

## How the Assistant Connects to Your API Key

The assistant-based extraction system automatically integrates with your existing API key configuration. Here's exactly how it works:

##  Automatic Integration

### 1. **Uses Your Existing Configuration**
The assistant-based system uses the same configuration system as your current tool:

```python
# In assistant_based_extraction.py
from config import get_openai_api_key  # Same config you're already using

class AssistantBasedExtractor:
    def __init__(self):
        self.openai_api_key = get_openai_api_key()  # Gets your existing key
        self.client = OpenAI(api_key=self.openai_api_key)  # Uses your key
```

### 2. **Same API Key Sources**
Your API key can come from any of these sources (in order of priority):
1. **Environment Variable**: `OPENAI_API_KEY` in your `.env` file
2. **Session State**: Set via the application UI
3. **Fallback**: Returns empty string if not found

## 🔧 Setting Up Your API Key

### Option 1: Update Your .env File (Recommended)
Edit your [.env](file:///c:/Users/edgar/Documents/GitHub/noianalyzer/noianalyzer/.env) file and replace the placeholder:

```env
# Before (placeholder):
OPENAI_API_KEY=REPLACE_WITH_REAL_OPENAI_API_KEY

# After (with your real key):
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
```

### Option 2: Set Environment Variable
```bash
# Linux/Mac:
export OPENAI_API_KEY=sk-proj-your-actual-api-key-here

# Windows:
set OPENAI_API_KEY=sk-proj-your-actual-api-key-here
```

### Option 3: Through Application UI
If your application has a settings page, you can set it there (this uses session state).

## ✅ Verification

### Test Your Setup
Run the verification script to confirm everything is connected:

```bash
python verify_api_key.py
```

Expected output:
```
Verifying OpenAI API key configuration...
Environment variable OPENAI_API_KEY: SET
  Key preview: sk-proj...XXXX
Config system API key: SET
  Key preview: sk-proj...XXXX

✅ API key is properly configured!
You're ready to use assistant-based extraction.
```

## 🚀 Using the Assistant

Once your API key is configured, the assistant will work automatically:

```python
from assistant_based_extraction import AssistantBasedExtractor

# Initialize (automatically uses your API key)
extractor = AssistantBasedExtractor()

# Extract data (no additional configuration needed)
result = extractor.extract_financial_data(document_content, document_name)
```

## 📁 Files That Handle the Connection

1. **[config.py](file:///c:/Users/edgar/Documents/GitHub/noianalyzer/noianalyzer/config.py)** - Your existing configuration system
2. **[assistant_based_extraction.py](file:///c:/Users/edgar/Documents/GitHub/noianalyzer/noianalyzer/assistant_based_extraction.py)** - Automatically uses [get_openai_api_key()](file:///c:/Users/edgar/Documents/GitHub/noianalyzer/noianalyzer/config.py#L129-L152)
3. **[constants.py](file:///c:/Users/edgar/Documents/GitHub/noianalyzer/noianalyzer/constants.py)** - Defines `ENV_VARS["OPENAI_API_KEY"] = "OPENAI_API_KEY"`

## 🔒 Security Notes

- Your API key is handled the same way as in the current system
- Keys are not hardcoded in the assistant code
- The same security practices apply (environment variables, etc.)
- Assistant ID is saved locally but contains no sensitive information

## 🎯 Summary

You don't need to do anything special to connect the assistant to your API key. It automatically uses the same configuration system as your existing tool. Just make sure your `OPENAI_API_KEY` is properly set in your [.env](file:///c:/Users/edgar/Documents/GitHub/noianalyzer/noianalyzer/.env) file or environment variables, and the assistant will work seamlessly with your existing setup.