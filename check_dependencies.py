#!/usr/bin/env python3
"""
Comprehensive Dependency Check for NOI Analyzer
Verifies all required packages and modules are available and properly configured.
"""

import sys
import os
import importlib
from typing import List, Dict, Tuple

def check_python_version() -> bool:
    """Check if Python version is sufficient"""
    min_version = (3, 8)
    current_version = sys.version_info[:2]
    
    print(f"🐍 Python Version: {sys.version}")
    if current_version >= min_version:
        print("✅ Python version is compatible")
        return True
    else:
        print(f"❌ Python {min_version[0]}.{min_version[1]}+ required, found {current_version[0]}.{current_version[1]}")
        return False

def check_core_dependencies() -> List[Tuple[str, bool, str]]:
    """Check all core dependencies from requirements.txt"""
    
    dependencies = [
        # Core Streamlit application
        ("streamlit", "1.28.0", "Core Streamlit framework"),
        
        # Data processing
        ("pandas", "2.0.3", "Data manipulation"),
        ("numpy", "1.24.3", "Numerical computing"),
        
        # API and web requests
        ("requests", "2.31.0", "HTTP requests"),
        
        # File processing
        ("pdfplumber", "0.9.0", "PDF text extraction"),
        ("chardet", "5.2.0", "Character encoding detection"),
        
        # AI and language models
        ("openai", "1.3.0", "OpenAI API client"),
        
        # Visualization
        ("plotly", "5.15.0", "Interactive charts"),
        
        # Environment configuration
        ("dotenv", "1.0.0", "Environment variable loading"),
        
        # Report generation
        ("jinja2", "3.1.2", "Template engine"),
        ("xlsxwriter", "3.1.2", "Excel file generation"),
        
        # Error tracking
        ("sentry_sdk", "1.32.0", "Error monitoring"),
        
        # Payment processing
        ("stripe", "6.7.0", "Payment processing"),
        
        # Essential utilities
        ("typing_extensions", "4.7.1", "Type extensions"),
        ("email_validator", "2.1.0", "Email validation"),
    ]
    
    results = []
    print("\n📦 Checking Core Dependencies:")
    print("-" * 50)
    
    for package, expected_version, description in dependencies:
        try:
            # Handle special package names
            import_name = package
            if package == "dotenv":
                import_name = "python_dotenv"
            elif package == "email_validator":
                import_name = "email_validator"
            
            module = importlib.import_module(import_name)
            
            # Try to get version
            version = "unknown"
            if hasattr(module, "__version__"):
                version = module.__version__
            elif hasattr(module, "version"):
                version = module.version
            elif hasattr(module, "VERSION"):
                version = module.VERSION
                
            print(f"✅ {package:<20} v{version:<15} - {description}")
            results.append((package, True, version))
            
        except ImportError as e:
            print(f"❌ {package:<20} {'MISSING':<15} - {description}")
            results.append((package, False, str(e)))
        except Exception as e:
            print(f"⚠️  {package:<20} {'ERROR':<15} - {description}: {str(e)}")
            results.append((package, False, str(e)))
    
    return results

def check_optional_dependencies() -> List[Tuple[str, bool, str]]:
    """Check optional dependencies that won't break the app if missing"""
    
    optional_deps = [
        ("weasyprint", "PDF generation (optional)"),
        ("fastapi", "FastAPI integration (optional)"),
        ("uvicorn", "ASGI server (optional)"),
        ("redis", "Redis integration (optional)"),
        ("boto3", "AWS integration (optional)"),
    ]
    
    results = []
    print("\n🔧 Checking Optional Dependencies:")
    print("-" * 50)
    
    for package, description in optional_deps:
        try:
            module = importlib.import_module(package)
            version = getattr(module, "__version__", "unknown")
            print(f"✅ {package:<20} v{version:<15} - {description}")
            results.append((package, True, version))
        except ImportError:
            print(f"⚠️  {package:<20} {'NOT INSTALLED':<15} - {description}")
            results.append((package, False, "Not installed"))
    
    return results

