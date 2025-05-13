import base64
from reborn_logo import get_reborn_logo_base64

def get_logo_base64():
    """
    Returns the logo as a base64 string
    """
    return get_reborn_logo_base64()

def get_logo_html():
    """
    Returns HTML for embedding the logo
    """
    return f"""
        <div style="text-align: center; padding: 1rem;">
            <img src="data:image/png;base64,{get_logo_base64()}" 
                 alt="Reborn Logo"
                 style="max-width: 200px; height: auto;">
        </div>
    """
