#!/bin/bash
echo "=== RENDER DEBUG INFORMATION ==="
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la

echo ""
echo "=== CONFIGURATION FILES ==="
echo "Looking for render.yaml:"
find . -name "render.yaml" -exec cat {} \;

echo ""
echo "Looking for any other deployment configs:"
find . -name "Procfile" -o -name "*.toml" -o -name "poetry.lock" -o -name "uv.lock" | head -10

echo ""
echo "=== ENVIRONMENT VARIABLES ==="
echo "PORT: $PORT"
echo "PYTHON_VERSION: $PYTHON_VERSION"
echo "UV_FORCE_DISABLE: $UV_FORCE_DISABLE"
echo "POETRY_FORCE_DISABLE: $POETRY_FORCE_DISABLE"

echo ""
echo "=== PYTHON INFORMATION ==="
python --version
which python
pip --version
which pip

echo ""
echo "=== REQUIREMENTS FILES ==="
echo "Contents of requirements.txt:"
cat requirements.txt 2>/dev/null || echo "requirements.txt not found"

echo ""
echo "=== AVAILABLE PYTHON SCRIPTS ==="
ls -la *.py | head -5

echo ""
echo "=== ATTEMPTING TO RUN OUR API ==="
echo "Checking if ultra_minimal_api.py exists and is executable:"
ls -la ultra_minimal_api.py
echo "First few lines of ultra_minimal_api.py:"
head -10 ultra_minimal_api.py

echo ""
echo "=== RENDER BUILD PROCESS COMPLETE ==="