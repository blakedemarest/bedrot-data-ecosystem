#!/bin/bash
# Quick WSL Python Environment Setup

echo "🚀 Quick WSL Python Setup"
echo "========================"

# Navigate to project root
cd "$(dirname "$(dirname "${BASH_SOURCE[0]}")")"

# Remove old venv if exists
if [ -d ".venv" ]; then
    echo "Removing old .venv..."
    rm -rf .venv
fi

# Create new venv
echo "Creating new virtual environment..."
python3 -m venv .venv

# Activate it
echo "Activating..."
source .venv/bin/activate

# Install just pandas for now
echo "Installing pandas..."
pip install --upgrade pip
pip install pandas

# Test it
echo ""
echo "Testing pandas import..."
python -c "import pandas; print('✅ pandas works! Version:', pandas.__version__)"

echo ""
echo "✅ Done! To activate in future:"
echo "   source .venv/bin/activate"