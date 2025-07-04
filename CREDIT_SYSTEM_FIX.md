# Credit System Fix Guide

## Issues Fixed

### 1. HTML Display Problem
- **Problem**: Raw HTML was showing instead of rendered cards in the credit purchase interface
- **Solution**: Replaced complex HTML with Streamlit native components for better compatibility

### 2. Purchase API Error
- **Problem**: "Email and package required" error when clicking purchase buttons
- **Solution**: 
  - Fixed form data parsing in API server to handle both JSON and form-encoded data
  - Added better error handling and debugging
  - Improved backend URL auto-detection

## How to Start the Credit System

### Option 1: Auto-Start (Recommended)
```bash
python start_credit_api.py
```
This will automatically choose the best server option.

### Option 2: Ultra Minimal Server (Most Reliable)
```bash
python start_credit_api.py ultra
```
- Uses port 10000
- No external dependencies
- Most compatible

### Option 3: FastAPI Server (Full Features)
```bash
python start_credit_api.py minimal
```
- Uses port 8000
- Requires FastAPI and uvicorn
- Full feature set

## Testing the Fix

1. Start the API server using one of the methods above
2. Run the test script:
   ```bash
   python test_credit_api.py
   ```
3. Check that all endpoints are working

## Environment Configuration

Set the backend URL if using a custom server:
```bash
export BACKEND_URL=http://your-server:port
```

Or on Windows:
```cmd
set BACKEND_URL=http://your-server:port
```

## Troubleshooting

### If you see connection errors:
1. Make sure the API server is running
2. Check that no firewall is blocking the ports
3. Verify the correct port is being used (8000 or 10000)

### If the UI still shows raw HTML:
1. Update Streamlit to the latest version
2. Restart the Streamlit application
3. Clear browser cache

### If purchases still fail:
1. Check the browser console for JavaScript errors
2. Look at the API server logs for error messages
3. Run the test script to verify API functionality

## Files Modified

- `utils/credit_ui.py` - Fixed HTML display and added better error handling
- `ultra_minimal_api.py` - Fixed form data parsing and added logging
- `test_credit_api.py` - New test script for verification
- `start_credit_api.py` - New server startup script

## Next Steps

1. Start the API server
2. Test the credit purchase flow
3. Verify that the UI displays properly
4. Check that purchases redirect to checkout correctly 