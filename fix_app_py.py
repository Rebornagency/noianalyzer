import re

# Read the file
with open("c:\\Users\\edgar\\Documents\\GitHub\\noianalyzer\\noianalyzer\\app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: Add return type annotation to generate_comparison_excel fallback function
# Find the line with the fallback function definition and add the return type
pattern = r"(except ImportError:\s+def generate_comparison_excel\(\):)"
replacement = r"except ImportError:\n    def generate_comparison_excel() -> bytes | None:"
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Fix 2: Add type ignore comment to suppress the set_table_styles warning
pattern = r"(\.set_table_styles\(\[)"
replacement = r".set_table_styles([  # type: ignore"
content = re.sub(pattern, replacement, content)

# Write the file back
with open("c:\\Users\\edgar\\Documents\\GitHub\\noianalyzer\\noianalyzer\\app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed both issues in app.py:")
print("1. Added return type annotation to generate_comparison_excel fallback function")
print("2. Added type ignore comment to suppress set_table_styles warning")