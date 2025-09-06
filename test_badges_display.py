import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_badges_display():
    """Test that the green containers (badges) are properly displayed"""
    try:
        # Read the credit_ui_minimal.py file
        with open('utils/credit_ui_minimal.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for the presence of badge HTML
        badge_indicators = [
            '5 Credits!',
            'Best Value!',
            'Save ',
            'background: linear-gradient(135deg, #10b981, #059669)',
            'background: linear-gradient(135deg, #3b82f6, #2563eb)'
        ]
        
        found_indicators = []
        missing_indicators = []
        
        for indicator in badge_indicators:
            if indicator in content:
                found_indicators.append(indicator)
            else:
                missing_indicators.append(indicator)
        
        print(f"✅ Found {len(found_indicators)} badge indicators:")
        for indicator in found_indicators:
            print(f"  - {indicator}")
        
        if missing_indicators:
            print(f"❌ Missing {len(missing_indicators)} badge indicators:")
            for indicator in missing_indicators:
                print(f"  - {indicator}")
            return False
        else:
            print("✅ All badge indicators found!")
            return True
            
    except Exception as e:
        print(f"❌ Error checking badges: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Badges Display...")
    print("=" * 50)
    
    success = test_badges_display()
    
    if success:
        print("🎉 Badges display test passed!")
        sys.exit(0)
    else:
        print("❌ Badges display test failed.")
        sys.exit(1)