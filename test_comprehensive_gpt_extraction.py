import io
from ai_extraction import extract_data_from_documents

# Create mock file objects with sample financial data
current_month_text = """
CURRENT MONTH ACTUALS - JANUARY 2024

REVENUE:
Gross Potential Rent: $100,000
Vacancy Loss: ($5,000)
Concessions: ($2,000)
Other Income: $3,000
Effective Gross Income: $96,000

EXPENSES:
Property Taxes: $12,000
Insurance: $2,000
Repairs & Maintenance: $3,000
Utilities: $4,000
Management Fees: $6,000
Total Operating Expenses: $27,000

Net Operating Income: $69,000
"""

prior_month_text = """
PRIOR MONTH ACTUALS - DECEMBER 2023

REVENUE:
Gross Potential Rent: $95,000
Vacancy Loss: ($4,500)
Concessions: ($1,500)
Other Income: $2,500
Effective Gross Income: $91,500

EXPENSES:
Property Taxes: $11,500
Insurance: $2,000
Repairs & Maintenance: $2,500
Utilities: $3,800
Management Fees: $5,800
Total Operating Expenses: $25,600

Net Operating Income: $65,900
"""

budget_text = """
BUDGET - 2024

REVENUE:
Gross Potential Rent: $102,000
Vacancy Loss: ($5,200)
Concessions: ($2,100)
Other Income: $3,200
Effective Gross Income: $97,900

EXPENSES:
Property Taxes: $12,200
Insurance: $2,100
Repairs & Maintenance: $3,100
Utilities: $4,100
Management Fees: $6,100
Total Operating Expenses: $27,600

Net Operating Income: $70,300
"""

# Create file-like objects
current_month_file = io.BytesIO(current_month_text.encode('utf-8'))
current_month_file.name = "current_month_actuals.txt"

prior_month_file = io.BytesIO(prior_month_text.encode('utf-8'))
prior_month_file.name = "prior_month_actuals.txt"

budget_file = io.BytesIO(budget_text.encode('utf-8'))
budget_file.name = "budget.txt"

# Test the extraction function for all documents
try:
    result = extract_data_from_documents(
        current_month_file=current_month_file,
        prior_month_file=prior_month_file,
        budget_file=budget_file
    )
    
    print("Extraction successful!")
    print(f"Result keys: {list(result.keys())}")
    
    if "current_month" in result:
        current = result["current_month"]
        print("\nCurrent Month Data:")
        print(f"GPR: {current.get('gpr', 'Not found')}")
        print(f"NOI: {current.get('noi', 'Not found')}")
        print(f"OpEx: {current.get('opex', 'Not found')}")
    
    if "prior_month" in result:
        prior = result["prior_month"]
        print("\nPrior Month Data:")
        print(f"GPR: {prior.get('gpr', 'Not found')}")
        print(f"NOI: {prior.get('noi', 'Not found')}")
        print(f"OpEx: {prior.get('opex', 'Not found')}")
    
    if "budget" in result:
        budget = result["budget"]
        print("\nBudget Data:")
        print(f"GPR: {budget.get('gpr', 'Not found')}")
        print(f"NOI: {budget.get('noi', 'Not found')}")
        print(f"OpEx: {budget.get('opex', 'Not found')}")
        
except Exception as e:
    print(f"Error during extraction: {e}")
    import traceback
    traceback.print_exc()