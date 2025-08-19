@echo off
setlocal EnableDelayedExpansion

REM ================================================================================
REM                    BEDROT DATA LAKE PIPELINE - WINDOWS COMPATIBLE
REM ================================================================================

echo.
echo ================================================================================
echo                         BEDROT DATA LAKE PIPELINE
echo                          Starting at %date% %time%
echo ================================================================================
echo.

REM Set working directory
cd /d "%~dp0"
set "PROJECT_ROOT=%CD%"
echo [DEBUG] PROJECT_ROOT: %PROJECT_ROOT%

REM Check if virtual environment exists
if not exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at %PROJECT_ROOT%\.venv
    echo [ERROR] Please create it with: python -m venv .venv
    echo [ERROR] Then install requirements: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Set Python to use venv
set "PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"
echo [DEBUG] Using Python: %PYTHON%

REM Quick test to ensure Python works
"%PYTHON%" --version
if errorlevel 1 (
    echo [ERROR] Failed to run Python from virtual environment
    pause
    exit /b 1
)

REM Set PYTHONPATH
set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%"
echo [DEBUG] PYTHONPATH: %PYTHONPATH%

REM Create logs directory
if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs"

REM Simple log file name
set "LOG_FILE=%PROJECT_ROOT%\logs\pipeline_run.log"
echo [INFO] Log file: %LOG_FILE%
echo.

REM Initialize counters
set EXTRACTION_FAILURES=0
set CLEANER_FAILURES=0

REM ========== EXTRACTORS ==========
echo [STEP 1/3] Running Data Extractors
echo [STEP 1/3] Running Data Extractors >> "%LOG_FILE%"
echo ========================================
echo.

REM Spotify
echo [INFO] Running Spotify extractor...
"%PYTHON%" "%PROJECT_ROOT%\src\spotify\extractors\spotify_audience_extractor.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [WARNING] Spotify extraction failed
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [OK] Spotify extraction completed
)

REM DistroKid
echo [INFO] Running DistroKid extractor...
"%PYTHON%" "%PROJECT_ROOT%\src\distrokid\extractors\dk_auth.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [WARNING] DistroKid extraction failed
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [OK] DistroKid extraction completed
)

REM TikTok Zone A0
echo [INFO] Running TikTok Zone A0 extractor...
"%PYTHON%" "%PROJECT_ROOT%\src\tiktok\extractors\tiktok_analytics_extractor_zonea0.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [WARNING] TikTok Zone A0 extraction failed
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [OK] TikTok Zone A0 extraction completed
)

REM TikTok PIG1987
echo [INFO] Running TikTok PIG1987 extractor...
"%PYTHON%" "%PROJECT_ROOT%\src\tiktok\extractors\tiktok_analytics_extractor_pig1987.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [WARNING] TikTok PIG1987 extraction failed
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [OK] TikTok PIG1987 extraction completed
)

REM TooLost (using only toolost_scraper.py as requested)
echo [INFO] Running TooLost extractor...
"%PYTHON%" "%PROJECT_ROOT%\src\toolost\extractors\toolost_scraper.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [WARNING] TooLost extraction failed
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [OK] TooLost extraction completed
)

REM Linktree
echo [INFO] Running Linktree extractor...
"%PYTHON%" "%PROJECT_ROOT%\src\linktree\extractors\linktree_analytics_extractor.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [WARNING] Linktree extraction failed
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [OK] Linktree extraction completed
)

REM MetaAds - Daily Campaigns
echo [INFO] Running MetaAds daily campaigns extractor...
"%PYTHON%" "%PROJECT_ROOT%\src\metaads\extractors\meta_daily_campaigns_extractor.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [WARNING] MetaAds daily campaigns extraction failed
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [OK] MetaAds daily campaigns extraction completed
)

REM MetaAds - Campaigns
echo [INFO] Running MetaAds campaigns extractor...
"%PYTHON%" "%PROJECT_ROOT%\src\metaads\extractors\meta_campaigns_extractor.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [WARNING] MetaAds campaigns extraction failed
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [OK] MetaAds campaigns extraction completed
)

REM MetaAds - Impressions
echo [INFO] Running MetaAds impressions extractor...
"%PYTHON%" "%PROJECT_ROOT%\src\metaads\extractors\meta_impressions_extractor.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [WARNING] MetaAds impressions extraction failed
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [OK] MetaAds impressions extraction completed
)

echo.
echo [INFO] Extraction phase complete. Failures: %EXTRACTION_FAILURES%
echo.

REM ========== CLEANERS ==========
echo [STEP 2/3] Running Data Cleaners
echo [STEP 2/3] Running Data Cleaners >> "%LOG_FILE%"
echo ========================================
echo.

REM Loop through each service directory
for /d %%P in ("%PROJECT_ROOT%\src\*") do (
    if exist "%%P\cleaners" (
        set "SERVICE=%%~nxP"
        if not "!SERVICE!"==".playwright" if not "!SERVICE!"=="common" (
            echo [INFO] Running cleaners for !SERVICE!
            
            REM Run cleaners in order
            for %%S in (landing2raw raw2staging staging2curated) do (
                if exist "%%P\cleaners\!SERVICE!_%%S.py" (
                    echo   - Running !SERVICE!_%%S.py
                    "%PYTHON%" "%%P\cleaners\!SERVICE!_%%S.py" >> "%LOG_FILE%" 2>&1
                    if errorlevel 1 (
                        echo   [WARNING] !SERVICE!_%%S.py failed
                        set /a CLEANER_FAILURES+=1
                    ) else (
                        echo   [OK] !SERVICE!_%%S.py completed
                    )
                )
            )
            echo.
        )
    )
)

echo [INFO] Cleaner phase complete. Failures: %CLEANER_FAILURES%
echo.

REM ========== SUMMARY ==========
echo [STEP 3/3] Pipeline Summary
echo ========================================
set /a TOTAL_FAILURES=%EXTRACTION_FAILURES%+%CLEANER_FAILURES%

if %TOTAL_FAILURES% EQU 0 (
    echo [SUCCESS] All pipeline components completed successfully!
) else (
    echo [WARNING] Pipeline completed with %TOTAL_FAILURES% failures.
    echo Check the log file: %LOG_FILE%
)

echo.
echo Pipeline completed at %date% %time%
echo.
echo Press any key to exit...
pause >nul

endlocal
exit /b 0