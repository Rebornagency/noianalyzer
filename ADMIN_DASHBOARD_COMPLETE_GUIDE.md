# 🛠️ Complete Admin Dashboard Setup Guide

## 🎉 What's New - Full Admin Control Enabled!

Your admin dashboard now has **complete functionality** with secure API endpoints for:

✅ **User Management**
- View all users with detailed information
- Search and filter users
- Quick credit adjustments per user
- User status management (active/suspended/banned)

✅ **Credit Management**
- Manual credit adjustments with full audit trail
- Real-time credit balance updates
- Transaction history viewing
- System-wide credit statistics

✅ **Transaction Monitoring**
- Complete transaction history
- Filter by user or view all
- Transaction type categorization
- Credit flow analysis

✅ **System Monitoring**
- Real-time system statistics
- Credit usage analytics
- Recent activity tracking
- System health checks

✅ **Security & Abuse Prevention**
- IP monitoring and blocking
- Suspicious activity detection
- Secure admin authentication
- Complete audit logging

## 🚀 Quick Start Guide

### 1. Set Your Admin API Key (CRITICAL)

**For Security**: Set a strong admin API key in your environment:

```bash
# In production (Render dashboard)
ADMIN_API_KEY=your_ultra_secure_admin_key_2024_change_this

# For local testing
export ADMIN_API_KEY=your_local_admin_key_for_testing
```

**Important**: Replace the default test key with something secure (20+ characters)!

### 2. Start Your Services

```bash
# Start the API server (with new admin endpoints)
python api_server_minimal.py

# In another terminal, start the admin dashboard
streamlit run admin_dashboard.py
```

### 3. Access Your Admin Dashboard

1. Open your browser to the admin dashboard URL
2. Login with your admin password (default: `admin123`)
3. You now have full admin control!

## 🔧 Available Admin Functions

### **User Management Tab**
- **Search Users**: Find users by email
- **View User Details**: Complete user profiles with statistics
- **Quick Credit Adjustments**: Add/remove credits instantly
- **Status Management**: Activate, suspend, or ban users
- **User Activity**: See creation dates and activity

### **Transaction History Tab**
- **View All Transactions**: Complete transaction log
- **Filter by User**: Focus on specific user's transactions
- **Transaction Types**: Purchase, usage, bonus, refund tracking
- **Detailed Information**: Timestamps, amounts, descriptions

### **Support Tools Tab**
- **Enhanced User Lookup**: Get complete user details and history
- **Manual Credit Adjustments**: Add/remove credits with reasons
- **System Health Checks**: Test API connectivity and admin access
- **Real-time Updates**: See changes immediately

### **System Stats Tab**
- **Key Metrics**: Users, credits, transactions overview
- **Recent Activity**: New users and purchases tracking
- **Credit Analysis**: Usage rates and flow analysis
- **Visual Charts**: Credit distribution graphs
- **System Health**: Database and API status monitoring

## 🛡️ Security Features

### **Admin Authentication**
- Secure API key authentication for all admin endpoints
- Admin password protection for dashboard access
- Unauthorized access prevention

### **Audit Trail**
- All admin actions are logged with timestamps
- Credit adjustments include admin identifier and reason
- Transaction history maintains complete records

### **Input Validation**
- Email validation for all user operations
- Credit amount validation (no zero adjustments)
- Reason requirements for all manual changes

## 🔍 Admin API Endpoints Reference

### User Management
- `GET /pay-per-use/admin/users` - Get all users
- `GET /pay-per-use/admin/user/{email}` - Get user details
- `POST /pay-per-use/admin/user-status` - Update user status

### Credit Management
- `POST /pay-per-use/admin/adjust-credits` - Manual credit adjustment
- `GET /pay-per-use/admin/stats` - System statistics

### Transaction & Monitoring
- `GET /pay-per-use/admin/transactions` - All transactions
- `GET /pay-per-use/admin/suspicious-ips` - Abuse monitoring
- `POST /pay-per-use/admin/block-ip` - Block suspicious IPs

## 🧪 Testing Your Setup

Run the test script to verify everything works:

```bash
python test_admin_endpoints.py
```

This will test all admin endpoints and confirm your setup is working correctly.

## 💡 Usage Examples

### **Add Credits to User**
1. Go to "Support Tools" tab
2. Enter user email and credit amount
3. Provide reason (e.g., "Customer support compensation")
4. Click "Apply Credit Adjustment"
5. See updated balance immediately

### **Investigate User Issue**
1. Go to "Support Tools" tab
2. Enter user email in "Enhanced User Lookup"
3. View complete user profile and transaction history
4. Make adjustments if needed

### **Monitor System Health**
1. Go to "System Stats" tab
2. Review key metrics and recent activity
3. Check credit flow and usage patterns
4. Use auto-refresh for real-time monitoring

### **Handle Abuse**
1. Go to "System Stats" and check suspicious activity
2. Use admin endpoints to view suspicious IPs
3. Block IPs if necessary
4. Monitor new user patterns

## 🚨 Emergency Procedures

### **If User Lost Credits**
1. Use "Enhanced User Lookup" to check transaction history
2. Identify the issue (failed payment, system error, etc.)
3. Use "Manual Credit Adjustment" to restore credits
4. Document the reason clearly

### **If System Issues**
1. Use "System Health Check" to test connectivity
2. Check admin API key configuration
3. Verify database accessibility
4. Review recent transaction patterns

## 🔒 Security Best Practices

### **Admin API Key**
- Use a unique, strong key (20+ characters)
- Store in environment variables only
- Change regularly (every 3-6 months)
- Never share or commit to code

### **Admin Password**
- Change from default "admin123" immediately
- Use environment variable: `ADMIN_PASSWORD=your_secure_password`
- Keep secure and don't share

### **Monitoring**
- Regular check of system stats
- Monitor for unusual activity patterns
- Review transaction logs periodically
- Check for new suspicious IPs

## 🎯 Production Deployment

### **Environment Variables Required**
```bash
# Essential
ADMIN_API_KEY=your_secure_admin_key_here
ADMIN_PASSWORD=your_secure_admin_password

# API Configuration
CREDIT_API_URL=https://your-api-server.onrender.com

# Database
DATABASE_PATH=noi_analyzer.db
```

### **Render Deployment**
1. Add all environment variables in Render dashboard
2. Deploy admin dashboard as separate service
3. Use `requirements-admin.txt` for minimal dependencies
4. Test all functionality in production

## 🆘 Troubleshooting

### **"Unauthorized" Errors**
- Check ADMIN_API_KEY matches between client and server
- Verify environment variable is set correctly
- Restart services after changing keys

### **"Connection Failed" Errors**
- Ensure API server is running
- Check CREDIT_API_URL configuration
- Verify network connectivity

### **"User Not Found" Errors**
- Confirm email address is correct
- Check if user actually exists in system
- Verify database is accessible

### **Dashboard Not Loading**
- Check admin password configuration
- Verify all dependencies are installed
- Check for any import errors

## 🎉 You're All Set!

Your admin dashboard now has **complete control** over your NOI Analyzer credit system. You can:

- ✅ Manage all users and their credits
- ✅ Handle customer support issues instantly
- ✅ Monitor system health and usage
- ✅ Prevent abuse and handle security issues
- ✅ Get real-time insights into your business

**Enjoy your powerful admin capabilities!** 🚀