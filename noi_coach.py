import streamlit as st
import logging
import random
from typing import List, Dict, Any, Optional

# Import loading functions
try:
    from utils.ui_helpers import (
        display_loading_spinner, display_inline_loading, 
        get_loading_message_for_action, LoadingContext
    )
except ImportError:
    # Fallback functions if ui_helpers is not available
    def display_loading_spinner(message, subtitle=None):
        st.info(f"{message} {subtitle or ''}")
    def display_inline_loading(message, icon="⏳"):
        st.info(f"{icon} {message}")
    def get_loading_message_for_action(action, file_count=1):
        return "Processing...", "Please wait..."

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('noi_coach')

# Example prompts to help users get started
EXAMPLE_PROMPTS = [
    "What strategies can I use to reduce vacancy rates?",
    "How can I optimize my property's operating expenses?",
    "What are industry benchmarks for NOI in multifamily properties?",
    "How do I analyze year-over-year NOI performance?",
    "What's a good cap rate for commercial properties in today's market?",
    "How can I improve my property's cash flow?",
    "What metrics should I track to evaluate property manager performance?",
    "How do I calculate and interpret debt service coverage ratio?",
    "What are effective strategies to increase rental income?",
    "How should I prioritize capital improvements to maximize ROI?"
]

def initialize_chat_history():
    """Initialize the chat history in session state if it doesn't exist"""
    if "noi_coach_messages" not in st.session_state:
        st.session_state.noi_coach_messages = []
        
    if "noi_coach_context" not in st.session_state:
        st.session_state.noi_coach_context = "general"

def add_message(role: str, content: str):
    """Add a message to the chat history"""
    st.session_state.noi_coach_messages.append({"role": role, "content": content})

def generate_response(prompt: str, context: str) -> str:
    """
    Generate a response to the user's prompt based on the selected context
    
    Args:
        prompt: The user's question or prompt
        context: The selected context (general, residential, commercial, etc.)
        
    Returns:
        A string containing the AI-generated response
    """
    try:
        # In a real implementation, this would call an AI service
        # For now, we'll return placeholder responses based on context
        
        # Log the request
        logger.info(f"Generating NOI Coach response for prompt: '{prompt}' with context: {context}")
        
        # Simple context-based responses
        if "vacancy" in prompt.lower():
            if context == "residential":
                return "For residential properties, reducing vacancy rates often involves improving curb appeal, offering competitive rent prices, implementing resident referral programs, and ensuring quick turnaround on unit preparation between tenants. Consider upgrading high-visibility amenities and investing in professional photography for listings."
            elif context == "commercial":
                return "For commercial properties, reducing vacancy rates typically requires a multi-faceted approach: work with specialized brokers familiar with your market, consider tenant improvement allowances to attract quality businesses, offer flexible lease terms for new tenants, and develop a targeted marketing strategy highlighting your property's unique advantages for business operations."
            else:
                return "To reduce vacancy rates, focus on competitive pricing, property improvements, effective marketing, and responsive property management. Regular market analysis can help you stay ahead of trends and adjust your strategy accordingly."
                
        elif "operating expenses" in prompt.lower() or "opex" in prompt.lower():
            return "To optimize operating expenses, consider: 1) Conducting regular energy audits and implementing efficiency upgrades, 2) Rebidding service contracts annually, 3) Implementing preventative maintenance programs to reduce emergency repairs, 4) Analyzing utility consumption patterns to identify waste, and 5) Considering bulk purchasing for supplies across multiple properties if applicable."
            
        elif "benchmark" in prompt.lower():
            if context == "residential":
                return "For residential multifamily properties, NOI benchmarks typically range from 60-75% of Effective Gross Income (EGI), though this varies significantly by market, property class, and age. Class A properties in prime markets might achieve NOI margins of 70-75%, while Class C properties might operate at 55-65% of EGI."
            elif context == "commercial":
                return "Commercial property NOI benchmarks vary widely by property type. Office buildings typically target NOI of 65-75% of EGI, retail properties 65-70%, and industrial properties 70-80%. Location, class, and tenant quality significantly impact these ranges."
            else:
                return "Industry NOI benchmarks typically range from 60-75% of Effective Gross Income, varying by property type, class, location, and market conditions. It's best to compare your property against similar properties in your specific submarket for the most relevant benchmarks."
        
        # Generic response if no keywords match
        else:
            return "That's an excellent question about property financial management. To provide the most accurate guidance, I'd recommend analyzing your specific property data and market conditions. Generally, successful property investors focus on maximizing revenue while controlling expenses, maintaining appropriate reserves for capital expenditures, and regularly reviewing performance against both historical data and market benchmarks."
            
    except Exception as e:
        logger.error(f"Error generating NOI Coach response: {str(e)}", exc_info=True)
        return "I apologize, but I encountered an error processing your question. Please try again or rephrase your question."

