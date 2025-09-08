# Fix for DuplicateWidgetID Error in Terms of Service Flow

## Problem
When users upload documents but don't accept the Terms of Service, clicking the "Process Documents" button causes a DuplicateWidgetID error because the code tries to restore the button with the same key that was used for the original button.

## Root Cause
The issue occurs in the process button click handler where:
1. The original button is created with `key="main_process_button"`
2. When terms are not accepted, the code calls `restore_button` with the same key
3. This creates two widgets with the same key, causing the DuplicateWidgetID error

## Solution
Move the terms of service check to the beginning of the process button click handler and return early if terms are not accepted, without trying to restore the button with the same key.

## Code Changes Needed

### Current Problematic Code (around line 4700+):
```python
if process_clicked:
    logger.info("Process Documents button was clicked")
    logger.info(f"Current session state - terms_accepted: {st.session_state.get('terms_accepted', False)}")
    logger.info(f"Current session state - user_email: {st.session_state.get('user_email', '')}")
    logger.info(f"Current session state - testing_mode: {is_testing_mode_active()}")
    
    # ... later in the code ...
    # Check if Terms of Service have been accepted
    logger.info(f"Checking terms acceptance: {st.session_state.get('terms_accepted', False)}")
    if not st.session_state.get('terms_accepted', False):
        logger.info("Terms not accepted, showing error message")
        st.session_state.show_tos_error = True
        # Clear loading states before showing error
        loading_container.empty()
        restore_button(process_button_placeholder, "Process Documents", key="main_process_button", type="primary", use_container_width=True)
        # Don't call st.rerun() here to prevent infinite loop
        # The error message will be displayed on the next render cycle
        return  # Exit the function to prevent further processing
```

### Fixed Code:
```python
if process_clicked:
    logger.info("Process Documents button was clicked")
    logger.info(f"Current session state - terms_accepted: {st.session_state.get('terms_accepted', False)}")
    logger.info(f"Current session state - user_email: {st.session_state.get('user_email', '')}")
    logger.info(f"Current session state - testing_mode: {is_testing_mode_active()}")
    
    # Check if Terms of Service have been accepted BEFORE any processing
    logger.info(f"Checking terms acceptance: {st.session_state.get('terms_accepted', False)}")
    if not st.session_state.get('terms_accepted', False):
        logger.info("Terms not accepted, showing error message")
        st.session_state.show_tos_error = True
        st.markdown(
            '<div class="tos-error">⚠️ You must accept the Terms of Service and Privacy Policy to process documents.</div>',
            unsafe_allow_html=True
        )
        # Don't proceed with processing - just show the error and return
        return  # Exit the function to prevent further processing
    
    # Continue with the rest of the processing...
    # NEW: Check if email is provided before proceeding
    user_email = st.session_state.get('user_email', '').strip()
    # ... rest of the code
```

## Additional Cleanup
Remove the duplicate else clause that was causing syntax errors around lines 4725-4730:

### Remove this duplicate code:
```python
else:
    # Terms accepted, continue with processing (moved to earlier in the function)
    logger.info("Terms accepted, continuing with document processing")
```

## Summary
This fix ensures that:
1. Terms of service are checked immediately when the process button is clicked
2. If terms are not accepted, an error message is displayed and the function returns early
3. No attempt is made to restore the button with the same key, preventing DuplicateWidgetID errors
4. The user flow is clear - they see an error message and can accept terms to proceed