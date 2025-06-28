"""
Centralized Constants for NOI Analyzer

This module contains all constants, magic strings, and configuration values
used throughout the NOI Analyzer application.
"""

# Financial Metrics
MAIN_METRICS = [
    "gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"
]

# Canonical OpEx components – keep these names everywhere
OPEX_COMPONENTS = [
    "property_taxes",
    "insurance",
    "repairs_maintenance",
    "utilities",
    "management_fees",
    # historical / less-common buckets
    "administrative",
    "payroll",
    "marketing",
    "other_expenses"
]

# Canonical Other-Income components
INCOME_COMPONENTS = [
    "parking",
    "laundry",
    "late_fees",
    "pet_fees",
    "application_fees",
    "storage_fees",
    "amenity_fees",
    "utility_reimbursements",
    "cleaning_fees",
    "cancellation_fees",
    "miscellaneous"
]

# Document Types
DOCUMENT_TYPES = {
    "CURRENT_MONTH": "current_month",
    "PRIOR_MONTH": "prior_month", 
    "BUDGET": "budget",
    "PRIOR_YEAR": "prior_year"
}

# API Configuration
DEFAULT_API_CONFIG = {
    "EXTRACTION_API_URL": "https://dataextractionai.onrender.com",
    "TIMEOUT": 60,
    "MAX_RETRIES": 3,
    "BATCH_SIZE": 5
}

# Data Formats
DATE_FORMAT = "%Y-%m-%d"
CURRENCY_FORMAT = "USD"

# Field Mappings for API responses
FIELD_MAPPING = {
    "gpr": ["gross_potential_rent", "potential_rent", "scheduled_rent"],
    "opex": ["operating_expenses", "total_operating_expenses", "expenses_total"],
    "noi": ["net_operating_income", "noi", "net_income"],
    "egi": ["effective_gross_income", "adjusted_income", "effective_income"]
}

# Field-name synonyms → canonical name.  Used by utils.common.normalize_field_names()
FIELD_SYNONYMS = {
    # OpEx
    "taxes": "property_taxes",
    "property_tax": "property_taxes",
    "repairs_and_maintenance": "repairs_maintenance",
    "property_management": "management_fees",
    # Other Income aliases
    "parking_income": "parking",
    "laundry_income": "laundry",
    "misc": "miscellaneous",
}

# Validation tolerances
FINANCIAL_TOLERANCE = 1.0  # Dollar tolerance for financial checks
FINANCIAL_EPS = 1e-4       # Small epsilon for divide-by-zero guards

# UI Constants
DISPLAY_PRECISION = 2  # Decimal places for financial displays
CURRENCY_SYMBOL = "$"

# Log Configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = "INFO"

# Error Messages
ERROR_MESSAGES = {
    "INVALID_API_RESPONSE": "Invalid API response received",
    "MISSING_REQUIRED_KEYS": "Missing required keys in data",
    "EGI_INCONSISTENCY": "EGI calculation inconsistency detected",
    "NOI_INCONSISTENCY": "NOI calculation inconsistency detected", 
    "OPEX_INCONSISTENCY": "OpEx components sum inconsistency detected",
    "INCOME_INCONSISTENCY": "Other Income components sum inconsistency detected",
    "FILE_PROCESSING_ERROR": "Error processing file",
    "API_KEY_MISSING": "API key not found",
    "VALIDATION_FAILED": "Data validation failed"
}

# Success Messages
SUCCESS_MESSAGES = {
    "DATA_LOADED": "Data loaded successfully",
    "VALIDATION_PASSED": "Data validation passed",
    "FILE_PROCESSED": "File processed successfully",
    "NARRATIVE_GENERATED": "Financial narrative generated successfully"
}

# Environment Variable Names
ENV_VARS = {
    "OPENAI_API_KEY": "OPENAI_API_KEY",
    "EXTRACTION_API_KEY": "EXTRACTION_API_KEY", 
    "EXTRACTION_API_URL": "EXTRACTION_API_URL",
    "API_TIMEOUT": "API_TIMEOUT",
    "API_MAX_RETRIES": "API_MAX_RETRIES"
}

# Streamlit Configuration
STREAMLIT_CONFIG = {
    "PAGE_TITLE": "NOI Analyzer",
    "PAGE_ICON": "📊",
    "LAYOUT": "wide",
    "INITIAL_SIDEBAR_STATE": "expanded"
}

# File Upload Configuration
FILE_UPLOAD_CONFIG = {
    "MAX_FILE_SIZE": 200,  # MB
    "ACCEPTED_TYPES": ["pdf", "png", "jpg", "jpeg"],
    "MAX_FILES": 10
} 