def display_noi_coach():
    """Display the NOI Coach interface"""
    st.success("Enhanced NOI Coach Loaded!") # Temporary message for testing
    st.markdown("## NOI Coach")
    
    # Initialize chat history if needed
    initialize_chat_history()
    
    # Create a container for the entire NOI Coach interface
    with st.container():
        # Context selector
        st.markdown("### Property Context")
        context_options = {
            "general": "General Advice",
            "residential": "Residential Properties",
            "commercial": "Commercial Properties",
            "mixed_use": "Mixed-Use Properties"
        }
        
        selected_context = st.radio(
            "Select the property context for more relevant advice:",
            options=list(context_options.keys()),
            format_func=lambda x: context_options[x],
            index=list(context_options.keys()).index(st.session_state.noi_coach_context),
            horizontal=True,
            key="noi_coach_context_selector"
        )
        
        # Update the context in session state if changed
        if selected_context != st.session_state.noi_coach_context:
            st.session_state.noi_coach_context = selected_context
        
        # Instructions
        with st.expander("Instructions & Tips", expanded=False):
            st.markdown("""
            ### How to Use NOI Coach
            
            NOI Coach is your virtual assistant for property financial management advice. Here's how to get the most out of it:
            
            1. **Select the appropriate property context** above to receive more tailored advice
            2. **Ask specific questions** about NOI analysis, property performance, or financial strategies
            3. **Provide relevant details** like property type, size, or location for more personalized guidance
            4. **Try the example prompts** below if you're not sure where to start
            
            NOI Coach works best when your questions are clear and focused on specific aspects of property financial management.
            """)
        
        # Example prompts
        st.markdown("### Example Questions")
        
        # Display example prompts in a grid
        cols = st.columns(2)
        random_prompts = random.sample(EXAMPLE_PROMPTS, min(6, len(EXAMPLE_PROMPTS)))
        
        for i, prompt in enumerate(random_prompts):
            with cols[i % 2]:
                if st.button(prompt, key=f"example_prompt_{i}", use_container_width=True):
                    # Add the example prompt as a user message
                    add_message("user", prompt)
                    
                    # Show inline loading for quick feedback
                    loading_container = st.empty()
                    with loading_container.container():
                        display_inline_loading("Generating advice...", "💭")
                    
                    try:
                        # Generate and add the response
                        response = generate_response(prompt, st.session_state.noi_coach_context)
                        add_message("assistant", response)
                        
                        # Clear loading
                        loading_container.empty()
                    except Exception as e:
                        loading_container.empty()
                        st.error(f"Error: {str(e)}")
                    
                    # Rerun to update display
                    st.rerun()
        
        # Display chat history
        st.markdown("### Conversation")
        
        # Chat container with custom styling
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.noi_coach_messages:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div style="
                        background-color: rgba(59, 130, 246, 0.1);
                        border-radius: 8px;
                        padding: 10px 15px;
                        margin: 5px 0 5px auto;
                        max-width: 80%;
                        align-self: flex-end;
                        border-left: 3px solid #3B82F6;
                    ">
                        <p style="margin: 0; color: #E0E0E0;"><strong>You:</strong> {message["content"]}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="
                        background-color: rgba(30, 41, 59, 0.7);
                        border-radius: 8px;
                        padding: 10px 15px;
                        margin: 5px auto 5px 0;
                        max-width: 80%;
                        align-self: flex-start;
                        border-left: 3px solid #4DB6AC;
                    ">
                        <p style="margin: 0; color: #F0F0F0;"><strong>NOI Coach:</strong> {message["content"]}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Input area
        st.markdown("### Ask a Question")
        
        # Create a form for the chat input
        with st.form(key="noi_coach_form", clear_on_submit=True):
            user_input = st.text_area(
                "Type your question about NOI analysis, property performance, or financial strategies",
                height=100,
                key="noi_coach_input",
                help="Be specific and include relevant details for better advice"
            )
            
            # Submit button
            submit_col1, submit_col2, submit_col3 = st.columns([1, 2, 1])
            with submit_col2:
                submit_button = st.form_submit_button(
                    "Get Advice",
                    use_container_width=True
                )
            
        # Process the form submission
        if submit_button and user_input:
            # Add the user message to the chat history
            add_message("user", user_input)
            
            # Get loading message for NOI Coach
            loading_msg, loading_subtitle = get_loading_message_for_action("noi_coach")
            
            # Show loading indicator
            loading_container = st.empty()
            with loading_container.container():
                display_loading_spinner(loading_msg, loading_subtitle)
            
            try:
                # Generate the response
                response = generate_response(user_input, st.session_state.noi_coach_context)
                add_message("assistant", response)
                
                # Clear loading indicator
                loading_container.empty()
                
                # Show brief success message
                success_container = st.empty()
                with success_container.container():
                    display_inline_loading("Response generated!", "✅")
                
                # Clear success message after short delay
                import time
                time.sleep(1)
                success_container.empty()
                
            except Exception as e:
                # Clear loading on error
                loading_container.empty()
                st.error(f"Error generating response: {str(e)}")
                logger.error(f"NOI Coach error: {str(e)}")
            
            # Force a rerun to update the chat display
            st.rerun() 