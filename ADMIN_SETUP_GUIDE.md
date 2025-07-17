# 🔐 Admin API Key Setup Guide

## What is the Admin API Key?

The Admin API Key protects sensitive admin endpoints that let you:
- View suspicious IP addresses with multiple free trial attempts
- Block abusive IP addresses
- Monitor system usage
- Manage user accounts

## 🔧 Setting Up Your Admin API Key

### Step 1: Generate a Strong Password

Use a password manager or generate a secure key:

```bash
# Example strong admin keys (don't use these exact ones):
NOI_ADMIN_2024_$ecure_K3y_f0r_Pr0duct10n
AdminKey_NOI_2024_SuperSecure123!@#
```

### Step 2: Set in Render Environment Variables

1. **Go to your Render dashboard**
2. **Select your API service**
3. **Go to Environment tab**
4. **Add environment variable:**
   - **Key:** `ADMIN_API_KEY`
   - **Value:** `your-strong-admin-key-here`

### Step 3: Test Admin Access

Once deployed, test your admin endpoints:

```bash
# View suspicious IPs (3+ trial attempts)
curl "https://your-api-url.onrender.com/pay-per-use/admin/suspicious-ips?min_trials=3&admin_key=your-admin-key"

# Block an abusive IP
curl -X POST "https://your-api-url.onrender.com/pay-per-use/admin/block-ip" \
  -F "ip_address=192.168.1.100" \
  -F "reason=Multiple fake accounts detected" \
  -F "admin_key=your-admin-key"
```

## 🛡️ Admin Monitoring Workflow

### Daily Check (5 minutes)
1. **Check suspicious IPs:**
   ```
   GET /pay-per-use/admin/suspicious-ips?min_trials=3&admin_key=YOUR_KEY
   ```

2. **Review results** - look for:
   - IPs with 5+ trial attempts
   - Similar email patterns from same IP
   - Rapid signup patterns

3. **Block obvious abuse:**
   ```
   POST /pay-per-use/admin/block-ip
   - IP address to block
   - Reason for blocking
   - Your admin key
   ```

### Weekly Review (15 minutes)
1. **Check all IPs with 2+ attempts**
2. **Review user patterns**
3. **Adjust abuse prevention settings if needed**

## 🚨 Security Best Practices

### ✅ DO:
- Use a unique, complex admin key (20+ characters)
- Store admin key in environment variables only
- Change admin key every 3-6 months
- Keep admin key secret (don't share in email/chat)
- Use HTTPS only for admin requests

### ❌ DON'T:
- Use simple passwords like "admin123"
- Store admin key in code files
- Share admin key with unauthorized people
- Use admin key in client-side code
- Access admin endpoints over HTTP

## 📊 Admin Response Examples

### Suspicious IPs Response:
```json
{
  "suspicious_ips": [
    {
      "ip_address": "192.168.1.100",
      "trial_count": 5,
      "first_trial_date": "2024-01-01T10:00:00",
      "last_trial_date": "2024-01-01T12:00:00"
    }
  ]
}
```

### Block IP Response:
```json
{
  "message": "IP 192.168.1.100 has been blocked"
}
```

## 🔍 Monitoring Script

Here's a simple script to check for abuse daily:

```bash
#!/bin/bash
# Save as: check_abuse.sh

ADMIN_KEY="your-admin-key-here"
API_URL="https://your-api-url.onrender.com"

echo "🔍 Checking for suspicious activity..."
curl -s "${API_URL}/pay-per-use/admin/suspicious-ips?min_trials=3&admin_key=${ADMIN_KEY}" \
  | jq '.suspicious_ips[] | "IP: \(.ip_address) - \(.trial_count) attempts"'

echo "✅ Check complete"
```

## 🆘 If Admin Key is Compromised

1. **Immediately change the admin key** in Render environment variables
2. **Redeploy your service** to pick up new key
3. **Review recent admin activity** in logs
4. **Check for any malicious IP blocks** that need to be reversed

---

**Remember:** The admin key is like the master password for your system. Treat it with the same security as your banking passwords! 