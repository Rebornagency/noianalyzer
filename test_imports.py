import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Testing imports...")

try:
    from utils.credit_ui_robust import display_credit_store
    print("✅ Successfully imported credit_ui_robust")
except Exception as e:
    print(f"❌ Failed to import credit_ui_robust: {e}")

try:
    from utils.credit_ui_fresh import display_credit_store
    print("✅ Successfully imported credit_ui_fresh")
except Exception as e:
    print(f"❌ Failed to import credit_ui_fresh: {e}")

try:
    from utils.credit_ui import display_credit_store
    print("✅ Successfully imported credit_ui")
except Exception as e:
    print(f"❌ Failed to import credit_ui: {e}")

print("Import test complete.")