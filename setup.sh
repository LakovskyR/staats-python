#!/bin/bash
# STAATS Python - Quick Setup Script
# Run this to get started in 60 seconds

set -e  # Exit on error

echo "========================================="
echo "🚀 STAATS Python - Quick Setup"
echo "========================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found: Python $python_version"

# Create virtual environment
echo ""
echo "🔧 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   Virtual environment already exists"
else
    python3 -m venv venv
    echo "   ✅ Created venv/"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Activated"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "   ✅ Installed all dependencies"

# Create output directories
echo ""
echo "📁 Creating directories..."
mkdir -p output temp
echo "   ✅ Created output/ and temp/"

# Run tests
echo ""
echo "🧪 Running tests..."
python demo.py > /dev/null 2>&1
echo "   ✅ Core tests passed"

# All done
echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "🎯 Next Steps:"
echo ""
echo "1. Web App (Recommended):"
echo "   streamlit run app.py"
echo "   Then open: http://localhost:8501"
echo ""
echo "2. CLI Tool:"
echo "   python staats_cli.py process data.csv config.json -o output.xlsx"
echo ""
echo "3. Complete Demo:"
echo "   python complete_demo.py"
echo ""
echo "📖 Documentation:"
echo "   - COMPLETE_GUIDE.md - Full usage guide"
echo "   - PRODUCTION_DEPLOYMENT.md - Deployment instructions"
echo "   - GITHUB_README.md - Repository overview"
echo ""
echo "🔥 Happy processing!"
echo ""