def check_application_modules() -> List[Tuple[str, bool, str]]:
    """Check if all application modules can be imported"""
    
    app_modules = [
        ("config", "Application configuration"),
        ("constants", "Application constants"), 
        ("sentry_config", "Error tracking configuration"),
        ("ai_insights_gpt", "AI insights generation"),
        ("noi_calculations", "NOI calculations"),
        ("utils.helpers", "Helper utilities"),
        ("utils.credit_ui", "Credit system UI"),
        ("utils.ui_helpers", "UI helper functions"),
        ("financial_storyteller", "Financial narrative generation"),
        ("storyteller_display", "Narrative display"),
        ("reborn_logo", "Logo utilities"),
        ("insights_display", "Insights display"),
        ("ai_extraction", "AI data extraction"),
    ]
    
    results = []
    print("\n🏗️  Checking Application Modules:")
    print("-" * 50)
    
    for module, description in app_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module:<25} - {description}")
            results.append((module, True, "OK"))
        except ImportError as e:
            print(f"❌ {module:<25} - {description}: {str(e)}")
            results.append((module, False, str(e)))
        except Exception as e:
            print(f"⚠️  {module:<25} - {description}: {str(e)}")
            results.append((module, False, str(e)))
    
    return results

def check_environment_variables() -> Dict[str, bool]:
    """Check critical environment variables"""
    
    env_vars = [
        ("OPENAI_API_KEY", "OpenAI API access", False),
        ("SENTRY_DSN", "Error tracking", True),
        ("STRIPE_SECRET_KEY", "Payment processing", True),
        ("BACKEND_URL", "Backend API URL", True),
        ("ADMIN_PASSWORD", "Admin dashboard access", True),
    ]
    
    results = {}
    print("\n🔑 Checking Environment Variables:")
    print("-" * 50)
    
    for var_name, description, optional in env_vars:
        value = os.getenv(var_name)
        if value:
            # Mask sensitive values
            display_value = f"{value[:8]}..." if len(value) > 8 else "SET"
            print(f"✅ {var_name:<20} {display_value:<15} - {description}")
            results[var_name] = True
        else:
            status = "⚠️ " if optional else "❌"
            print(f"{status} {var_name:<20} {'NOT SET':<15} - {description}")
            results[var_name] = False
    
    return results

def main():
    """Run comprehensive dependency check"""
    print("🔍 NOI Analyzer - Comprehensive Dependency Check")
    print("=" * 60)
    
    # Check Python version
    python_ok = check_python_version()
    
    # Check dependencies
    core_deps = check_core_dependencies()
    optional_deps = check_optional_dependencies()
    app_modules = check_application_modules()
    env_vars = check_environment_variables()
    
    # Summary
    print("\n📋 SUMMARY:")
    print("=" * 60)
    
    core_missing = [dep for dep, status, _ in core_deps if not status]
    app_missing = [mod for mod, status, _ in app_modules if not status]
    env_missing = [var for var, status in env_vars.items() if not status and var == "OPENAI_API_KEY"]
    
    if python_ok and not core_missing and not app_missing:
        print("🎉 ALL CRITICAL DEPENDENCIES ARE SATISFIED!")
        print("✅ The NOI Analyzer website should work properly.")
        
        if optional_deps:
            optional_available = [dep for dep, status, _ in optional_deps if status]
            print(f"🔧 Optional features available: {len(optional_available)}/{len(optional_deps)}")
        
        if env_missing:
            print(f"⚠️  Environment variables to configure: {', '.join(env_missing)}")
        
        print("\n🚀 You can start the application with: streamlit run app.py")
        
    else:
        print("❌ CRITICAL ISSUES FOUND:")
        
        if not python_ok:
            print("   - Python version needs upgrade")
        
        if core_missing:
            print(f"   - Missing core dependencies: {', '.join(core_missing)}")
            print("   - Run: pip install -r requirements.txt")
        
        if app_missing:
            print(f"   - Missing application modules: {', '.join(app_missing)}")
        
        print("\n🔧 Please resolve these issues before starting the application.")

if __name__ == "__main__":
    main()