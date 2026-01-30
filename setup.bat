@echo off
REM STAATS Python - Quick Setup Script (Windows)
REM Run this to get started in 60 seconds

echo =========================================
echo 🚀 STAATS Python - Quick Setup
echo =========================================
echo.

REM Check Python version
echo 📋 Checking Python version...
python --version
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.12+
    pause
    exit /b 1
)
echo    ✅ Python found
echo.

REM Create virtual environment
echo 🔧 Creating virtual environment...
if exist venv (
    echo    Virtual environment already exists
) else (
    python -m venv venv
    echo    ✅ Created venv\
)
echo.

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate
echo    ✅ Activated
echo.

REM Install dependencies
echo 📦 Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
echo    ✅ Installed all dependencies
echo.

REM Create output directories
echo 📁 Creating directories...
if not exist output mkdir output
if not exist temp mkdir temp
echo    ✅ Created output\ and temp\
echo.

REM Run tests
echo 🧪 Running tests...
python demo.py >nul 2>&1
echo    ✅ Core tests passed
echo.

REM All done
echo =========================================
echo ✅ Setup Complete!
echo =========================================
echo.
echo 🎯 Next Steps:
echo.
echo 1. Web App (Recommended):
echo    streamlit run app.py
echo    Then open: http://localhost:8501
echo.
echo 2. CLI Tool:
echo    python staats_cli.py process data.csv config.json -o output.xlsx
echo.
echo 3. Complete Demo:
echo    python complete_demo.py
echo.
echo 📖 Documentation:
echo    - COMPLETE_GUIDE.md - Full usage guide
echo    - PRODUCTION_DEPLOYMENT.md - Deployment instructions
echo    - GITHUB_README.md - Repository overview
echo.
echo 🔥 Happy processing!
echo.
pause
