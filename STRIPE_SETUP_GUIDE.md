# 🎯 Stripe Setup Guide for NOI Analyzer

## Overview
This guide walks you through setting up **real Stripe payments** for testing the credit purchase system.

## 📋 Prerequisites

1. **Stripe Account**: Create one at [stripe.com](https://stripe.com)
2. **Stripe CLI** (optional but recommended for webhook testing)

## 🔧 Step 1: Stripe Dashboard Setup

### 1.1 Create Products and Prices

Log into your [Stripe Dashboard](https://dashboard.stripe.com) and create these products:

#### **Starter Pack**
- **Product Name**: "NOI Analyzer - Starter Pack"
- **Description**: "5 credits for NOI analysis"
- **Price**: $25.00 USD
- **Billing**: One-time payment
- **Copy the Price ID** (starts with `price_...`)

#### **Professional Pack**
- **Product Name**: "NOI Analyzer - Professional Pack"  
- **Description**: "15 credits for NOI analysis"
- **Price**: $60.00 USD
- **Billing**: One-time payment
- **Copy the Price ID**

#### **Business Pack**
- **Product Name**: "NOI Analyzer - Business Pack"
- **Description**: "50 credits for NOI analysis"  
- **Price**: $150.00 USD
- **Billing**: One-time payment
- **Copy the Price ID**

### 1.2 Get API Keys

From the Stripe Dashboard → Developers → API Keys:

- **Publishable Key** (starts with `pk_test_...`)
- **Secret Key** (starts with `sk_test_...`)

## 🌐 Step 2: Environment Configuration

Create or update your `.env` file:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here

# Credit Package Price IDs (from Step 1.1)
STRIPE_STARTER_PRICE_ID=price_1234567890abcdef
STRIPE_PROFESSIONAL_PRICE_ID=price_0987654321fedcba
STRIPE_BUSINESS_PRICE_ID=price_abcdef1234567890

# Webhook Configuration
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Success/Cancel URLs
CREDIT_SUCCESS_URL=http://localhost:8501?success=true
CREDIT_CANCEL_URL=http://localhost:8501?cancelled=true

# Backend URL (for production)
BACKEND_URL=https://noianalyzer-1.onrender.com
```

## 🔄 Step 3: Update Production Server

### Option A: Update via Environment Variables

If you're using Render.com or similar:

1. Go to your service dashboard
2. Add the environment variables from Step 2
3. Redeploy the service

### Option B: Test Locally First

1. Set up the environment variables locally
2. Run the API server with real Stripe integration
3. Test the purchase flow

## 🧪 Step 4: Testing Process

### 4.1 Test with Stripe Test Cards

Use these test card numbers in Stripe checkout:

- **Successful Payment**: `4242 4242 4242 4242`
- **Declined Payment**: `4000 0000 0000 0002`  
- **3D Secure**: `4000 0000 0000 3220`

**For all test cards:**
- **Expiry**: Any future date (e.g., 12/25)
- **CVC**: Any 3 digits (e.g., 123)
- **ZIP**: Any 5 digits (e.g., 12345)

### 4.2 Complete Testing Flow

1. **Start the app** with updated environment variables
2. **Enter your email** in the NOI Analyzer
3. **Click "Buy Credits"**
4. **Choose a package** - you should now see a real Stripe checkout URL
5. **Complete the test payment** using the test card numbers above
6. **Verify credits are added** to your account

## 🔗 Step 5: Webhook Setup (Optional but Recommended)

For production, set up webhooks to handle successful payments:

1. **Stripe Dashboard** → Developers → Webhooks
2. **Add endpoint**: `https://your-domain.com/pay-per-use/stripe/webhook`
3. **Select events**: `checkout.session.completed`
4. **Copy the webhook secret** to your environment variables

## 🛠️ Step 6: Using the Update Script

I'll create a script to help you update the Stripe price IDs: 