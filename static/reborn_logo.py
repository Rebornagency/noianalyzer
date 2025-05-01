
import base64

def get_logo_base64():
    with open("Reborn Logo.jpeg", "rb") as f:
        return base64.b64encode(f.read()).decode()

def get_logo_html():
    return f"""
        <div style="text-align: center; padding: 1rem;">
            <img src="data:image/jpeg;base64,{get_logo_base64()}" 
                 alt="Reborn Logo"
                 style="max-width: 200px; height: auto;">
        </div>
    """
