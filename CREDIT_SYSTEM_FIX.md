# Credit System Fix Guide

## Issues Fixed

### 1. HTML Display Problem ✅
- **Problem**: Raw HTML was showing instead of rendered cards in the credit purchase interface
- **Solution**: Replaced complex HTML with Streamlit native components for better compatibility

### 2. Purchase API Error ✅
- **Problem**: "Email and package required" error when clicking purchase buttons
- **Solution**: 
  - Fixed form data parsing in API server to handle both JSON and form-encoded data
  - Added better error handling and debugging
  - Improved backend URL auto-detection

### 3. Mock Checkout URL Issue ✅
- **Problem**: Checkout URLs were pointing to `mock-checkout.example.com` which doesn't work
- **Solution**: 
  - Smart detection of mock vs real checkout URLs
  - Automatic payment simulation for development/testing
  - Graceful fallback to production server

## How the Credit System Now Works

### 🔄 **Automatic Backend Detection**
The system now automatically tries backends in this order:
1. **Production Server**: `https://noianalyzer-1.onrender.com` (primary)
2. **Local FastAPI**: `http://localhost:8000` 
3. **Local Minimal**: `http://localhost:10000`

### 💳 **Smart Purchase Flow**

#### For Mock/Development URLs:
- Shows "Purchase Initiated" with package details
- Simulates payment processing (2-second delay)
- Automatically adds credits to account
- Updates credit balance in real-time
- Shows success confirmation

#### For Real Stripe URLs:
- Opens checkout in new tab/window
- Shows fallback link if redirect fails
- Handles real payment processing

## Testing the System

### ✅ **Quick Test**
1. Enter your email in the NOI Analyzer
2. Click "🛒 Buy Credits" in the sidebar or main header
3. Choose any package and click "Buy [Package Name]"
4. You should see either:
   - **Development Mode**: Automatic simulation and credit addition
   - **Production Mode**: Redirect to real Stripe checkout

### 🔧 **Troubleshooting**

#### If "Redirecting to checkout..." shows but nothing happens:
1. **Check your backend**: Look for `Backend connected successfully` in logs
2. **Try refreshing**: Sometimes the first connection takes a moment
3. **Check popup blockers**: Ensure your browser allows popups

#### If you see "Backend API Unavailable":
1. The system will show debug information
2. Try refreshing the page
3. Check that you're connected to the internet

#### If credits don't update after purchase:
1. Refresh the page manually
2. Check the sidebar for updated balance
3. Look for success messages in the interface

## Production vs Development

### 🌐 **Production Mode** (`https://noianalyzer-1.onrender.com`)
- Real Stripe integration
- Actual payment processing
- Credits added via webhooks

### 🛠️ **Development Mode** (Local servers)
- Simulated payments
- Instant credit addition
- Perfect for testing

## Environment Variables

```bash
# Optional: Force a specific backend
export BACKEND_URL="https://your-custom-backend.com"

# For production Stripe (not needed for development)
export STRIPE_SECRET_KEY="sk_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."
```

## Success Indicators

✅ **Working correctly when you see:**
- Credit balance in top-right header
- "Backend connected successfully" in logs
- Smooth purchase flow without errors
- Credits update after purchase

❌ **Needs attention when you see:**
- "Backend API Unavailable" messages
- "Failed to initiate purchase" errors
- Credits not updating after payment

---

**Latest Update**: Credit system now handles both development and production environments seamlessly with smart URL detection and automatic payment simulation for testing.

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