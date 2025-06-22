import streamlit as st
import math

def format_financial_change_universal(value, comparison_type="change", is_percentage=False):
    if value is None or math.isinf(value) or math.isnan(value):
        value = 0
    if value > 0:
        css_class = f"{comparison_type}-positive"
        prefix = "+" if not is_percentage else "+"
        suffix = "%" if is_percentage else ""
    elif value < 0:
        css_class = f"{comparison_type}-negative"
        prefix = ""
        suffix = "%" if is_percentage else ""
    else:
        css_class = f"{comparison_type}-neutral"
        prefix = ""
        suffix = "%" if is_percentage else ""
    if is_percentage:
        formatted_value = f"{value:.1f}"
    else:
        formatted_value = f"{value:,.0f}"
    return f'<span class="{css_class} {"percentage-value" if is_percentage else "currency-value"}">{prefix}{formatted_value}{suffix}</span>'

def format_currency_value_universal(value):
    if value is None or math.isinf(value) or math.isnan(value):
        return f'<span class="currency-value">/A</span>'
    return f'<span class="currency-value"></span>'

def create_prior_month_comparison_table_html(data):
    html = '''
    <div class="prior-month-table-container">
        <table class="prior-month-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Current</th>
                    <th>Prior Month</th>
                    <th class="change-dollar-column">Change ($)</th>
                    <th class="change-percent-column">Change (%)</th>
                </tr>
            </thead>
            <tbody>
    '''
    for row in data:
        metric_name = row['metric']
        current_value = format_currency_value_universal(row['current'])
        prior_value = format_currency_value_universal(row['prior'])
        change_dollar = format_financial_change_universal(row['change_dollar'], "change", is_percentage=False)
        change_percent = format_financial_change_universal(row['change_percent'], "change", is_percentage=True)
        html += f'''
                <tr>
                    <td>{metric_name}</td>
                    <td>{current_value}</td>
                    <td>{prior_value}</td>
                    <td class="change-dollar-column">{change_dollar}</td>
                    <td class="change-percent-column">{change_percent}</td>
                </tr>
        '''
    html += '''
            </tbody>
        </table>
    </div>
    '''
    return html

def create_budget_comparison_table_html(data):
    html = '''
    <div class="budget-comparison-table-container">
        <table class="budget-comparison-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Actual</th>
                    <th>Budget</th>
                    <th class="variance-dollar-column">Variance ($)</th>
                    <th class="variance-percent-column">Variance (%)</th>
                </tr>
            </thead>
            <tbody>
    '''
    for row in data:
        metric_name = row['metric']
        actual_value = format_currency_value_universal(row['actual'])
        budget_value = format_currency_value_universal(row['budget'])
        variance_dollar = format_financial_change_universal(row['variance_dollar'], "variance", is_percentage=False)
        variance_percent = format_financial_change_universal(row['variance_percent'], "variance", is_percentage=True)
        html += f'''
                <tr>
                    <td>{metric_name}</td>
                    <td>{actual_value}</td>
                    <td>{budget_value}</td>
                    <td class="variance-dollar-column">{variance_dollar}</td>
                    <td class="variance-percent-column">{variance_percent}</td>
                </tr>
        '''
    html += '''
            </tbody>
        </table>
    </div>
    '''
    return html

def create_prior_year_comparison_table_html(data):
    html = '''
    <div class="prior-year-comparison-table-container">
        <table class="prior-year-comparison-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Current Year</th>
                    <th>Prior Year</th>
                    <th class="growth-dollar-column">Growth ($)</th>
                    <th class="growth-percent-column">Growth (%)</th>
                </tr>
            </thead>
            <tbody>
    '''
    for row in data:
        metric_name = row['metric']
        current_value = format_currency_value_universal(row['current'])
        prior_year_value = format_currency_value_universal(row['prior_year'])
        growth_dollar = format_financial_change_universal(row['growth_dollar'], "growth", is_percentage=False)
        growth_percent = format_financial_change_universal(row['growth_percent'], "growth", is_percentage=True)
        html += f'''
                <tr>
                    <td>{metric_name}</td>
                    <td>{current_value}</td>
                    <td>{prior_year_value}</td>
                    <td class="growth-dollar-column">{growth_dollar}</td>
                    <td class="growth-percent-column">{growth_percent}</td>
                </tr>
        '''
    html += '''
            </tbody>
        </table>
    </div>
    '''
    return html

def load_custom_css_universal():
    css_file = "static/css/reborn_theme.css"
    try:
        with open(css_file, 'r') as f:
            css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Error: The stylesheet {css_file} was not found. Please ensure it exists in the correct directory.")

def render_navigation_with_search_universal():
    col1, col2 = st.columns([6, 1])
    with col1:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Prior Month", "Budget", "Prior Year", "Summary", "NOI Coach"
        ])
    with col2:
        st.markdown('''
            <div class="nav-search-container">
                <svg class="nav-search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
            </div>
        ''', unsafe_allow_html=True)
    return tab1, tab2, tab3, tab4, tab5

def transform_data_for_view(source_data, comparison_type):
    metrics = {
        'GPR': 'gpr', 'Vacancy': 'vacancy', 'EGI': 'egi', 
        'OpEx': 'opex', 'NOI': 'noi'
    }
    table_data = []
    for display_name, data_key in metrics.items():
        row = {'metric': display_name}
        if comparison_type == "prior_month":
            row['current'] = source_data.get(f'{data_key}_current', 0)
            row['prior'] = source_data.get(f'{data_key}_prior', 0)
            row['change_dollar'] = source_data.get(f'{data_key}_change_dollar', 0)
            row['change_percent'] = source_data.get(f'{data_key}_change_percent', 0)
        elif comparison_type == "budget":
            row['actual'] = source_data.get(f'{data_key}_actual', 0)
            row['budget'] = source_data.get(f'{data_key}_budget', 0)
            row['variance_dollar'] = source_data.get(f'{data_key}_variance_dollar', 0)
            row['variance_percent'] = source_data.get(f'{data_key}_variance_percent', 0)
        elif comparison_type == "prior_year":
            row['current'] = source_data.get(f'{data_key}_current', 0)
            row['prior_year'] = source_data.get(f'{data_key}_prior_year', 0)
            row['growth_dollar'] = source_data.get(f'{data_key}_growth_dollar', 0)
            row['growth_percent'] = source_data.get(f'{data_key}_growth_percent', 0)
        table_data.append(row)
    return table_data

def render_comparison_view_universal(tab, comparison_type, data):
    with tab:
        table_data = transform_data_for_view(data, comparison_type)
        if comparison_type == "prior_month":
            st.markdown("## Current Month vs. Prior Month", unsafe_allow_html=True)
            table_html = create_prior_month_comparison_table_html(table_data)
        elif comparison_type == "budget":
            st.markdown("## Current Month vs. Budget", unsafe_allow_html=True)
            table_html = create_budget_comparison_table_html(table_data)
        elif comparison_type == "prior_year":
            st.markdown("## Current Month vs. Prior Year", unsafe_allow_html=True)
            table_html = create_prior_year_comparison_table_html(table_data)
        else:
            table_html = "<div>Invalid comparison type</div>"
        st.markdown(table_html, unsafe_allow_html=True)
