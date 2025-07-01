import requests
import os
from typing import List, Optional, Dict
import streamlit as st


def create_stripe_job_and_redirect(email: str, files: List[st.runtime.uploaded_file_manager.UploadedFile], doc_types: Optional[List[str]] = None):
    """Create a pay-per-use job and redirect to Stripe checkout."""
    
    # Prepare files for upload
    files_data = []
    for file in files:
        file.seek(0)  # Reset file pointer
        files_data.append(('files', (file.name, file.getvalue(), file.type)))
    
    # Prepare form data
    form_data = [('email', email)]
    if doc_types:
        for doc_type in doc_types:
            form_data.append(('doc_types', doc_type))
    
    # Get backend URL
    backend_url = os.getenv("BACKEND_URL", "https://noianalyzer.onrender.com")
    
    try:
        # Call backend to create job
        response = requests.post(
            f"{backend_url}/pay-per-use/jobs",
            data=form_data,
            files=files_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            checkout_url = result.get('checkout_url')
            job_id = result.get('job_id')
            
            if checkout_url:
                # Store job_id in session for potential status checking
                st.session_state.current_job_id = job_id
                
                # Redirect to Stripe checkout using JavaScript
                st.markdown(f"""
                <script>
                window.open('{checkout_url}', '_self');
                </script>
                """, unsafe_allow_html=True)
                
                # Also show a clickable link as fallback
                st.success("Redirecting to checkout...")
                st.markdown(f"If you're not redirected automatically, [click here to complete payment]({checkout_url})")
                
                return True
            else:
                st.error("Failed to create checkout session. Please try again.")
                return False
        else:
            st.error(f"Failed to create job: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return False
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return False 