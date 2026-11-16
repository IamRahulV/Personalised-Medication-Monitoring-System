@echo off
TITLE Smart Medication Reminder & Health Tracker
echo ======================================================================
echo    Smart Medication Reminder ^& Health Tracker - B.Tech CSE Project
echo ======================================================================
echo.

:: 1. Check if virtual environment exists; create if not
if not exist "venv" (
    echo [INFO] Creating Python virtual environment 'venv'...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment. Ensure Python is installed and in PATH.
        pause
        exit /b 1
    )
    echo [INFO] Virtual environment created successfully.
) else (
    echo [INFO] Virtual environment 'venv' already exists.
)

:: 2. Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: 3. Install required packages
echo [INFO] Installing / verifying dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: 4. Safely initialize database tables without overwriting existing data
echo [INFO] Initializing SQLite database schema (medication.db)...
python database.py

:: 5. Launch Streamlit application
echo.
echo ======================================================================
echo  Application is launching!
echo  Local Dashboard URL: http://localhost:8501
echo  Press Ctrl+C in this terminal window to stop the server.
echo ======================================================================
echo.

streamlit run app.py

pause
