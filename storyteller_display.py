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
    if "edited_narrative" in st.session_state:
        narrative = st.session_state.edited_narrative
    elif "generated_narrative" in st.session_state:
        narrative = st.session_state.generated_narrative
    else:
        narrative = "No financial narrative has been generated yet."
    
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