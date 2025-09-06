import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_credit_ui_structure():
    """Test that the credit UI has proper HTML structure"""
    try:
        # Read the credit_ui_minimal.py file
        with open('utils/credit_ui_minimal.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key structural elements
        required_patterns = [
            'card_html = f"""',
            'card_html += """',
            'st.markdown(card_html, unsafe_allow_html=True)',
            '</div>',
            '5 Credits!',
            'Best Value!',
            'Save '
        ]
        
        missing_patterns = []
        found_patterns = []
        
        for pattern in required_patterns:
            if pattern in content:
                found_patterns.append(pattern)
            else:
                missing_patterns.append(pattern)
        
        print(f"✅ Found {len(found_patterns)} required patterns:")
        for pattern in found_patterns:
            print(f"  - {pattern}")
        
        if missing_patterns:
            print(f"❌ Missing {len(missing_patterns)} required patterns:")
            for pattern in missing_patterns:
                print(f"  - {pattern}")
            return False
        else:
            print("✅ All required patterns found!")
            return True
            
    except Exception as e:
        print(f"❌ Error checking credit UI structure: {e}")
        return False

def test_badge_logic():
    """Test that the badge logic is correct"""
    try:
        # Read the credit_ui_minimal.py file
        with open('utils/credit_ui_minimal.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for proper badge logic
        badge_conditions = [
            'idx == 0 and len(packages) > 1',
            '(len(packages) > 2 and idx == 1) or (len(packages) == 2 and idx == 1)',
            'savings_text and idx > 1'
        ]
        
        missing_conditions = []
        found_conditions = []
        
        for condition in badge_conditions:
            if condition in content:
                found_conditions.append(condition)
            else:
                missing_conditions.append(condition)
        
        print(f"✅ Found {len(found_conditions)} badge conditions:")
        for condition in found_conditions:
            print(f"  - {condition}")
        
        if missing_conditions:
            print(f"❌ Missing {len(missing_conditions)} badge conditions:")
            for condition in missing_conditions:
                print(f"  - {condition}")
            return False
        else:
            print("✅ All badge conditions found!")
            return True
            
    except Exception as e:
        print(f"❌ Error checking badge logic: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Verifying Credit UI Fix...")
    print("=" * 50)
    
    structure_test = test_credit_ui_structure()
    print()
    badge_test = test_badge_logic()
    
    if structure_test and badge_test:
        print("\n🎉 Credit UI fix verification passed!")
        print("The HTML structure should now render properly.")
        sys.exit(0)
    else:
        print("\n❌ Credit UI fix verification failed.")
        sys.exit(1)