# Sentry Integration Setup Guide for NOI Analyzer

This guide will walk you through setting up Sentry error tracking for your NOI Analyzer application. Sentry will help you monitor errors, track performance, and debug issues in production.

## 📋 Table of Contents

1. [Create Sentry Account and Project](#1-create-sentry-account-and-project)
2. [Install Dependencies](#2-install-dependencies)
3. [Set Up Environment Variables](#3-set-up-environment-variables)
4. [Test the Integration](#4-test-the-integration)
5. [Understanding the Dashboard](#5-understanding-the-dashboard)
6. [Advanced Configuration](#6-advanced-configuration)
7. [Best Practices](#7-best-practices)

---

## 1. Create Sentry Account and Project

### Step 1.1: Sign Up for Sentry
1. Go to [https://sentry.io/signup/](https://sentry.io/signup/)
2. Create a free account (starts with 14-day Business trial, then free tier)
3. Choose **United States** for data storage location (or EU if preferred)

### Step 1.2: Create a Python Project
1. Once logged in, click **"Create Project"**
2. Select **"Python"** as your platform
3. Set alert frequency to **"Alert me on high priority issues"**
4. Name your project: **"NOI Analyzer"**
5. Assign to your default team
6. Click **"Create Project"**

### Step 1.3: Copy Your DSN
- **IMPORTANT**: Copy the DSN key shown on the setup page
- It looks like: `https://abc123def456@o789012.ingest.sentry.io/345678`
- You'll need this in the next step

---

## 2. Install Dependencies

The Sentry SDK has already been added to your `requirements.txt` file. To install it:

### Option A: Using pip
```bash
pip install -r requirements.txt
```

### Option B: Install Sentry directly
```bash
pip install "sentry-sdk[streamlit]==2.29.1"
```

---

## 3. Set Up Environment Variables

### Step 3.1: Create a .env file
Create a file named `.env` in your project root directory (same folder as `app.py`):

```bash
# NOI Analyzer Environment Variables

# OpenAI API Configuration (if you haven't set this already)
OPENAI_API_KEY=your_openai_api_key_here

# Sentry Error Tracking Configuration
SENTRY_DSN=https://your-key@o123456.ingest.sentry.io/789012
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=0.1

# Optional: Set a custom release version
# SENTRY_RELEASE=noi-analyzer@1.0.0
```

### Step 3.2: Replace the placeholder values
- Replace `your_openai_api_key_here` with your actual OpenAI API key
- Replace `https://your-key@o123456.ingest.sentry.io/789012` with the DSN you copied from Sentry

### Step 3.3: Environment Configuration
- **Development**: Use `SENTRY_ENVIRONMENT=development` while testing
- **Production**: Change to `SENTRY_ENVIRONMENT=production` when deploying
- **Traces Sample Rate**: 
  - `0.1` = Track 10% of transactions (good for development)
  - `0.01` = Track 1% of transactions (recommended for production)

---

## 4. Test the Integration

### Step 4.1: Run Your Application
```bash
streamlit run app.py
```

### Step 4.2: Check the Console
You should see this message in your terminal:
```
INFO - Sentry error tracking initialized successfully
```

If you see this warning instead:
```
WARNING - Sentry error tracking not initialized - check SENTRY_DSN environment variable
```
Double-check your `.env` file and make sure the `SENTRY_DSN` is correct.

### Step 4.3: Test Error Tracking
To test that Sentry is working, you can temporarily add this code to your app and trigger it:

```python
# Add this temporarily for testing
if st.button("Test Sentry (Remove After Testing)"):
    raise Exception("This is a test error for Sentry!")
```

When you click the button, you should see the error appear in your Sentry dashboard within a few seconds.

---

## 5. Understanding the Dashboard

### Step 5.1: Access Your Dashboard
1. Go to [https://sentry.io](https://sentry.io)
2. Log in to your account
3. Select your "NOI Analyzer" project

### Step 5.2: Key Sections
- **Issues**: Shows all errors and exceptions
- **Performance**: Shows slow operations and transactions
- **Releases**: Track deployments and their impact
- **Alerts**: Configure when to be notified

### Step 5.3: What Gets Tracked Automatically
Your NOI Analyzer now tracks:
- ✅ All unhandled exceptions
- ✅ File upload events
- ✅ Document processing operations
- ✅ Button clicks and user actions
- ✅ Performance of key operations
- ✅ User session information
- ✅ Application startup and errors

---

## 6. Advanced Configuration

### Step 6.1: Production Settings
For production deployment, update your `.env` file:

```bash
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.01  # Lower sampling for production
SENTRY_RELEASE=noi-analyzer@v1.0.0  # Set your app version
```

### Step 6.2: Custom Alerts
1. In Sentry dashboard, go to **Alerts** → **Create Alert**
2. Set up alerts for:
   - High error rates
   - Performance issues
   - New error types

### Step 6.3: Release Tracking
To track releases and associate errors with specific deployments:

```bash
# Set in your deployment environment
SENTRY_RELEASE=noi-analyzer@$(date +%Y.%m.%d)
```

---

## 7. Best Practices

### Step 7.1: Privacy and Security
- ✅ Sensitive data is automatically filtered out
- ✅ Financial data is not sent to Sentry
- ✅ API keys are filtered from error reports
- ✅ Personal information is excluded

### Step 7.2: Error Management
- **Resolve Issues**: Mark issues as resolved in Sentry when fixed
- **Set Ownership**: Assign issues to team members
- **Add Context**: Use the breadcrumbs to understand user actions

### Step 7.3: Performance Monitoring
- Monitor document processing times
- Track slow API calls
- Identify bottlenecks in data analysis

---

## 🎯 What You'll Get

With Sentry integrated, you now have:

### Error Tracking
- **Real-time error alerts** via email
- **Detailed stack traces** with local variables
- **User context** showing what files were being processed
- **Breadcrumbs** showing the sequence of actions leading to errors

### Performance Monitoring
- **Slow operation detection** for document processing
- **Performance trends** over time
- **Transaction tracking** for key user flows

### Production Insights
- **Error rates** and trends
- **User session information** 
- **Release impact** tracking
- **Custom metrics** for your specific use cases

---

## 🚨 Troubleshooting

### Problem: "Sentry not initialized" message
**Solution**: Check that your `.env` file is in the project root and contains the correct `SENTRY_DSN`

### Problem: No errors appear in Sentry
**Solution**: 
1. Check your internet connection
2. Verify the DSN is correct
3. Try the test error button mentioned in Step 4.3

### Problem: Too many alerts
**Solution**: 
1. Increase `SENTRY_TRACES_SAMPLE_RATE` 
2. Set up alert rules to filter noise
3. Use issue grouping in Sentry dashboard

---

## 📞 Support

- **Sentry Documentation**: [https://docs.sentry.io/platforms/python/](https://docs.sentry.io/platforms/python/)
- **Sentry Discord**: [https://discord.gg/sentry](https://discord.gg/sentry)
- **Configuration File**: Check `sentry_config.py` for all available options

---

## 🎉 You're All Set!

Your NOI Analyzer now has enterprise-grade error tracking! You'll be notified of any issues and can debug them faster with detailed context about what users were doing when errors occurred.

Remember to:
- Monitor your Sentry dashboard regularly
- Resolve issues as you fix them
- Adjust sampling rates based on your usage
- Set up custom alerts for critical errors 