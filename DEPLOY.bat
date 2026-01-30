@echo off
REM STAATS Python - Automated Push & Deploy Script
REM Run this after extracting the ZIP file

echo.
echo ========================================
echo   STAATS Python - Auto Deploy
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ Error: Please run this from the staats_python directory
    echo.
    echo Extract the ZIP file first, then:
    echo   cd staats_python
    echo   DEPLOY.bat
    echo.
    pause
    exit /b 1
)

echo 📦 Step 1: Setting up Git...
echo.

REM Initialize git
git init
git config user.email "staats@aplusa.com"
git config user.name "STAATS Python"
git branch -m main 2>nul

REM Add files
git add .

REM Commit
git commit -m "Initial commit: STAATS Python v1.0 - Complete production system" 2>nul
if %ERRORLEVEL% NEQ 0 (
    git commit --amend -m "Initial commit: STAATS Python v1.0 - Complete production system" 2>nul
)

echo ✅ Git initialized
echo.

echo 🔗 Step 2: Pushing to GitHub...
echo.

REM Add remote
git remote remove origin 2>nul
git remote add origin https://github.com/LakovskyR/staats-python.git

REM Push
echo ⚠️  You may be prompted for GitHub credentials
echo     Username: LakovskyR
echo     Password: Use your Personal Access Token
echo.
echo     Don't have a token? Create one at:
echo     https://github.com/settings/tokens
echo     (Select 'repo' scope)
echo.

git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Successfully pushed to GitHub!
    echo    Repository: https://github.com/LakovskyR/staats-python
    echo.
) else (
    echo.
    echo ⚠️  Push may have failed. Please check:
    echo     - GitHub credentials are correct
    echo     - Personal Access Token has 'repo' permissions
    echo.
    echo You can try again by running:
    echo     git push -u origin main
    echo.
)

echo ========================================
echo 🚀 Step 3: Deploying Streamlit App
echo ========================================
echo.

echo 📦 Installing dependencies...
pip install -r requirements.txt >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Dependencies installed
) else (
    echo ⚠️  Some dependencies may have failed to install
    echo     You can install manually: pip install -r requirements.txt
)
echo.

echo 🌐 Starting Streamlit web app...
echo.
echo ========================================
echo   Web App Starting
echo ========================================
echo.
echo The app will open in your browser at:
echo   http://localhost:8501
echo.
echo To share with your team, use:
echo   http://YOUR-IP-ADDRESS:8501
echo.
echo To stop the app: Press Ctrl+C
echo.
echo ========================================
echo.

REM Start Streamlit
streamlit run app.py

REM If streamlit failed
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Streamlit failed to start
    echo.
    echo Please install Streamlit:
    echo   pip install streamlit
    echo.
    echo Then run:
    echo   streamlit run app.py
    echo.
    pause
)
