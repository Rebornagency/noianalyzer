#!/usr/bin/env python3
"""
Simple test runner for the perfect approach implementation.
"""

import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Run the simple perfect test
print("Running simple perfect approach test...")
try:
    import simple_perfect_test
    print("✅ Simple perfect approach test completed successfully!")
except Exception as e:
    print(f"❌ Error running simple perfect approach test: {e}")

# Run the comprehensive test
print("\nRunning comprehensive perfect approach test...")
try:
    import perfect_approach_comprehensive_test
    print("✅ Comprehensive perfect approach test completed successfully!")
except Exception as e:
    print(f"❌ Error running comprehensive perfect approach test: {e}")

print("\n🎉 All tests completed!")