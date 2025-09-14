import streamlit as st
import logging
import io
import xlsxwriter
from datetime import datetime
from constants import MAIN_METRICS, OPEX_COMPONENTS, INCOME_COMPONENTS

# Configure logging
logger = logging.getLogger('noi_analyzer')

def generate_comparison_excel():
    """
    Generate an Excel file containing only the structured numerical comparison data.
    
    Returns:
        bytes: Excel file as bytes if successful, None otherwise
    """
    logger.info("EXCEL EXPORT: Generating comparison Excel with numerical data only")
    
    try:
        # Verify we have the necessary data
        if not hasattr(st.session_state, 'comparison_results') or not st.session_state.comparison_results:
            logger.error("EXCEL EXPORT: No comparison results found in session state")
            return None
            
        # Get property name
        property_name = st.session_state.property_name if hasattr(st.session_state, 'property_name') and st.session_state.property_name else "Property"
        
        # Create Excel workbook in memory
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#3B82F6',  # Blue background
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        metric_format = workbook.add_format({
            'bold': True,
            'font_color': '#1E40AF',  # Dark blue for metric names
            'bg_color': '#EFF6FF',    # Light blue background
            'font_size': 10,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1
        })
        
        number_format = workbook.add_format({
            'font_size': 10,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '$#,##0.00'
        })
        
        percent_format = workbook.add_format({
            'font_size': 10,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '0.00%'
        })
        
        # Create worksheets for each comparison type
        comparison_types = [
            ('month_vs_prior', 'Month vs Prior'),
            ('actual_vs_budget', 'Actual vs Budget'),
            ('year_vs_year', 'Year vs Year')
        ]
        
        for comparison_key, sheet_name in comparison_types:
            if comparison_key not in st.session_state.comparison_results or not st.session_state.comparison_results[comparison_key]:
                continue
                
            worksheet = workbook.add_worksheet(sheet_name[:31])  # Excel sheet names limited to 31 chars
            comparison_data = st.session_state.comparison_results[comparison_key]
            
            # Write headers
            headers = ['Metric', 'Current Period', 'Comparison Period', 'Difference', 'Percent Change']
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
            
            # Write data rows
            row = 1
            metrics = MAIN_METRICS + OPEX_COMPONENTS + INCOME_COMPONENTS
            
            for metric in metrics:
                # Check if this metric exists in the data
                current_key = f"{metric}_current"
                compare_suffix = 'prior' if comparison_key == 'month_vs_prior' else 'budget' if comparison_key == 'actual_vs_budget' else 'prior_year'
                compare_key = f"{metric}_{compare_suffix}"
                change_suffix = 'change' if comparison_key != 'actual_vs_budget' else 'variance'
                change_key = f"{metric}_{change_suffix}"
                pct_change_suffix = 'percent_change' if comparison_key != 'actual_vs_budget' else 'percent_variance'
                pct_change_key = f"{metric}_{pct_change_suffix}"
                
                # Only add row if at least one value exists
                if any(key in comparison_data for key in [current_key, compare_key, change_key, pct_change_key]):
                    current_val = comparison_data.get(current_key, 0)
                    compare_val = comparison_data.get(compare_key, 0)
                    change_val = comparison_data.get(change_key, 0)
                    pct_change_val = comparison_data.get(pct_change_key, 0)
                    
                    # Write metric name
                    worksheet.write(row, 0, metric.replace('_', ' ').title(), metric_format)
                    
                    # Write values
                    worksheet.write(row, 1, current_val, number_format)
                    worksheet.write(row, 2, compare_val, number_format)
                    worksheet.write(row, 3, change_val, number_format)
                    
                    # Write percentage change (convert to decimal for proper formatting)
                    if isinstance(pct_change_val, (int, float)):
                        worksheet.write(row, 4, pct_change_val / 100, percent_format)
                    else:
                        worksheet.write(row, 4, 0, percent_format)
                    
                    row += 1
            
            # Auto-adjust column widths
            worksheet.set_column('A:A', 25)  # Metric names
            worksheet.set_column('B:E', 15)  # Values
            
        # Create a summary worksheet
        summary_worksheet = workbook.add_worksheet('Summary')
        
        # Write summary headers
        summary_headers = ['Metric', 'Current Period', 'Prior Month', 'Budget', 'Prior Year']
        for col, header in enumerate(summary_headers):
            summary_worksheet.write(0, col, header, header_format)
        
        # Write summary data
        row = 1
        for metric in MAIN_METRICS:
            summary_worksheet.write(row, 0, metric.replace('_', ' ').title(), metric_format)
            
            # Get values from each period
            current_val = st.session_state.comparison_results.get('current', {}).get(metric, 0)
            prior_val = st.session_state.comparison_results.get('prior', {}).get(metric, 0)
            budget_val = st.session_state.comparison_results.get('budget', {}).get(metric, 0)
            prior_year_val = st.session_state.comparison_results.get('prior_year', {}).get(metric, 0)
            
            # Write values
            summary_worksheet.write(row, 1, current_val, number_format)
            summary_worksheet.write(row, 2, prior_val, number_format)
            summary_worksheet.write(row, 3, budget_val, number_format)
            summary_worksheet.write(row, 4, prior_year_val, number_format)
            
            row += 1
        
        # Auto-adjust column widths for summary
        summary_worksheet.set_column('A:A', 25)
        summary_worksheet.set_column('B:E', 15)
        
        # Close workbook
        workbook.close()
        
        # Get the Excel data
        excel_data = output.getvalue()
        logger.info("EXCEL EXPORT: Excel file generated successfully")
        return excel_data
        
    except Exception as e:
        logger.error(f"EXCEL EXPORT: Error generating Excel file: {str(e)}", exc_info=True)
        return None