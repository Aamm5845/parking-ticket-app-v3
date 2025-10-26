@echo off
echo ========================================
echo     Tickety - Local Development Mode
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

:: Set current directory to script location
cd /d "%~dp0"

:: Set environment variables for local development
set ENABLE_SELENIUM=1
set FLASK_ENV=development
set FLASK_DEBUG=1

:: Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

:: Activate virtual environment
call .venv\Scripts\activate.bat

:: Install/upgrade requirements-dev.txt
echo Installing development dependencies...
pip install --upgrade pip
pip install -r requirements-dev.txt

:: Check if .env file exists, if not create one
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
)

:: Start the Flask app
echo.
echo ========================================
echo Starting Tickety with Selenium enabled
echo ========================================
echo.
echo App will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

:: Open browser automatically after 3 seconds
start "" timeout /t 3 /nobreak >nul 2>&1 && start "" "http://localhost:5000"

:: Start Flask app
python app.py

pause