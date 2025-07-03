# Credit System Setup Guide

## Quick Start

### 1. Start the API Server (Required!)

The credit system needs a backend API server to work. Start it with:

```bash
python start_api.py
```

Or manually:
```bash
python api_server.py
```

You should see:
```
🚀 Starting NOI Analyzer API server on 127.0.0.1:8000
📋 Health check will be available at: http://127.0.0.1:8000/health
💳 Credit endpoints will be available at: http://127.0.0.1:8000/pay-per-use/
```

### 2. Start the Streamlit App

In a separate terminal:
```bash
streamlit run app.py
```

### 3. How It Works

1. **Email Input**: Enter your email at the top of the page
2. **Free Credits**: New users get 3 free credits automatically  
3. **Credit Balance**: Shows in the sidebar after entering email
4. **Purchase More**: Click "🛒 Buy Credits" when you run out

## Troubleshooting

### "💳 Backend API Unavailable" 
- The API server isn't running
- Start it with: `python start_api.py`

### "💳 Credit System: Disabled"
- Check that `utils/credit_ui.py` can be imported
- Make sure all dependencies are installed: `pip install -r requirements.txt`

### Still getting HTML instead of JSON?
- Make sure `BACKEND_URL` points to the API server (default: `http://localhost:8000`)
- The API server must be running on a different port than Streamlit
- Streamlit usually runs on port 8501, API server on port 8000

## Environment Variables

- `BACKEND_URL`: API server URL (default: `http://localhost:8000`)
- `RESEND_API_KEY`: Your Resend API key for sending emails
- `STRIPE_SECRET_KEY`: Your Stripe secret key
- `STRIPE_WEBHOOK_SECRET`: Your Stripe webhook secret

## Architecture

```
Streamlit App (port 8501) 
    ↓ HTTP requests
FastAPI Server (port 8000)
    ↓ 
Database (SQLite)
``` 