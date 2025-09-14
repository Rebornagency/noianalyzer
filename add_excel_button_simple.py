#!/usr/bin/env python3
"""
Simple script to add Excel export button to app.py
"""

# Read the app.py file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if the Excel button is already there
if 'Export Excel' in content and 'global_excel_export' in content:
    print("Excel export button already exists in app.py")
    exit(0)

# Find the exact location to insert the Excel button
insert_after = '''                    logger.error(f"PDF generation error: {str(e)}")'''

excel_button_code = '''
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

# Insert the Excel button code
if insert_after in content:
    content = content.replace(insert_after, insert_after + excel_button_code)
    
    # Write the modified content back to the file
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Successfully added Excel export button to app.py")
else:
    print("Could not find the location to insert the Excel button")
    exit(1)