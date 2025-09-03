import streamlit as st
import sys
import os

# Add the utils directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

# Mock the display_credit_store function to test UI changes
def display_credit_store():
    """Mock credit store display for testing UI changes"""
    
    # Modern header styling
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #FFFFFF; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">
            💳 Credit Store
        </h1>
        <p style="color: #A0A0A0; font-size: 1.2rem; margin-bottom: 1rem;">
            Purchase credits to unlock NOI analysis capabilities
        </p>
        <p style="color: #FACC15; font-size: 1.1rem; font-weight: 600;">
            ⏱ Save <span style="font-weight: 800;">up to 3 hours</span> of manual spreadsheet work per analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced CSS for modern, clean package cards
    st.markdown("""
    <style>
    /* Modern Credit Package Cards */
    div.credit-package-card {
        background: linear-gradient(145deg, #1a2436, #0f1722);
        border: 1px solid #2a3a50;
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
        padding: 2rem;
        margin: 1.5rem 0;
        text-align: center;
        transition: all 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    div.credit-package-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
        border-color: #3b82f6;
    }
    
    div.credit-package-card h3 {
        color: #FFFFFF;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0 0 1.5rem 0;
        padding-bottom: 1rem;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
    }
    
    div.credit-package-card .credits-amount {
        color: #FFFFFF;
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1rem 0;
    }
    
    div.credit-package-card .price {
        color: #FFFFFF;
        font-size: 2.5rem;
        font-weight: 800;
        margin: 1rem 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    div.credit-package-card .per-credit {
        color: #A0A0A0;
        font-size: 1rem;
        font-style: italic;
        margin: 0.5rem 0 1.5rem 0;
    }
    
    div.credit-package-card .savings-badge {
        background: linear-gradient(135deg, #10b981, #059669);
        color: #FFFFFF;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 0.8rem 1.5rem;
        border-radius: 50px;
        margin: 1rem auto;
        width: fit-content;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
    }
    
    div.credit-package-card .description {
        color: #D0D0D0;
        font-size: 1rem;
        line-height: 1.6;
        margin: 1.5rem 0;
        flex-grow: 1;
    }
    
    div.credit-package-card .time-savings {
        color: #FACC15;
        font-weight: 700;
        font-size: 1.1rem;
        margin: 1rem 0;
    }
    
    div.credit-package-card .purchase-button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: #FFFFFF;
        border: none;
        border-radius: 12px;
        padding: 1rem;
        font-size: 1.1rem;
        font-weight: 700;
        width: 100%;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.5);
        margin-top: auto;
    }
    
    div.credit-package-card .purchase-button:hover {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(37, 99, 235, 0.7);
    }
    
    div.credit-package-card .purchase-button:disabled {
        background: #6b7280;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        div.credit-package-card {
            padding: 1.5rem;
            margin: 1rem 0;
        }
        
        div.credit-package-card h3 {
            font-size: 1.5rem;
        }
        
        div.credit-package-card .price {
            font-size: 2rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Mock packages data
    packages = [
        {
            "package_id": "basic",
            "name": "Basic Package",
            "credits": 5,
            "price_dollars": 10.00,
            "per_credit_cost": 2.00,
            "description": "Perfect for trying out our service"
        },
        {
            "package_id": "pro",
            "name": "Pro Package",
            "credits": 15,
            "price_dollars": 25.00,
            "per_credit_cost": 1.67,
            "description": "Best value for regular users"
        },
        {
            "package_id": "enterprise",
            "name": "Enterprise Package",
            "credits": 50,
            "price_dollars": 75.00,
            "per_credit_cost": 1.50,
            "description": "Ideal for heavy users and teams"
        }
    ]
    
    # Display packages in a responsive grid
    num_packages = len(packages)
    if num_packages == 1:
        cols = st.columns(1)
    elif num_packages == 2:
        cols = st.columns(2)
    else:
        cols = st.columns(min(num_packages, 3))
    
    for idx, package in enumerate(packages):
        col = cols[idx % len(cols)]
        
        with col:
            # Calculate savings
            savings_text = ""
            if idx > 0 and len(packages) > 1:
                base_per_credit = packages[0]["per_credit_cost"]
                current_per_credit = package["per_credit_cost"]
                savings_percent = ((base_per_credit - current_per_credit) / base_per_credit) * 100
                if savings_percent > 0:
                    savings_text = f"Save {savings_percent:.0f}%!"
            
            # Modern card container
            st.markdown('<div class="credit-package-card">', unsafe_allow_html=True)
            
            # Package title with special highlighting for popular package
            if idx == 1 and len(packages) > 2:  # Middle package in 3+ packages
                st.markdown(f'<h3>🌟 {package["name"]} (Popular)</h3>', unsafe_allow_html=True)
            else:
                st.markdown(f'<h3>{package["name"]}</h3>', unsafe_allow_html=True)
            
            # Credits amount
            st.markdown(f'<div class="credits-amount">{package["credits"]} Credits</div>', unsafe_allow_html=True)
            
            # Price
            st.markdown(f'<div class="price">${package["price_dollars"]:.2f}</div>', unsafe_allow_html=True)
            
            # Per credit cost
            st.markdown(f'<div class="per-credit">${package["per_credit_cost"]:.2f} per credit</div>', unsafe_allow_html=True)

            # Savings badge
            if savings_text:
                st.markdown(f'<div class="savings-badge">{savings_text}</div>', unsafe_allow_html=True)
            elif len(packages) > 1:
                # For the best value package (first one), show a different badge
                if idx == 0:
                    st.markdown('<div class="savings-badge">Best Value! 🚀</div>', unsafe_allow_html=True)
            
            # Time savings calculation
            hours_saved = int(round(package['credits'] * 1.75))
            st.markdown(
                f'<div class="time-savings">⏱ Save ~{hours_saved} hours of work!</div>',
                unsafe_allow_html=True,
            )
            
            # Description
            description_text = package.get('description', f"Top up {package['credits']} credits")
            st.markdown(f'<div class="description">{description_text}</div>', unsafe_allow_html=True)
            
            # Purchase button
            email = st.session_state.get('user_email', '')
            
            if not email:
                st.warning("Please enter your email in the main app to purchase credits.")
                st.markdown('<button class="purchase-button" disabled>Enter Email to Buy</button>', unsafe_allow_html=True)
            else:
                # Use HTML button for better styling control
                if st.button(f"Buy {package['name']}", key=f"buy_{package['package_id']}", use_container_width=True):
                    st.info(f"Would purchase {package['name']} package")
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close card div
    
    # Add proper spacing after all cards are displayed
    st.markdown("<br><br>", unsafe_allow_html=True)

# Streamlit app
st.set_page_config(page_title="Credit Store Test", layout="wide")

st.title("Credit Store UI Test")

# Initialize session state
if 'user_email' not in st.session_state:
    st.session_state.user_email = "test@example.com"

# Display the credit store
display_credit_store()