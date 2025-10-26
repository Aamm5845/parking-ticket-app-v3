@echo off
echo.
echo ========================================
echo     Tickety - Fight Parking Ticket
echo ========================================
echo.

cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    REM If virtual environment doesn't exist, create one
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -q selenium webdriver-manager
)

echo.
echo 🚀 Starting Ticket Fighter...
echo.

REM Run the standalone script
python fight_ticket_standalone.py

if errorlevel 1 (
    echo.
    echo ❌ Error occurred. Check the messages above.
)

pause
