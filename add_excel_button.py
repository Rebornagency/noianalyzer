#!/usr/bin/env python3
"""
Script to add Excel export button to app.py
"""

import os
import re

# Read the app.py file
app_file_path = 'app.py'
with open(app_file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if the Excel button is already there
if 'Export Excel' in content and 'global_excel_export' in content:
    print("Excel export button already exists in app.py")
    exit(0)

# Find the PDF export section and add the Excel button after it
pdf_section_pattern = r'''(col_pdf, col_spacer = st\.columns\$$1,7\$$\s+
\s+with col_pdf:\s+
\s+# PDF Export button with loading state - ensure consistent styling\s+
\s+pdf_clicked, pdf_button_placeholder = create_loading_button\([^)]+\)\s+
\s+if pdf_clicked:\s+
\s+# Show loading state immediately\s+
\s+show_button_loading\([^)]+\)\s+
\s+# Get loading message for PDF generation\s+
\s+loading_msg, loading_subtitle = get_loading_message_for_action\([^)]+\)\s+
\s+# Show loading indicator\s+
\s+loading_container = st\.empty\(\)\s+
\s+with loading_container\.container\(\):\s+
\s+display_loading_spinner\([^)]+\)\s+
\s+try:\s+
\s+pdf_bytes = generate_comprehensive_pdf\(\)\s+
\s+if pdf_bytes:\s+
\s+# Create a unique filename with timestamp\s+
\s+timestamp = datetime\.now\(\)\.strftime\([^)]+\)\s+
\s+property_part = [^}]+\s+
\s+# Clear loading states\s+
\s+loading_container\.empty\(\)\s+
\s+restore_button\([^)]+\)\s+
\s+# Check if we have HTML content \(fallback\) or PDF content\s+
\s+if not WEASYPRINT_AVAILABLE and pdf_bytes and b'<!DOCTYPE html>' in pdf_bytes\$$:50\$$:\s+
\s+# We have HTML content \(fallback case\)\s+
\s+html_filename = [^}]+\s+
\s+st\.download_button\([^)]+\)\s+
\s+st\.info\([^)]+\)\s+
\s+elif WEASYPRINT_AVAILABLE and pdf_bytes:\s+
\s+# We have actual PDF content\s+
\s+pdf_filename = [^}]+\s+
\s+st\.download_button\([^)]+\)\s+
\s+# Show success message\s+
\s+show_processing_status\([^)]+\)\s+
\s+else:\s+
\s+# Handle case where pdf_bytes is None or empty\s+
\s+st\.error\([^)]+\)\s+
\s+else:\s+
\s+# Clear loading states on failure\s+
\s+loading_container\.empty\(\)\s+
\s+restore_button\([^)]+\)\s+
\s+st\.info\([^)]+\)\s+
\s+except Exception as e:\s+
\s+# Clear loading states on failure\s+
\s+loading_container\.empty\(\)\s+
\s+restore_button\([^)]+\)\s+
\s+st\.info\([^)]+\)\s+
\s+logger\.error\([^)]+\))'''

# Replacement text with both PDF and Excel buttons side by side
replacement_text = r'''\1

        # Add Excel Export button
        st.markdown("---")
        excel_clicked, excel_button_placeholder = create_loading_button(
            "Export Excel",
            key="global_excel_export",
            help="Export comparison data to Excel format",
            type="primary",
            use_container_width=True
        )
        
        if excel_clicked:
            # Show loading state immediately
            show_button_loading(excel_button_placeholder, "Generating Excel...")
            
            # Get loading message for Excel generation
            loading_msg, loading_subtitle = get_loading_message_for_action("generate_excel")
            
            # Show loading indicator
            loading_container = st.empty()
            with loading_container.container():
                display_loading_spinner(loading_msg, loading_subtitle)
            
            try:
                excel_bytes = generate_comparison_excel()
                if excel_bytes:
                    # Create a unique filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    property_part = st.session_state.property_name.replace(" ", "_") if hasattr(st.session_state, 'property_name') and st.session_state.property_name else "Property"
                    
                    # Clear loading states
                    loading_container.empty()
                    restore_button(excel_button_placeholder, "Export Excel", key="global_excel_export_success", type="primary", use_container_width=True)
                    
                    # We have Excel content
                    excel_filename = f"NOI_Comparison_{property_part}_{timestamp}.xlsx"
                    st.download_button(
                        label="📥 Download Excel Report",
                        data=excel_bytes,
                        file_name=excel_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"download_excel_report_{timestamp}",
                        type="primary",
                        use_container_width=True
                    )
                    # Show success message
                    show_processing_status("Excel report generated successfully!", status_type="success")
                else:
                    # Clear loading states on failure
                    loading_container.empty()
                    restore_button(excel_button_placeholder, "Export Excel", key="global_excel_export_failure", type="primary", use_container_width=True)
                    st.error("❌ Failed to generate Excel report. Please try again or contact support.")
            except Exception as e:
                # Clear loading states on failure
                loading_container.empty()
                restore_button(excel_button_placeholder, "Export Excel", key="global_excel_export_error", type="primary", use_container_width=True)
                st.error(f"🔧 Excel generation encountered an issue: {str(e)}")
                logger.error(f"Excel generation error: {str(e)}", exc_info=True)'''

# Apply the replacement
new_content = re.sub(pdf_section_pattern, replacement_text, content, flags=re.DOTALL)

# Write the modified content back to the file
with open(app_file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully added Excel export button to app.py")