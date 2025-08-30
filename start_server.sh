#!/bin/bash

echo "=== CUSTOM START SCRIPT INITIATED ==="
echo "Current directory: $(pwd)"
echo "Available files:"
ls -la *.py | head -10

echo ""
echo "=== ENVIRONMENT CHECK ==="
echo "PORT: $PORT"
echo "Python version: $(python --version)"

echo ""
echo "=== CHECKING FOR OUR API FILE ==="
if [ -f "ultra_minimal_api.py" ]; then
    echo "✅ ultra_minimal_api.py found!"
    echo "File size: $(wc -c < ultra_minimal_api.py) bytes"
    echo "First 5 lines:"
    head -5 ultra_minimal_api.py
    
    echo ""
    echo "=== STARTING ULTRA MINIMAL API ==="
    exec python ultra_minimal_api.py
else
    echo "❌ ultra_minimal_api.py NOT FOUND!"
    echo "Available Python files:"
    ls -la *.py
    exit 1
fi