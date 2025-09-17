"""
Test script to verify that pipeline_runner can be imported successfully.
"""

try:
    from .pipeline_runner import run_noi_pipeline
    print("SUCCESS: pipeline_runner imported successfully")
    print(f"run_noi_pipeline function: {run_noi_pipeline}")
except ImportError as e:
    print(f"ERROR: Failed to import pipeline_runner: {e}")