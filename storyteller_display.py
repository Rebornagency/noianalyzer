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
    Display the financial narrative in the tabs interface with editing capability.
    """
    logger.info("Displaying financial narrative in tabs")
    
    # Check if narrative exists in session state
    has_narrative = (
        "generated_narrative" in st.session_state and 
        st.session_state.generated_narrative and 
        isinstance(st.session_state.generated_narrative, str)
    )
    
    # Log narrative status
    if has_narrative:
        narrative_snippet = st.session_state.generated_narrative[:100] + "..." if len(st.session_state.generated_narrative) > 100 else st.session_state.generated_narrative
        logger.info(f"Found narrative in session state (snippet): {narrative_snippet}")
    else:
        logger.info("No narrative found in session state or narrative is empty")
    
    # Display the narrative
    st.markdown("""
        <div class="reborn-section-title financial-narrative">Financial Performance Narrative</div>
    """, unsafe_allow_html=True)
    
    if has_narrative:
        # MODIFIED: Remove the expander and display directly to avoid redundant title
        # Process the narrative to ensure consistent styling by removing any potential HTML elements
        narrative_text = st.session_state.generated_narrative.replace("<", "&lt;").replace(">", "&gt;")
        
        # Ensure consistent styling by wrapping in a div with specific styling
        st.markdown(f"""
            <div class="reborn-content narrative-text" style="
                color: #E0E0E0; 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 1rem;
                line-height: 1.6;
                background-color: rgba(30, 41, 59, 0.8);
                padding: 1rem;
                border-radius: 6px;
                margin-bottom: 1rem;
            ">
                {narrative_text}
            </div>
        """, unsafe_allow_html=True)
        
        # Add edit button
        if st.button("Edit Narrative", key="edit_narrative_btn"):
            st.session_state.show_narrative_editor = True
        
        # Show editor if requested
        if "show_narrative_editor" in st.session_state and st.session_state.show_narrative_editor:
            st.subheader("Edit Narrative")
            edited_narrative = st.text_area(
                "Edit the financial narrative below:",
                value=st.session_state.generated_narrative,
                height=300,
                key="narrative_editor_tab" # Changed key to avoid conflict if another editor exists
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Changes", key="save_narrative_btn"):
                    st.session_state.edited_narrative = edited_narrative
                    st.session_state.generated_narrative = edited_narrative # Keep generated in sync if edited
                    st.session_state.show_narrative_editor = False
                    st.success("Narrative updated successfully!")
                    st.rerun()
            with col2:
                if st.button("Cancel", key="cancel_narrative_btn"):
                    st.session_state.show_narrative_editor = False
                    st.rerun()
    else:
        st.info("No financial narrative has been generated yet. Process documents to generate a narrative.") 