# PDF Generation Setup Guide

The NOI Analyzer uses WeasyPrint for high-quality PDF generation. However, WeasyPrint is not included in the default requirements due to installation complexity on some systems.

## Why WeasyPrint is Optional

WeasyPrint provides professional-quality PDF generation with proper styling and formatting, but it requires:
- A Rust toolchain for compilation
- Several system dependencies

To avoid installation issues, especially on cloud platforms like Render, WeasyPrint is included as an optional dependency.

## Enabling Full PDF Generation

### Option 1: Install WeasyPrint Locally (Recommended for Development)

1. Install the Rust toolchain:
   - Windows: Download from https://www.rust-lang.org/tools/install
   - macOS: `brew install rust`
   - Linux: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`

2. Install WeasyPrint:
   ```bash
   pip install weasyprint
   ```

3. Restart your Python environment

### Option 2: Use the Built-in HTML Fallback

If you prefer not to install WeasyPrint, the application will automatically fall back to HTML-based reporting:
- Click the "Try PDF Export" button
- Use the "Print Report as PDF" button in the generated HTML report
- Select "Save as PDF" in your browser's print dialog

## Troubleshooting

### Common Installation Issues

1. **Missing Rust toolchain**:
   ```
   error: can't find Rust compiler
   ```
   Solution: Install Rust as described above.

2. **Missing system dependencies** (Linux):
   ```
   error: cairo >= 1.15.10 is required
   ```
   Solution: Install system dependencies:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev
   
   # CentOS/RHEL
   sudo yum install cairo-devel pango-devel libjpeg-devel libgif-devel librsvg2-devel
   ```

3. **Permission errors**:
   ```
   PermissionError: [Errno 13] Permission denied
   ```
   Solution: Use a virtual environment or install with `--user` flag:
   ```bash
   pip install --user weasyprint
   ```

## Verifying Installation

After installation, you can verify WeasyPrint is available:

```python
try:
    from weasyprint import HTML
    print("WeasyPrint is available")
except ImportError:
    print("WeasyPrint is not available")
```

The application will automatically detect if WeasyPrint is available and use it for PDF generation.