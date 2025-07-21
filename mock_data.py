import random
import datetime
from typing import Dict, Any, Optional, List

def generate_mock_financial_data(document_type: str, base_value: float = 100000.0, 
                                variance: float = 0.1, scenario: str = "Standard Performance") -> Dict[str, Any]:
    """
    Generate realistic mock financial data for testing.
    
    Args:
        document_type: Type of document (current_month, prior_month, budget, prior_year)
        base_value: Base value for GPR
        variance: Variance factor for randomization
        scenario: Testing scenario to adjust data patterns
        
    Returns:
        Dictionary containing mock financial data
    """
    # Apply scenario-specific adjustments
    if scenario == "High Growth":
        if document_type == "current_month":
            base_multiplier = 1.15  # Current month shows strong growth
        elif document_type == "prior_month":
            base_multiplier = 0.95  # Prior month was lower
        elif document_type == "budget":
            base_multiplier = 1.05  # Budget was conservative
        else:  # prior_year
            base_multiplier = 0.85  # Prior year was much lower
    elif scenario == "Declining Performance":
        if document_type == "current_month":
            base_multiplier = 0.92  # Current month shows decline
        elif document_type == "prior_month":
            base_multiplier = 0.98  # Prior month was better
        elif document_type == "budget":
            base_multiplier = 1.10  # Budget was optimistic
        else:  # prior_year
            base_multiplier = 1.05  # Prior year was better
    elif scenario == "Budget Variance":
        if document_type == "current_month":
            base_multiplier = 1.0  # Current month is baseline
        elif document_type == "prior_month":
            base_multiplier = 0.97  # Prior month slightly lower
        elif document_type == "budget":
            base_multiplier = 1.20  # Budget was very optimistic
        else:  # prior_year
            base_multiplier = 0.95  # Prior year was lower
    else:  # Standard Performance
        if document_type == "current_month":
            base_multiplier = 1.0  # Current month is baseline
        elif document_type == "prior_month":
            base_multiplier = 0.98  # Prior month slightly lower
        elif document_type == "budget":
            base_multiplier = 1.02  # Budget slightly higher
        else:  # prior_year
            base_multiplier = 0.94  # Prior year was lower
    
    # Calculate base GPR with randomization
    gpr = base_value * base_multiplier * random.uniform(1.0 - variance, 1.0 + variance)
    
    # Calculate other metrics based on GPR
    vacancy_rate = random.uniform(0.03, 0.08)
    vacancy_loss = gpr * vacancy_rate
    
    other_income_rate = random.uniform(0.05, 0.12)
    other_income = gpr * other_income_rate
    
    egi = gpr - vacancy_loss + other_income
    
    opex_rate = random.uniform(0.35, 0.45)
    opex = egi * opex_rate
    
    noi = egi - opex
    
    # Generate appropriate dates based on document type
    if document_type == "current_month":
        date = datetime.datetime.now()
    elif document_type == "prior_month":
        date = datetime.datetime.now() - datetime.timedelta(days=30)
    elif document_type == "prior_year":
        date = datetime.datetime.now() - datetime.timedelta(days=365)
    else:
        date = datetime.datetime.now()
    
    # Format date as string
    date_str = date.strftime("%Y-%m-%d")
    
    # Create OpEx components with realistic proportions
    property_taxes = opex * random.uniform(0.25, 0.35)
    insurance = opex * random.uniform(0.10, 0.15)
    repairs_maintenance = opex * random.uniform(0.15, 0.25)
    utilities = opex * random.uniform(0.15, 0.25)
    management_fees = opex * random.uniform(0.05, 0.10)
    administrative = opex * random.uniform(0.05, 0.10)
    payroll = opex * random.uniform(0.05, 0.10)
    marketing = opex * random.uniform(0.02, 0.05)
    other_expenses = opex - (property_taxes + insurance + repairs_maintenance + 
                            utilities + management_fees + administrative + 
                            payroll + marketing)
    
    # Create Other Income components with realistic proportions
    parking = other_income * random.uniform(0.30, 0.40)
    laundry = other_income * random.uniform(0.10, 0.20)
    late_fees = other_income * random.uniform(0.05, 0.10)
    pet_fees = other_income * random.uniform(0.05, 0.15)
    application_fees = other_income * random.uniform(0.05, 0.10)
    storage_fees = other_income * random.uniform(0.05, 0.15)
    amenity_fees = other_income * random.uniform(0.02, 0.05)
    utility_reimbursements = other_income * random.uniform(0.05, 0.15)
    cleaning_fees = other_income * random.uniform(0.02, 0.05)
    cancellation_fees = other_income * random.uniform(0.01, 0.03)
    miscellaneous = other_income - (parking + laundry + late_fees + pet_fees + 
                                   application_fees + storage_fees + amenity_fees + 
                                   utility_reimbursements + cleaning_fees + cancellation_fees)
    
    # Create the mock data dictionary matching the structure expected by the app
    mock_data = {
        "document_type": document_type,
        "document_date": date_str,
        "extraction_timestamp": datetime.datetime.now().timestamp(),
        "extraction_method": "mock_data",
        "gpr": round(gpr, 2),
        "vacancy_loss": round(vacancy_loss, 2),
        "other_income": round(other_income, 2),
        "egi": round(egi, 2),
        "opex": round(opex, 2),
        "noi": round(noi, 2),
        
        # OpEx components
        "property_taxes": round(property_taxes, 2),
        "insurance": round(insurance, 2),
        "repairs_maintenance": round(repairs_maintenance, 2),
        "utilities": round(utilities, 2),
        "management_fees": round(management_fees, 2),
        "administrative": round(administrative, 2),
        "payroll": round(payroll, 2),
        "marketing": round(marketing, 2),
        "other_expenses": round(other_expenses, 2),
        
        # Other Income components
        "parking": round(parking, 2),
        "laundry": round(laundry, 2),
        "late_fees": round(late_fees, 2),
        "pet_fees": round(pet_fees, 2),
        "application_fees": round(application_fees, 2),
        "storage_fees": round(storage_fees, 2),
        "amenity_fees": round(amenity_fees, 2),
        "utility_reimbursements": round(utility_reimbursements, 2),
        "cleaning_fees": round(cleaning_fees, 2),
        "cancellation_fees": round(cancellation_fees, 2),
        "miscellaneous": round(miscellaneous, 2),
    }
    
    return mock_data

