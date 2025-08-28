#!/usr/bin/env python3
"""
NOI Analyzer - Setup and Fix Current System
Run this before implementing any enhancements
"""

import os
import sys
import subprocess

def install_dependencies():
    """Install missing dependencies"""
    print("📦 Installing missing dependencies...")
    
    required_packages = [
        "pydantic",
        "fastapi", 
        "uvicorn",
        "stripe",
        "requests",
        "python-dotenv"
    ]
    
    for package in required_packages:
        try:
            print(f"   Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"   ✅ {package} installed")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to install {package}: {e}")
            return False
    
    return True

def create_env_template():
    """Create .env template file"""
    print("📝 Creating environment template...")
    
    env_content = """# NOI Analyzer Environment Variables
# CRITICAL: Replace all placeholder values with real ones

# OpenAI API Key (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here

# Stripe Configuration (REQUIRED for payments)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_STARTER_PRICE_ID=price_your_starter_price_id
STRIPE_PROFESSIONAL_PRICE_ID=price_your_professional_price_id
STRIPE_BUSINESS_PRICE_ID=price_your_business_price_id

# Credit System Configuration
FREE_TRIAL_CREDITS=3
MAX_TRIALS_PER_IP=2
TRIAL_COOLDOWN_DAYS=7
CREDITS_PER_ANALYSIS=1

# URLs (Update with your domain)
BACKEND_URL=http://localhost:8000
CREDIT_SUCCESS_URL=http://localhost:8000/credit-success?session_id={CHECKOUT_SESSION_ID}&email={email}
CREDIT_CANCEL_URL=http://localhost:8000/payment-cancel
MAIN_APP_URL=http://localhost:8501

# Database
DATABASE_PATH=noi_analyzer.db

# Admin (for testing)
ADMIN_API_KEY=test_admin_key_change_me

# Optional: Error tracking
SENTRY_DSN=your_sentry_dsn_here
SENTRY_ENVIRONMENT=development
"""
    
    env_file = ".env"
    if not os.path.exists(env_file):
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ Created {env_file} template")
        print("⚠️  IMPORTANT: Edit .env file with your real API keys!")
    else:
        print(f"⚠️  {env_file} already exists - not overwriting")
    
    return True

def initialize_database():
    """Initialize the database"""
    print("🗄️  Initializing database...")
    
    try:
        # Import after dependencies are installed
        from pay_per_use.database import db_service
        
        # This will create the database file and tables
        print("   Creating database tables...")
        db_service.init_database()
        
        # Create default packages
        print("   Creating default credit packages...")
        db_service.create_default_packages()
        
        print("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def test_basic_functionality():
    """Test that everything is working"""
    print("🧪 Testing basic functionality...")
    
    try:
        from pay_per_use.database import db_service
        from pay_per_use.credit_service import credit_service
        
        # Test user creation
        test_email = "test@example.com"
        user = db_service.get_or_create_user(test_email)
        print(f"✅ Test user created: {user.email} with {user.credits} credits")
        
        # Test packages
        packages = db_service.get_active_packages()
        print(f"✅ Found {len(packages)} credit packages")
        
        return True
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 NOI Analyzer - System Setup")
    print("=" * 40)
    
    steps = [
        ("Install Dependencies", install_dependencies),
        ("Create Environment Template", create_env_template),
        ("Initialize Database", initialize_database),
        ("Test Basic Functionality", test_basic_functionality)
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"❌ Setup failed at: {step_name}")
            return False
    
    print("\n" + "=" * 40)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("\n📝 Next Steps:")
    print("1. Edit .env file with your real API keys")
    print("2. Test the credit system: python verify_credit_system.py")
    print("3. Start the API server: python api_server_minimal.py")
    print("4. Test purchases in the Streamlit app")
    print("\n⚠️  ONLY AFTER TESTING, consider the enhanced features")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup failed. Please fix the issues above.")
        sys.exit(1)