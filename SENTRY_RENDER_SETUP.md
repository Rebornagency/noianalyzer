# 📊 Sentry Setup for Render Deployment

## Why Sentry for Production?

Sentry will automatically alert you when:
- Users encounter errors
- Payments fail
- API calls timeout
- Critical bugs occur

## 🚀 Quick Sentry Setup (5 minutes)

### Step 1: Create Sentry Account

1. **Go to [sentry.io](https://sentry.io)**
2. **Sign up with Google/GitHub** (free tier available)
3. **Choose "Python" platform**
4. **Name your project:** "NOI Analyzer"

### Step 2: Get Your DSN

After creating the project, Sentry will show you a DSN that looks like:
```
https://abc123def456@o789012.ingest.sentry.io/345678
```

**Copy this DSN** - you'll need it in the next step.

### Step 3: Add to Render Environment Variables

1. **Go to your Render dashboard**
2. **Select your Streamlit service** (the main app)
3. **Go to Environment tab**
4. **Add these environment variables:**

```env
SENTRY_DSN=https://your-actual-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.01
```

### Step 4: Add to API Service Too

1. **Go to your API service** in Render
2. **Add the same Sentry environment variables**
3. **This will track errors in both frontend and backend**

### Step 5: Test It Works

After redeploying, you should see in your logs:
```
INFO - Sentry error tracking initialized successfully
```

## 🧪 Test Sentry Integration

### Option 1: Add Test Button (Temporary)

Add this to your Streamlit app temporarily:

```python
# Add to app.py temporarily for testing
if st.button("🧪 Test Sentry (Remove After Testing)"):
    raise Exception("This is a test error for Sentry!")
```

Click the button and you should see the error in your Sentry dashboard within seconds.

### Option 2: API Test

Test API error tracking:
```bash
curl "https://your-api-url.onrender.com/raise-error"
```

## 📱 Set Up Alerts

### Email Alerts (Recommended)

1. **Go to Sentry dashboard** → **Alerts**
2. **Create Alert Rule:**
   - **Conditions:** "An event is seen"
   - **Filters:** "Level equals Error or Fatal"
   - **Actions:** "Send email to your-email@domain.com"

### Slack Alerts (Optional)

1. **Install Sentry Slack app**
2. **Connect to your workspace**
3. **Choose channel for alerts**

## 🔍 What Sentry Tracks Automatically

### In Your Streamlit App:
- ✅ File upload errors
- ✅ OpenAI API failures
- ✅ Credit system errors
- ✅ Document processing failures
- ✅ Database connection issues

### In Your API Service:
- ✅ Payment processing errors
- ✅ Stripe webhook failures
- ✅ Database errors
- ✅ Authentication failures

## 📊 Understanding Sentry Dashboard

### Key Sections:
- **Issues:** All errors grouped by type
- **Performance:** Slow operations
- **Releases:** Track deployments
- **User Feedback:** User-reported issues

### Important Metrics:
- **Error Rate:** Should be < 1%
- **Response Time:** Should be < 3 seconds
- **Affected Users:** Number of users hitting errors

## 🚨 Production Alert Thresholds

### Critical Alerts (Immediate Action):
- Payment processing failures
- Database connection errors
- High error rates (> 5%)

### Warning Alerts (Review Daily):
- Slow API responses (> 5 seconds)
- Credit system issues
- File processing errors

## 🔧 Sentry Best Practices

### ✅ DO:
- Set up email alerts for critical errors
- Review Sentry dashboard weekly
- Add context to errors with breadcrumbs
- Use Sentry releases to track deployments

### ❌ DON'T:
- Ignore error alerts
- Set too many noisy alerts
- Send sensitive data to Sentry (it's filtered automatically)
- Rely only on Sentry for monitoring

## 📈 Monitoring Your Business

### Weekly Sentry Review:
1. **Check error trends** - increasing or decreasing?
2. **Review new error types** - any new bugs introduced?
3. **Monitor user impact** - how many users affected?
4. **Performance trends** - is the app getting slower?

### Monthly Review:
1. **Update alert rules** based on what's important
2. **Review error resolution time**
3. **Check if errors correlate with usage spikes**

## 🆘 Common Issues & Solutions

### "Sentry not initializing"
- Check DSN is correct in environment variables
- Ensure Sentry package is installed (`pip install sentry-sdk`)
- Check logs for initialization errors

### "No errors showing up"
- Trigger a test error to verify connection
- Check SENTRY_ENVIRONMENT is set correctly
- Verify error sampling rate isn't too low

### "Too many alerts"
- Increase error threshold (from 1 to 5 errors)
- Filter out known issues that aren't critical
- Set up alert rules for specific error types only

---

**Bottom Line:** Once set up, Sentry runs automatically and will email you if anything breaks. It's like having a 24/7 system administrator watching your app! 