def generate_mock_consolidated_data(property_name: str = "Test Property", 
                                   scenario: str = "Standard Performance") -> Dict[str, Any]:
    """
    Generate a complete set of mock consolidated data for all document types.
    
    Args:
        property_name: Name of the property
        scenario: Testing scenario to adjust data patterns
        
    Returns:
        Dictionary containing mock consolidated data for all document types
    """
    # Use the same base value for consistency across document types
    base_value = random.uniform(80000.0, 120000.0)
    
    mock_consolidated_data = {
        "property_name": property_name,
        "current_month": generate_mock_financial_data("current_month", base_value, scenario=scenario),
        "prior_month": generate_mock_financial_data("prior_month", base_value, scenario=scenario),
        "budget": generate_mock_financial_data("budget", base_value, scenario=scenario),
        "prior_year": generate_mock_financial_data("prior_year", base_value, scenario=scenario)
    }
    
    return mock_consolidated_data

def generate_mock_insights(scenario: str = "Standard Performance") -> Dict[str, Any]:
    """
    Generate mock AI insights for testing based on scenario.
    
    Args:
        scenario: Testing scenario to adjust insight content
        
    Returns:
        Dictionary containing mock insights
    """
    # Scenario-specific insights
    if scenario == "High Growth":
        insights = {
            "summary": "The property shows exceptional growth with significant NOI improvements compared to all benchmark periods. Effective Gross Income (EGI) has increased substantially while operating expenses have been well-managed.",
            
            "performance": [
                "Gross Potential Rent (GPR) increased by 15.2% compared to prior month, demonstrating strong revenue growth.",
                "Vacancy loss decreased by 18.3% compared to budget, indicating improved occupancy rates and effective leasing strategies.",
                "Operating expenses remained 7.2% under budget, with utilities showing the largest savings at 9.8% below budgeted amount.",
                "Net Operating Income (NOI) improved by 22.4% year-over-year, demonstrating exceptional property performance improvement.",
                "Other income sources increased by 12.7%, primarily driven by higher parking and amenity fee collections."
            ],
            
            "recommendations": [
                "Consider accelerating planned rent increases given the strong market performance.",
                "Evaluate expansion opportunities or capital improvements to capitalize on positive momentum.",
                "Implement the successful expense control measures from this property across other properties in the portfolio.",
                "Review staffing levels to ensure service quality keeps pace with growth.",
                "Develop a strategy to maintain this growth trajectory through targeted marketing and tenant retention programs."
            ]
        }
    elif scenario == "Declining Performance":
        insights = {
            "summary": "The property shows concerning performance trends with NOI declining compared to prior periods. Revenue has decreased while operating expenses have increased beyond budgeted amounts.",
            
            "performance": [
                "Gross Potential Rent (GPR) decreased by 8.3% compared to prior month, indicating potential market weakness or competitive pressures.",
                "Vacancy loss increased by 12.5% compared to budget, suggesting leasing challenges or tenant retention issues.",
                "Operating expenses exceeded budget by 5.7%, with repairs and maintenance showing the largest variance at 15.3% above budget.",
                "Net Operating Income (NOI) declined by 13.2% year-over-year, representing a significant performance deterioration.",
                "Other income sources decreased by 6.8%, primarily due to lower parking and amenity fee collections."
            ],
            
            "recommendations": [
                "Conduct a comprehensive market analysis to understand competitive pressures and adjust pricing strategy accordingly.",
                "Implement an aggressive leasing campaign to address rising vacancy rates.",
                "Review and optimize expense management practices, particularly in the repairs and maintenance category.",
                "Consider property improvements or amenity enhancements to improve competitiveness.",
                "Develop a detailed action plan with specific milestones to reverse the negative performance trend."
            ]
        }
    elif scenario == "Budget Variance":
        insights = {
            "summary": "The property shows mixed performance with significant variances from budget projections. While some metrics exceed expectations, others fall short, suggesting a need for more accurate forecasting.",
            
            "performance": [
                "Gross Potential Rent (GPR) is 4.2% below budget projections, indicating overly optimistic revenue forecasting.",
                "Vacancy loss is 8.7% better than budget, suggesting conservative occupancy projections.",
                "Operating expenses are 3.5% over budget, with utilities and repairs showing the largest variances.",
                "Net Operating Income (NOI) is 7.8% below budget despite being 3.2% above prior year, indicating a forecasting gap.",
                "Other income sources are 12.3% above budget, primarily due to unexpected increases in parking and storage fees."
            ],
            
            "recommendations": [
                "Review budgeting methodology to improve accuracy of revenue and expense projections.",
                "Implement monthly variance analysis to identify and address trends earlier.",
                "Adjust current year expectations based on actual performance trends.",
                "Develop more detailed category-level budgets, especially for volatile expense categories.",
                "Consider implementing a rolling forecast approach to improve adaptability to changing conditions."
            ]
        }
    else:  # Standard Performance
        insights = {
            "summary": "The property shows stable performance with modest NOI improvements compared to budget and prior periods. Effective Gross Income (EGI) has increased while operating expenses have been well-managed.",
            
            "performance": [
                "Gross Potential Rent (GPR) increased by 5.2% compared to prior month, contributing to overall revenue growth.",
                "Vacancy loss decreased by 3.8% compared to budget, indicating stable occupancy rates.",
                "Operating expenses remained 2.1% under budget, with utilities showing modest savings.",
                "Net Operating Income (NOI) improved by 4.7% year-over-year, demonstrating consistent property performance.",
                "Other income sources increased by 3.5%, primarily driven by parking and laundry revenue."
            ],
            
            "recommendations": [
                "Continue current operational strategies given the stable performance metrics.",
                "Consider modest rent increases aligned with market conditions to maintain competitive positioning.",
                "Evaluate opportunities for incremental expense reductions without impacting service quality.",
                "Implement targeted marketing to further reduce vacancy and increase occupancy rates.",
                "Develop strategies to increase other income sources, particularly in amenity utilization."
            ]
        }
    
    return insights

