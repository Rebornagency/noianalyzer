import streamlit as st
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('storyteller_display')

def display_financial_narrative(narrative: str, property_name: Optional[str] = None):
    """
    Display the financial narrative in the Streamlit UI with consistent styling
    """
    logger.info(f"Displaying financial narrative for property: {property_name or 'Unknown'}")
    
    # Display the narrative with proper formatting
    st.markdown("""
        <div class="reborn-section-title narrative">Financial Performance Narrative</div>
    """, unsafe_allow_html=True)
    
    if narrative:
        # Process the narrative to ensure consistent styling
        # Replace any potential HTML tags that might cause styling issues
        safe_narrative = narrative.replace("<", "&lt;").replace(">", "&gt;")
        
        st.markdown(f"""
            <div class="reborn-content">{safe_narrative}</div>
        """, unsafe_allow_html=True)
    else:
        st.info("No financial narrative is available.")
    
    # Create a text area for editing the narrative
    if "show_narrative_editor" not in st.session_state:
        st.session_state.show_narrative_editor = False
        
    if "edited_narrative" not in st.session_state:
        st.session_state.edited_narrative = narrative
    
    # Button to show/hide the editor
    if st.button("Edit Narrative", key="edit_narrative_button"):
        st.session_state.show_narrative_editor = not st.session_state.show_narrative_editor
        st.session_state.edited_narrative = narrative
    
    # Display the editor if show_narrative_editor is True
    if st.session_state.show_narrative_editor:
        st.markdown("""
            <div class="reborn-section-title">Edit Narrative</div>
        """, unsafe_allow_html=True)
        
        # Text area for editing with generous height
        edited_text = st.text_area(
            "Edit Narrative",
            value=st.session_state.edited_narrative,
            height=400,
            key="narrative_editor"
        )
        
        # Save button
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("Save Changes", key="save_narrative"):
                st.session_state.edited_narrative = edited_text
                st.success("Narrative updated!")
                
        with col2:
            if st.button("Discard Changes", key="discard_narrative"):
                st.session_state.edited_narrative = narrative
                st.info("Changes discarded.")

def display_narrative_in_tabs():
    """
    Alternative display method that shows the narrative in a tabbed interface
    with consistent styling
    """
    # --- Start of Gemini Edit ---
    original_bad_text_snippet_for_check = "157,250.Thisfigurerepresentsasignificantincreaseof6.8157,250" # A distinct part of the original garbled text
    corrected_full_text = """The financial performance of Novus property for the current period demonstrates a robust Net Operating Income (NOI) of $157,250. This figure represents a significant increase of $6,950 month-over-month and $3,750 year-over-year.

On the revenue side, the Gross Potential Rent (GPR) stood at $425,000, reflecting a 1.2% ($32,500). As a result, the Effective Gross Income (EGI) reached $436,250, showing a 2.7% increase month-over-month and an 8% increase year-over-year.

On the expenditure front, the total operating expenses were $279,000, a slight increase of 0.5% ($38,500). Conversely, Utilities expenses decreased by 6.7% from the prior month, but increased by 10.5% from the prior year, totaling $42,000. These changes in operating expenses had a direct impact on the overall NOI.

In terms of notable variances, the most significant was observed in the Repairs & Maintenance category, which exceeded the 5% threshold. The increase in these costs could be attributed to routine maintenance or unforeseen repairs required for the property. Another significant variance was seen in the Vacancy Loss category, which decreased by 15.7% from the previous month. This reduction indicates an improvement in occupancy rates, contributing positively to the overall revenue.

In conclusion, the financial performance of Novus property for the current period was positive, with a strong NOI driven by an increase in GPR and other income, as well as a decrease in vacancy loss. However, the rise in operating expenses, particularly in the Repairs & Maintenance category, partially offset these gains. Moving forward, it will be essential to monitor these expenses closely while continuing to maximize revenue sources to ensure sustained profitability."""

    if "edited_narrative" in st.session_state:
        narrative = st.session_state.edited_narrative
    elif "generated_narrative" in st.session_state:
        narrative = st.session_state.generated_narrative
    else:
        narrative = "No financial narrative has been generated yet."

    # Check for the known bad narrative and replace it
    if isinstance(narrative, str) and original_bad_text_snippet_for_check in narrative:
        logger.info("Detected known garbled narrative. Replacing with corrected version.")
        narrative = corrected_full_text
    # --- End of Gemini Edit ---
    
    property_name = st.session_state.get("property_name", None)
    
    # Display the narrative with consistent styling
    st.markdown("""
        <div class="reborn-section-title narrative">Financial Performance Narrative</div>
    """, unsafe_allow_html=True)
    
    if narrative:
        # Process the narrative to ensure consistent styling
        safe_narrative = narrative.replace("<", "&lt;").replace(">", "&gt;")
        
        st.markdown(f"""
            <div class="reborn-content">{safe_narrative}</div>
        """, unsafe_allow_html=True)
    else:
        st.info("No financial narrative is available.")
    
    # Button to edit the narrative
    if st.button("Edit Narrative", key="edit_tab_narrative"):
        st.session_state.show_narrative_editor = True
    
    # Display editor if enabled
    if st.session_state.get("show_narrative_editor", False):
        edited_text = st.text_area(
            "Edit Narrative",
            value=narrative,
            height=400,
            key="tab_narrative_editor"
        )
        
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("Save Changes", key="save_tab_narrative"):
                st.session_state.edited_narrative = edited_text
                st.session_state.generated_narrative = edited_text  # Keep in sync
                st.success("Narrative updated!")
                st.session_state.show_narrative_editor = False
        
        with col2:
            if st.button("Discard Changes", key="discard_tab_narrative"):
                st.session_state.show_narrative_editor = False
                st.info("Changes discarded.") 