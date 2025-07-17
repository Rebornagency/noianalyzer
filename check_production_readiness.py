#!/usr/bin/env python3
"""
Production Readiness Check for NOI Analyzer
This script checks your configuration and identifies what needs to be fixed for production deployment
"""

import os
import logging
from datetime import datetime

def check_environment_variables():
    """Check if required environment variables are set"""
    print("🔍 ENVIRONMENT VARIABLES CHECK")
    print("=" * 50)
    
    # Critical security variables
    security_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ADMIN_API_KEY": os.getenv("ADMIN_API_KEY"),
        "SENTRY_DSN": os.getenv("SENTRY_DSN"),
    }
    
    # Stripe payment variables
    stripe_vars = {
        "STRIPE_SECRET_KEY": os.getenv("STRIPE_SECRET_KEY"),
        "STRIPE_WEBHOOK_SECRET": os.getenv("STRIPE_WEBHOOK_SECRET"),
        "STRIPE_STARTER_PRICE_ID": os.getenv("STRIPE_STARTER_PRICE_ID"),
        "STRIPE_PROFESSIONAL_PRICE_ID": os.getenv("STRIPE_PROFESSIONAL_PRICE_ID"),
        "STRIPE_BUSINESS_PRICE_ID": os.getenv("STRIPE_BUSINESS_PRICE_ID"),
    }
    
    # Email service variables
    email_vars = {
        "RESEND_API_KEY": os.getenv("RESEND_API_KEY"),
        "FROM_EMAIL": os.getenv("FROM_EMAIL"),
    }
    
    # URL configuration
    url_vars = {
        "BACKEND_URL": os.getenv("BACKEND_URL"),
        "CREDIT_SUCCESS_URL": os.getenv("CREDIT_SUCCESS_URL"),
        "CREDIT_CANCEL_URL": os.getenv("CREDIT_CANCEL_URL"),
    }
    
    # Abuse prevention settings
    abuse_vars = {
        "FREE_TRIAL_CREDITS": os.getenv("FREE_TRIAL_CREDITS", "1"),
        "MAX_TRIALS_PER_IP": os.getenv("MAX_TRIALS_PER_IP", "2"),
        "TRIAL_COOLDOWN_DAYS": os.getenv("TRIAL_COOLDOWN_DAYS", "7"),
    }
    
    def check_category(category_name, variables):
        print(f"\n📋 {category_name}:")
        all_good = True
        for var_name, var_value in variables.items():
            if var_value and not any(placeholder in var_value.lower() for placeholder in ['replace', 'placeholder', 'your_', 'sk_test_']):
                status = "✅"
                preview = var_value[:20] + "..." if len(var_value) > 20 else var_value
            elif var_value:
                status = "⚠️ "
                preview = "HAS VALUE BUT LOOKS LIKE PLACEHOLDER"
                all_good = False
            else:
                status = "❌"
                preview = "NOT SET"
                all_good = False
            
            print(f"   {status} {var_name}: {preview}")
        return all_good
    
    security_ok = check_category("SECURITY", security_vars)
    stripe_ok = check_category("STRIPE PAYMENTS", stripe_vars)
    email_ok = check_category("EMAIL SERVICE", email_vars)
    url_ok = check_category("URLS", url_vars)
    abuse_ok = check_category("ABUSE PREVENTION", abuse_vars)
    
    return security_ok, stripe_ok, email_ok, url_ok, abuse_ok

def check_files():
    """Check if required files exist"""
    print("\n📁 FILES CHECK")
    print("=" * 50)
    
    required_files = [
        "app.py",
        "pay_per_use/database.py",
        "pay_per_use/credit_service.py",
        "utils/credit_ui.py",
        "requirements.txt",
    ]
    
    optional_files = [
        ".env",
        "PRODUCTION_DEPLOYMENT_CHECKLIST.md",
        "STRIPE_SETUP_GUIDE.md",
    ]
    
    all_good = True
    
    print("\n📋 REQUIRED FILES:")
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING")
            all_good = False
    
    print("\n📋 RECOMMENDED FILES:")
    for file in optional_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ⚠️  {file} - RECOMMENDED")
    
    return all_good

def check_security_issues():
    """Check for security issues in code"""
    print("\n🔐 SECURITY ISSUES CHECK")
    print("=" * 50)
    
    security_issues = []
    
    # Check for hardcoded API keys in common files
    files_to_check = [
        "fixed_config.py",
        "config.py",
        "app.py",
    ]
    
    dangerous_patterns = [
        "sk-proj-",
        "sk-test-",
        "sk-live-",
        "HARDCODED_",
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern in dangerous_patterns:
                        if pattern in content and not content.count(f"# {pattern}") > 0:  # Ignore commented lines
                            security_issues.append(f"Found '{pattern}' in {file_path}")
            except Exception as e:
                print(f"   ⚠️  Could not check {file_path}: {e}")
    
    if security_issues:
        print("   ❌ SECURITY ISSUES FOUND:")
        for issue in security_issues:
            print(f"      🚨 {issue}")
        return False
    else:
        print("   ✅ No obvious security issues found in code")
        return True

def generate_production_report():
    """Generate a comprehensive production readiness report"""
    print("🚀 NOI ANALYZER - PRODUCTION READINESS CHECK")
    print("=" * 60)
    print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    security_env, stripe_env, email_env, url_env, abuse_env = check_environment_variables()
    files_ok = check_files()
    security_ok = check_security_issues()
    
    print("\n" + "=" * 60)
    print("📊 OVERALL READINESS ASSESSMENT")
    print("=" * 60)
    
    total_score = 0
    max_score = 6
    
    categories = [
        ("Security Environment Variables", security_env),
        ("Stripe Configuration", stripe_env),
        ("Email Service", email_env),
        ("URL Configuration", url_env),
        ("Required Files", files_ok),
        ("Security Issues", security_ok),
    ]
    
    for category, status in categories:
        if status:
            print(f"   ✅ {category}")
            total_score += 1
        else:
            print(f"   ❌ {category}")
    
    percentage = (total_score / max_score) * 100
    
    print(f"\n🎯 PRODUCTION READINESS: {total_score}/{max_score} ({percentage:.0f}%)")
    
    if percentage >= 80:
        print("   🟢 READY FOR PRODUCTION with minor fixes")
    elif percentage >= 60:
        print("   🟡 NEEDS SIGNIFICANT WORK before production")
    else:
        print("   🔴 NOT READY FOR PRODUCTION - Major issues to fix")
    
    print("\n📋 NEXT STEPS:")
    if not security_env:
        print("   1. 🔐 Set up security environment variables (CRITICAL)")
    if not stripe_env:
        print("   2. 💳 Configure Stripe payment system (CRITICAL)")
    if not email_env:
        print("   3. 📧 Set up email service")
    if not url_env:
        print("   4. 🌐 Configure production URLs")
    if not files_ok:
        print("   5. 📁 Fix missing required files")
    if not security_ok:
        print("   6. 🔐 Fix security issues in code")
    
    print(f"\n📖 For detailed instructions, see: PRODUCTION_DEPLOYMENT_CHECKLIST.md")
    print(f"💳 For Stripe setup, see: STRIPE_SETUP_GUIDE.md")

if __name__ == "__main__":
    try:
        generate_production_report()
    except Exception as e:
        print(f"❌ Error running production readiness check: {e}")
        print("Make sure you're running this from the project root directory.") 