def generate_mock_narrative(scenario: str = "Standard Performance") -> str:
    """
    Generate mock financial narrative for testing based on scenario.
    
    Args:
        scenario: Testing scenario to adjust narrative content
        
    Returns:
        String containing mock narrative
    """
    # Scenario-specific narratives
    if scenario == "High Growth":
        return """
# Financial Performance Narrative: High Growth

## Overview

The property has demonstrated exceptional financial performance this period, with remarkable improvements in key metrics compared to both budget projections and prior periods. Net Operating Income (NOI) has increased significantly, driven by substantial revenue growth and effective expense management.

## Revenue Analysis

Gross Potential Rent (GPR) has increased by 15.2% compared to the prior month, reflecting successful implementation of planned rent increases and strong market conditions. Vacancy loss has decreased by 18.3% compared to budget, indicating improved occupancy rates and highly effective leasing strategies. Other income sources have also performed exceptionally well, showing a 12.7% increase primarily driven by higher parking and amenity fee collections.

## Expense Management

Operating expenses have been exceptionally well-managed, remaining 7.2% under budget for the period. Utilities showed the largest savings at 9.8% below the budgeted amount, due to efficiency improvements implemented last quarter. Property taxes and insurance remained stable and in line with budget expectations.

## NOI Performance

The combination of strong revenue growth and disciplined expense control has resulted in a 22.4% improvement in NOI compared to the same period last year. This significantly exceeds the portfolio average of 5.2% and places this property among the top performers in the entire portfolio.

## Outlook and Recommendations

Based on current trends, we expect continued strong performance in the coming months. We recommend:

1. Considering accelerated rent increases given the strong market performance
2. Evaluating expansion opportunities or capital improvements
3. Implementing successful expense control measures across other properties
4. Reviewing staffing levels to ensure service quality keeps pace with growth
5. Developing strategies to maintain this growth trajectory

Overall, the property is significantly exceeding annual performance targets and represents a model for other properties in the portfolio.
"""
    elif scenario == "Declining Performance":
        return """
# Financial Performance Narrative: Declining Performance

## Overview

The property has demonstrated concerning financial performance this period, with notable deterioration in key metrics compared to both budget projections and prior periods. Net Operating Income (NOI) has decreased significantly, impacted by revenue declines and expense increases.

## Revenue Analysis

Gross Potential Rent (GPR) has decreased by 8.3% compared to the prior month, reflecting challenging market conditions and potential competitive pressures. Vacancy loss has increased by 12.5% compared to budget, indicating occupancy challenges and potential tenant retention issues. Other income sources have also underperformed, showing a 6.8% decrease primarily due to lower parking and amenity fee collections.

## Expense Management

Operating expenses have exceeded budget by 5.7% for the period. Repairs and maintenance showed the largest variance at 15.3% above the budgeted amount, due to several unexpected maintenance issues. Property taxes and insurance remained stable but other controllable expenses also showed concerning increases.

## NOI Performance

The combination of revenue declines and expense increases has resulted in a 13.2% decrease in NOI compared to the same period last year. This falls significantly below the portfolio average of 3.5% growth and places this property among the underperformers in the portfolio.

## Outlook and Recommendations

Based on current trends, immediate intervention is required to address performance issues. We recommend:

1. Conducting a comprehensive market analysis to understand competitive pressures
2. Implementing an aggressive leasing campaign to address rising vacancy
3. Reviewing and optimizing expense management practices
4. Considering property improvements to enhance competitiveness
5. Developing a detailed action plan with specific milestones

Overall, the property requires immediate attention to reverse negative performance trends and return to meeting performance targets.
"""
    elif scenario == "Budget Variance":
        return """
# Financial Performance Narrative: Budget Variance

## Overview

The property has demonstrated mixed financial performance this period, with significant variances from budget projections in several key metrics. While some areas exceed expectations, others fall short, suggesting a need for more accurate forecasting methodologies.

## Revenue Analysis

Gross Potential Rent (GPR) is 4.2% below budget projections, indicating overly optimistic revenue forecasting in the budgeting process. However, vacancy loss is 8.7% better than budget, suggesting conservative occupancy projections. Other income sources are performing 12.3% above budget, primarily due to unexpected increases in parking and storage fees that weren't fully accounted for in projections.

## Expense Management

Operating expenses are 3.5% over budget for the period. Utilities and repairs showed the largest variances, with utilities 5.2% over budget due to rate increases not fully captured in forecasts, and repairs 7.8% over budget due to several unplanned maintenance issues. Property taxes and insurance remained in line with budget expectations.

## NOI Performance

The combination of revenue shortfalls and expense overages has resulted in NOI being 7.8% below budget despite being 3.2% above prior year. This indicates a significant forecasting gap that needs to be addressed in future budgeting cycles.

## Outlook and Recommendations

Based on current trends and variance analysis, we recommend:

1. Reviewing budgeting methodology to improve accuracy of projections
2. Implementing monthly variance analysis to identify trends earlier
3. Adjusting current year expectations based on actual performance
4. Developing more detailed category-level budgets
5. Considering a rolling forecast approach to improve adaptability

Overall, while the property is performing adequately compared to prior periods, the significant budget variances indicate a need for improved forecasting and more frequent performance monitoring.
"""
    else:  # Standard Performance
        return """
# Financial Performance Narrative: Standard Performance

## Overview

The property has demonstrated stable financial performance this period, with modest improvements in key metrics compared to both budget projections and prior periods. Net Operating Income (NOI) has increased moderately, driven by balanced revenue growth and effective expense management.

## Revenue Analysis

Gross Potential Rent (GPR) has increased by 5.2% compared to the prior month, reflecting successful implementation of planned rent increases and stable market conditions. Vacancy loss has decreased by 3.8% compared to budget, indicating healthy occupancy rates and effective leasing strategies. Other income sources have also performed well, showing a 3.5% increase primarily driven by parking and laundry revenue.

## Expense Management

Operating expenses have been well-managed, remaining 2.1% under budget for the period. Utilities showed modest savings at 3.2% below the budgeted amount, likely due to normal seasonal variations and ongoing efficiency measures. Property taxes and insurance remained stable and in line with budget expectations.

## NOI Performance

The combination of steady revenue growth and disciplined expense control has resulted in a 4.7% improvement in NOI compared to the same period last year. This is slightly below the portfolio average of 5.2% but represents solid, consistent performance.

## Outlook and Recommendations

Based on current trends, we expect continued stable performance in the coming months. We recommend:

1. Continuing current operational strategies given the stable metrics
2. Considering modest rent increases aligned with market conditions
3. Evaluating opportunities for incremental expense reductions
4. Implementing targeted marketing to further reduce vacancy
5. Developing strategies to increase other income sources

Overall, the property is on track to meet annual performance targets if current trends continue.
""" 