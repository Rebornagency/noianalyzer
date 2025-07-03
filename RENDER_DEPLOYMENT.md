# Deploy NOI Analyzer API to Render

## Why Deploy to Render?
- ✅ No need to install Python locally
- ✅ Works 24/7 even when your computer is off  
- ✅ Professional, reliable hosting
- ✅ Free tier available

## Step-by-Step Deployment

### 1. Push Your Code to GitHub
```bash
git add .
git commit -m "Add API server and credit system"
git push origin main
```

### 2. Deploy to Render

1. **Go to**: https://render.com
2. **Sign up** with your GitHub account
3. **Click "New +"** → **"Web Service"**
4. **Connect** your `noianalyzer` repository
5. **Configure:**
   - **Name**: `noi-analyzer-api`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python api_server.py`
   - **Plan**: Free (or Starter for $7/month)

### 3. Add Environment Variables

In the Render dashboard, add these environment variables:

**Required:**
- `PORT` = `8000`
- `HOST` = `0.0.0.0`

**For Stripe (when ready):**
- `STRIPE_SECRET_KEY` = `your_stripe_secret_key`
- `STRIPE_WEBHOOK_SECRET` = `your_webhook_secret`

**For Email (when ready):**
- `RESEND_API_KEY` = `your_resend_api_key`

### 4. Get Your API URL

After deployment, Render gives you a URL like:
```
https://noi-analyzer-api.onrender.com
```

### 5. Update Your Local App

Set your local Streamlit app to use the deployed API:

**Windows PowerShell:**
```powershell
$env:BACKEND_URL = "https://noi-analyzer-api.onrender.com"
streamlit run app.py
```

**Mac/Linux:**
```bash
export BACKEND_URL="https://noi-analyzer-api.onrender.com"
streamlit run app.py
```

## 🎯 Final Architecture

```
Your Computer:
- Streamlit App (port 8501) 
    ↓ HTTP requests over internet
Render Cloud:
- FastAPI Server (your-app.onrender.com)
    ↓ 
- Database (SQLite on Render)
```

## ✅ Testing

1. **Test API**: Visit `https://your-app.onrender.com/health`
2. **Test Credits**: Visit `https://your-app.onrender.com/pay-per-use/packages`
3. **Run Streamlit**: `streamlit run app.py`
4. **Enter email** and check if credit balance appears

## 💡 Pro Tips

- **Free Tier**: Render free tier sleeps after 15 minutes of inactivity
- **Paid Tier**: $7/month keeps it always running
- **Logs**: Check Render dashboard for error logs
- **Updates**: Push to GitHub → Render auto-deploys 