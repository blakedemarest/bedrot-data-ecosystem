#!/bin/bash
# Setup WSL Python Virtual Environment for BEDROT Data Ecosystem

echo "🚀 Setting up WSL Python Virtual Environment"
echo "=========================================="

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📁 Project root: $PROJECT_ROOT"

# Navigate to project root
cd "$PROJECT_ROOT"

# Remove existing Windows venv if present
if [ -d ".venv" ]; then
    echo "🗑️  Removing existing .venv (likely Windows-created)..."
    rm -rf .venv
fi

# Check Python version
echo "🐍 Python version:"
python3 --version

# Create new virtual environment
echo "📦 Creating new virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install essential packages for data ecosystem
echo "📚 Installing essential packages..."
pip install pandas numpy python-dateutil

# Install data lake dependencies if requirements.txt exists
if [ -f "data_lake/requirements.txt" ]; then
    echo "📚 Installing data lake requirements..."
    pip install -r data_lake/requirements.txt
fi

# Install data warehouse dependencies if requirements.txt exists
if [ -f "data-warehouse/requirements.txt" ]; then
    echo "📚 Installing data warehouse requirements..."
    pip install -r data-warehouse/requirements.txt
fi

# Verify installations
echo ""
echo "✅ Verification:"
echo "==============="
python -c "import pandas; print('✓ pandas version:', pandas.__version__)"
python -c "import numpy; print('✓ numpy version:', numpy.__version__)"

# Test data integrity module
echo ""
echo "🧪 Testing data integrity module..."
python -c "
import sys
sys.path.append('data_lake/src')
try:
    from common.integrity_checks import DataIntegrityChecker
    print('✓ Data integrity module imports successfully!')
except Exception as e:
    print('✗ Error importing integrity module:', e)
"

# Create activation reminder
echo ""
echo "📝 Creating activation helper..."
cat > activate_venv.sh << 'EOF'
#!/bin/bash
# Quick activation script for BEDROT venv
source .venv/bin/activate
echo "✅ Virtual environment activated!"
echo "   Python: $(which python)"
echo "   Pip:    $(which pip)"
EOF

chmod +x activate_venv.sh

echo ""
echo "✨ Setup complete!"
echo ""
echo "To activate the virtual environment in future sessions, run:"
echo "  source .venv/bin/activate"
echo "  OR"
echo "  ./activate_venv.sh"
echo ""
echo "To deactivate, run:"
echo "  deactivate"