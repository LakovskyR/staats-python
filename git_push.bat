@echo off
REM Git Push Script - Run this on your local Windows machine

echo 🚀 Pushing STAATS Python to GitHub...
echo.

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ Error: Please run this from the staats_python directory
    pause
    exit /b 1
)

REM Configure git safe directory
git config --global --add safe.directory "%CD%"

REM Initialize and configure git
git init
git config user.email "staats@aplusa.com"
git config user.name "STAATS Python"

REM Rename branch to main
git branch -m main 2>nul

REM Add all files
echo 📦 Adding files...
git add .

REM Commit
echo 💾 Committing...
git commit -m "Initial commit: STAATS Python v1.0 - Complete production system" 2>nul || echo Already committed

REM Add remote
echo 🔗 Adding GitHub remote...
git remote remove origin 2>nul
git remote add origin https://github.com/LakovskyR/staats-python.git

REM Push
echo 🚀 Pushing to GitHub...
echo.
echo ⚠️  You may be prompted for GitHub credentials
echo     Use your GitHub username and personal access token (not password)
echo.
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Success! Code pushed to GitHub
    echo.
    echo 🎯 Repository: https://github.com/LakovskyR/staats-python
    echo.
    echo 📋 Next steps:
    echo    1. View repository: https://github.com/LakovskyR/staats-python
    echo    2. Deploy Streamlit app: See instructions below
    echo.
) else (
    echo.
    echo ❌ Push failed. Please check:
    echo    - You're logged into GitHub
    echo    - You have permissions for this repository
    echo    - Your personal access token is valid
    echo.
    echo 📖 GitHub authentication help:
    echo    https://docs.github.com/en/authentication
    echo.
)

pause
