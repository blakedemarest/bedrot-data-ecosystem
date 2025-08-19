@echo off
REM Simple Windows pipeline runner

REM Set PROJECT_ROOT properly without trailing spaces
cd /d "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"
set "PROJECT_ROOT=C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"

echo PROJECT_ROOT is set to: [%PROJECT_ROOT%]

REM Activate venv
call .venv\Scripts\activate.bat

REM Test a single cleaner
echo.
echo Testing Spotify landing2raw...
python src\spotify\cleaners\spotify_landing2raw.py

echo.
echo Done!