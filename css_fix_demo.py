# This is a demonstration of how to fix the CSS braces in f-string

# The problem in the original code:
# In the f-string, CSS braces {{ and }} were being interpreted as f-string placeholders

# The fix:
# We need to escape the braces by doubling them: {{ becomes {{{{ and }} becomes }}}}

def demonstrate_fix():
    uploader_id = "test123"
    
    # INCORRECT - This causes SyntaxError
    # st.markdown(
    # f"""
    # <style>
    # .upload-card-{uploader_id} {{
    #     background: linear-gradient(135deg, rgba(17, 24, 39, 0.95), rgba(31, 41, 55, 0.9)) !important;
    # }}
    # </style>
    # """,
    # unsafe_allow_html=True
    # )
    
    # CORRECT - This works properly
    st.markdown(
    f"""
    <style>
    .upload-card-{uploader_id} {{{{
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.95), rgba(31, 41, 55, 0.9)) !important;
    }}}} 
    </style>
    """,
    unsafe_allow_html=True
    )

# Explanation:
# In Python f-strings:
# - Single braces {} are used for placeholders
# - To get literal braces in the output, we need to escape them by doubling them
# - So {{ becomes {{{{ and }} becomes }}}}