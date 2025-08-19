@echo off
echo Activating virtual environment...

REM Check if .venv exists
if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Installing packages...
    call .venv\Scripts\activate.bat
    pip install -r requirements-minimal.txt
    playwright install chromium
) else (
    call .venv\Scripts\activate.bat
)

echo Virtual environment activated!
echo Python: %VIRTUAL_ENV%\Scripts\python.exe