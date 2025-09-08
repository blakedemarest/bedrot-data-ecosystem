@echo off
setlocal

echo Setting up environment...
cd /d "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"
set PROJECT_ROOT=%cd%

echo.
echo Running TikTok cleaners...
echo ========================================

echo [1/3] Running landing2raw...
python src\tiktok\cleaners\tiktok_landing2raw.py
if %errorlevel% neq 0 (
    echo ERROR: landing2raw failed
    pause
    exit /b 1
)

echo.
echo [2/3] Running raw2staging...
python src\tiktok\cleaners\tiktok_raw2staging.py
if %errorlevel% neq 0 (
    echo ERROR: raw2staging failed
    pause
    exit /b 1
)

echo.
echo [3/3] Running staging2curated...
python src\tiktok\cleaners\tiktok_staging2curated.py
if %errorlevel% neq 0 (
    echo ERROR: staging2curated failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo All TikTok cleaners completed successfully!
echo.

endlocal