@echo off
REM Start the BEDROT Data Dashboard Backend

echo Starting BEDROT Data Dashboard Backend...

REM Navigate to project directory
cd /d "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_dashboard"

REM Activate virtual environment
call venv\Scripts\activate

REM Start the backend server
python backend\main.py

pause