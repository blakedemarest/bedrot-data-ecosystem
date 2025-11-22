@echo off
setlocal EnableDelayedExpansion

REM ================================================================================
REM                       BEDROT DATA LAKE MASTER PIPELINE - FIXED VERSION
REM           Comprehensive ETL with Cookie Management and Health Monitoring
REM ================================================================================
REM This is the main consolidated pipeline that handles:
REM - Cookie status checking and auto-refresh
REM - Pipeline health monitoring with auto-remediation
REM - Individual service extractors
REM - Data cleaning pipeline
REM - Data warehouse ETL
REM - Comprehensive reporting
REM
REM ENHANCED LOGGING (2025-07-15):
REM - All Python scripts now run through run_with_auth_check.py
REM - Full stderr/stdout capture with timestamps
REM - Structured JSON logs in logs/pipeline_executor_structured.jsonl
REM - Grep-able error format: [ERROR] [timestamp] [service] message
REM - Check logs/pipeline_executor.log for detailed error information
REM ================================================================================

REM === EARLY ERROR CATCHING ===
if "%~1"=="--help" (
    echo Usage: run_datalake_cron.bat [--skip-extractors]
    echo.
    echo Options:
    echo   --skip-extractors    Skip data extraction, only run cleaners
    echo   --help              Show this help message
    exit /b 0
)

REM === ENVIRONMENT SETUP ===
echo.
echo ================================================================================
echo                         BEDROT DATA LAKE PIPELINE
echo                          Starting at %date% %time%
echo ================================================================================
echo.

REM Set console to UTF-8 for proper character display
chcp 65001 >nul 2>&1

REM Set Python to use UTF-8 encoding
set PYTHONIOENCODING=utf-8

REM Ensure we're in the correct directory
echo [DEBUG] Changing to project directory...
cd /d "%~dp0.."
if errorlevel 1 (
    echo [ERROR] Failed to change directory!
    pause
    exit /b 1
)
set "PROJECT_ROOT=%CD%"
echo [DEBUG] PROJECT_ROOT: %PROJECT_ROOT%

REM Capture cron job start time for reporting
set "CRON_START_TIME=%date% %time%"
set "CRON_START_DATE=%date%"
set "CRON_START_TIME_ONLY=%time%"
echo [INFO] Cron job started at: %CRON_START_TIME%

REM === Virtual Environment Management ===
echo [INFO] Checking for Python virtual environment...

REM Check for common virtual environment directories
set "VENV_DIR="
if exist "%PROJECT_ROOT%\venv\Scripts\activate.bat" set "VENV_DIR=venv"
if exist "%PROJECT_ROOT%\.venv\Scripts\activate.bat" set "VENV_DIR=.venv"
if exist "%PROJECT_ROOT%\env\Scripts\activate.bat" set "VENV_DIR=env"

REM Create virtual environment if none exists
if "%VENV_DIR%"=="" (
    echo [WARN] No virtual environment found. Creating .venv...
    python -m venv "%PROJECT_ROOT%\.venv" 2>nul
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment. Is Python installed?
        echo [ERROR] Please install Python 3.8+ and ensure it's in PATH
        exit /b 1
    )
    set "VENV_DIR=.venv"
    echo [INFO] Virtual environment created successfully
)

REM Activate the virtual environment
echo [INFO] Activating virtual environment: %VENV_DIR%
call "%PROJECT_ROOT%\%VENV_DIR%\Scripts\activate.bat" 2>nul
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    echo [ERROR] Virtual environment may be corrupted. Try deleting %VENV_DIR% and running again
    exit /b 1
)

REM Verify Python is available in venv
"%PROJECT_ROOT%\%VENV_DIR%\Scripts\python.exe" --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in virtual environment
    echo [ERROR] Virtual environment is misconfigured
    exit /b 1
)

REM Simple dependency check - check for key packages
echo [INFO] Verifying core dependencies...
set DEPS_MISSING=0

REM Check pandas
"%PROJECT_ROOT%\%VENV_DIR%\Scripts\python.exe" -c "import pandas" 2>nul
if errorlevel 1 set DEPS_MISSING=1

REM Check IPython
"%PROJECT_ROOT%\%VENV_DIR%\Scripts\python.exe" -c "import IPython" 2>nul
if errorlevel 1 set DEPS_MISSING=1

REM Check facebook_business
"%PROJECT_ROOT%\%VENV_DIR%\Scripts\python.exe" -c "import facebook_business" 2>nul
if errorlevel 1 set DEPS_MISSING=1

if %DEPS_MISSING% EQU 1 (
    echo [WARN] Some dependencies missing. Installing from requirements.txt...
    echo [INFO] This may take a few minutes...
    
    REM Check for requirements.txt
    if not exist "%PROJECT_ROOT%\requirements.txt" (
        echo [ERROR] No requirements.txt found!
        exit /b 1
    )
    
    REM Install dependencies with visible progress
    "%PROJECT_ROOT%\%VENV_DIR%\Scripts\python.exe" -m pip install -r "%PROJECT_ROOT%\requirements.txt"
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        exit /b 1
    )
    echo [INFO] Dependencies installed successfully
) else (
    echo [INFO] Core dependencies verified
)

echo [INFO] Virtual environment ready

REM Set Python executable path
set "PYTHON_EXE=%PROJECT_ROOT%\%VENV_DIR%\Scripts\python.exe"
echo [DEBUG] Using Python: %PYTHON_EXE%

REM Load environment variables from .env
if exist "%PROJECT_ROOT%\.env" (
    for /f "usebackq tokens=1,2 delims==" %%i in ("%PROJECT_ROOT%\.env") do set %%i=%%j
)

REM Expose src/ on PYTHONPATH so 'from common...' works in all child scripts
set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"

REM Create logs directory if it doesn't exist
if not exist "%PROJECT_ROOT%\logs" (
    echo Creating logs directory...
    mkdir "%PROJECT_ROOT%\logs"
)

REM Set log file for this run - use simple timestamp format
REM Using the simpler date parsing method that works reliably
set "mydate=%date:~10,4%%date:~4,2%%date:~7,2%"
set "mytime=%time:~0,2%%time:~3,2%"
set "mytime=%mytime: =0%"
set "LOG_FILE=%PROJECT_ROOT%\logs\pipeline_%mydate%_%mytime%.log"

REM Test if we can write to the log file
echo [INFO] Pipeline started at %date% %time% > "%LOG_FILE%" 2>nul
if errorlevel 1 (
    echo WARNING: Cannot write to log file. Creating alternative log...
    set "LOG_FILE=%PROJECT_ROOT%\logs\pipeline_temp.log"
    echo [INFO] Pipeline started at %date% %time% > "%LOG_FILE%"
)
echo Log file created: %LOG_FILE%
echo [INFO] Project Root: %PROJECT_ROOT% >> "%LOG_FILE%"
echo [INFO] Python Path: %PYTHONPATH% >> "%LOG_FILE%"
echo.

REM === STEP 1: COOKIE STATUS CHECK AND AUTO-REFRESH ===
echo [STEP 1/6] ============================================
echo [STEP 1/6] ============================================ >> "%LOG_FILE%"
echo [STEP 1/6] Cookie Status Check and Auto-Refresh
echo [STEP 1/6] Cookie Status Check and Auto-Refresh >> "%LOG_FILE%"
echo [STEP 1/6] ============================================
echo [STEP 1/6] ============================================ >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

echo [INFO] Checking current cookie status...
echo [INFO] Checking current cookie status... >> "%LOG_FILE%"

REM Check multiple possible locations for cookie scripts
set COOKIE_STATUS_SCRIPT=
set COOKIE_STATUS=0
if exist "%PROJECT_ROOT%\cookie_status.py" (
    set "COOKIE_STATUS_SCRIPT=%PROJECT_ROOT%\cookie_status.py"
) else if exist "%PROJECT_ROOT%\scripts\cookie_management\cookie_status.py" (
    set "COOKIE_STATUS_SCRIPT=%PROJECT_ROOT%\scripts\cookie_management\cookie_status.py"
)

if defined COOKIE_STATUS_SCRIPT (
    "%PYTHON_EXE%" "%COOKIE_STATUS_SCRIPT%" >> "%LOG_FILE%" 2>&1
    set COOKIE_STATUS=!ERRORLEVEL!
    
    if %COOKIE_STATUS% NEQ 0 (
        echo [INFO] Some cookies need refresh. Attempting auto-refresh...
        echo [INFO] Some cookies need refresh. Attempting auto-refresh... >> "%LOG_FILE%"
        
        set COOKIE_REFRESH_SCRIPT=
        if exist "%PROJECT_ROOT%\cookie_refresh.py" (
            set "COOKIE_REFRESH_SCRIPT=%PROJECT_ROOT%\cookie_refresh.py"
        ) else if exist "%PROJECT_ROOT%\scripts\cookie_management\cookie_refresh.py" (
            set "COOKIE_REFRESH_SCRIPT=%PROJECT_ROOT%\scripts\cookie_management\cookie_refresh.py"
        )
        
        if defined COOKIE_REFRESH_SCRIPT (
            "%PYTHON_EXE%" "%COOKIE_REFRESH_SCRIPT%" --refresh-all >> "%LOG_FILE%" 2>&1
            set REFRESH_RESULT=!ERRORLEVEL!
            if !REFRESH_RESULT! NEQ 0 (
                echo [WARNING] Cookie refresh encountered issues. Some services may fail.
                echo [WARNING] Cookie refresh encountered issues. Some services may fail. >> "%LOG_FILE%"
            ) else (
                echo [INFO] Cookie refresh completed successfully.
                echo [INFO] Cookie refresh completed successfully. >> "%LOG_FILE%"
            )
        ) else (
            echo [WARNING] Cookie refresh script not found. Skipping...
            echo [WARNING] Cookie refresh script not found. Skipping... >> "%LOG_FILE%"
        )
    ) else (
        echo [INFO] All cookies are healthy.
        echo [INFO] All cookies are healthy. >> "%LOG_FILE%"
    )
) else (
    echo [WARNING] Cookie status script not found. Skipping cookie check...
    echo [WARNING] Cookie status script not found. Skipping cookie check... >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

REM === STEP 2: PIPELINE HEALTH CHECK WITH AUTO-REMEDIATION ===
echo [STEP 2/6] ============================================
echo [STEP 2/6] ============================================ >> "%LOG_FILE%"
echo [STEP 2/6] Pipeline Health Check with Auto-Remediation
echo [STEP 2/6] Pipeline Health Check with Auto-Remediation >> "%LOG_FILE%"
echo [STEP 2/6] ============================================
echo [STEP 2/6] ============================================ >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

echo [INFO] Running pipeline health monitor...
echo [INFO] Running pipeline health monitor... >> "%LOG_FILE%"
set HEALTH_STATUS=0
if exist "%PROJECT_ROOT%\src\common\pipeline_health_monitor.py" (
    "%PYTHON_EXE%" "%PROJECT_ROOT%\src\common\pipeline_health_monitor.py" >> "%LOG_FILE%" 2>&1
    set HEALTH_STATUS=!ERRORLEVEL!
    
    if %HEALTH_STATUS% EQU 2 (
        echo [WARNING] Pipeline is in CRITICAL state. Review the report above.
        echo [WARNING] Pipeline is in CRITICAL state. Review the report above. >> "%LOG_FILE%"
    ) else if %HEALTH_STATUS% EQU 1 (
        echo [WARNING] Some services have issues. Auto-remediation attempted.
        echo [WARNING] Some services have issues. Auto-remediation attempted. >> "%LOG_FILE%"
    ) else (
        echo [INFO] Pipeline health check passed.
        echo [INFO] Pipeline health check passed. >> "%LOG_FILE%"
    )
) else (
    echo [WARNING] Pipeline health monitor not found. Skipping...
    echo [WARNING] Pipeline health monitor not found. Skipping... >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

REM === STEP 3: DATA EXTRACTION WITH INDIVIDUAL EXTRACTORS ===
if /I "%~1"=="--skip-extractors" (
    echo [INFO] Skipping extractors as requested...
    echo [INFO] Skipping extractors as requested... >> "%LOG_FILE%"
    goto CLEANERS
)

echo [STEP 3/6] ============================================
echo [STEP 3/6] ============================================ >> "%LOG_FILE%"
echo [STEP 3/6] Running Data Extractors
echo [STEP 3/6] Running Data Extractors >> "%LOG_FILE%"
echo [STEP 3/6] ============================================
echo [STEP 3/6] ============================================ >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

REM Ensure environment is properly set for each extractor
echo [DEBUG] Current directory: %CD% >> "%LOG_FILE%"
echo [DEBUG] PROJECT_ROOT: %PROJECT_ROOT% >> "%LOG_FILE%"
echo [DEBUG] PYTHONPATH: %PYTHONPATH% >> "%LOG_FILE%"

REM Track extraction results
set EXTRACTION_FAILURES=0

REM --- Spotify Extractor ---
echo [INFO] Running Spotify extractor...
echo [INFO] Running Spotify extractor... >> "%LOG_FILE%"
cd /d "%PROJECT_ROOT%"
"%PYTHON_EXE%" src\common\run_with_auth_check.py --script src\spotify\extractors\spotify_audience_extractor.py --service spotify --log-level INFO
set SPOTIFY_RESULT=!ERRORLEVEL!
if !SPOTIFY_RESULT! NEQ 0 (
    echo [WARNING] Spotify extraction failed (exit code: !SPOTIFY_RESULT!)
    echo [WARNING] Spotify extraction failed (exit code: !SPOTIFY_RESULT!) >> "%LOG_FILE%"
    echo [WARNING] Check logs\pipeline_executor.log for detailed error information >> "%LOG_FILE%"
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [INFO] OK: Spotify extraction completed
    echo [INFO] OK: Spotify extraction completed >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

REM --- DistroKid Extractor ---
echo [INFO] Running DistroKid extractor...
echo [INFO] Running DistroKid extractor... >> "%LOG_FILE%"
cd /d "%PROJECT_ROOT%"
"%PYTHON_EXE%" src\common\run_with_auth_check.py --script src\distrokid\extractors\dk_auth.py --service distrokid --log-level INFO
set DISTROKID_RESULT=!ERRORLEVEL!
if !DISTROKID_RESULT! NEQ 0 (
    echo [WARNING] DistroKid extraction failed (exit code: !DISTROKID_RESULT!)
    echo [WARNING] DistroKid extraction failed (exit code: !DISTROKID_RESULT!) >> "%LOG_FILE%"
    echo [WARNING] Check logs\pipeline_executor.log for detailed error information >> "%LOG_FILE%"
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [INFO] OK: DistroKid extraction completed
    echo [INFO] OK: DistroKid extraction completed >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

REM --- TikTok Extractors (Multiple Accounts) ---
echo [INFO] Running TikTok extractors...
echo [INFO] Running TikTok extractors... >> "%LOG_FILE%"

echo [INFO] - TikTok Zone A0 account...
echo [INFO] - TikTok Zone A0 account... >> "%LOG_FILE%"
cd /d "%PROJECT_ROOT%"
"%PYTHON_EXE%" src\common\run_with_auth_check.py --script src\tiktok\extractors\tiktok_analytics_extractor_zonea0.py --service tiktok-zonea0 --log-level INFO
set TIKTOK_ZONEA0_RESULT=!ERRORLEVEL!
if !TIKTOK_ZONEA0_RESULT! NEQ 0 (
    echo [WARNING] TikTok Zone A0 extraction failed (exit code: !TIKTOK_ZONEA0_RESULT!)
    echo [WARNING] TikTok Zone A0 extraction failed (exit code: !TIKTOK_ZONEA0_RESULT!) >> "%LOG_FILE%"
    echo [WARNING] Check logs\pipeline_executor.log for detailed error information >> "%LOG_FILE%"
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [INFO] OK: TikTok Zone A0 extraction completed
    echo [INFO] OK: TikTok Zone A0 extraction completed >> "%LOG_FILE%"
)

echo [INFO] - TikTok PIG1987 account...
echo [INFO] - TikTok PIG1987 account... >> "%LOG_FILE%"
cd /d "%PROJECT_ROOT%"
"%PYTHON_EXE%" src\common\run_with_auth_check.py --script src\tiktok\extractors\tiktok_analytics_extractor_pig1987.py --service tiktok-pig1987 --log-level INFO
set TIKTOK_PIG_RESULT=!ERRORLEVEL!
if !TIKTOK_PIG_RESULT! NEQ 0 (
    echo [WARNING] TikTok PIG1987 extraction failed (exit code: !TIKTOK_PIG_RESULT!)
    echo [WARNING] TikTok PIG1987 extraction failed (exit code: !TIKTOK_PIG_RESULT!) >> "%LOG_FILE%"
    echo [WARNING] Check logs\pipeline_executor.log for detailed error information >> "%LOG_FILE%"
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [INFO] OK: TikTok PIG1987 extraction completed
    echo [INFO] OK: TikTok PIG1987 extraction completed >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

REM --- TooLost Extractor ---
echo [INFO] Running TooLost extractor...
echo [INFO] Running TooLost extractor... >> "%LOG_FILE%"
cd /d "%PROJECT_ROOT%"
"%PYTHON_EXE%" src\common\run_with_auth_check.py --script src\toolost\extractors\toolost_scraper.py --service toolost --log-level INFO
set TOOLOST_RESULT=!ERRORLEVEL!
if !TOOLOST_RESULT! NEQ 0 (
    echo [WARNING] TooLost extraction failed (exit code: !TOOLOST_RESULT!)
    echo [WARNING] TooLost extraction failed (exit code: !TOOLOST_RESULT!) >> "%LOG_FILE%"
    echo [WARNING] Check logs\pipeline_executor.log for detailed error information >> "%LOG_FILE%"
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [INFO] OK: TooLost extraction completed
    echo [INFO] OK: TooLost extraction completed >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

REM --- Linktree Extractor ---
echo [INFO] Running Linktree extractor...
echo [INFO] Running Linktree extractor... >> "%LOG_FILE%"
cd /d "%PROJECT_ROOT%"
"%PYTHON_EXE%" src\common\run_with_auth_check.py --script src\linktree\extractors\linktree_analytics_extractor.py --service linktree --log-level INFO
set LINKTREE_RESULT=!ERRORLEVEL!
if !LINKTREE_RESULT! NEQ 0 (
    echo [WARNING] Linktree extraction failed (exit code: !LINKTREE_RESULT!)
    echo [WARNING] Linktree extraction failed (exit code: !LINKTREE_RESULT!) >> "%LOG_FILE%"
    echo [WARNING] Check logs\pipeline_executor.log for detailed error information >> "%LOG_FILE%"
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [INFO] OK: Linktree extraction completed
    echo [INFO] OK: Linktree extraction completed >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

REM --- MetaAds Extractors ---
echo [INFO] Running MetaAds extractors...
echo [INFO] Running MetaAds extractors... >> "%LOG_FILE%"

echo [INFO] - MetaAds Daily Campaigns...
echo [INFO] - MetaAds Daily Campaigns... >> "%LOG_FILE%"
cd /d "%PROJECT_ROOT%"
"%PYTHON_EXE%" src\common\run_with_auth_check.py --script src\metaads\extractors\meta_daily_campaigns_extractor.py --service metaads-daily --log-level INFO
set METAADS_DAILY_RESULT=!ERRORLEVEL!
if !METAADS_DAILY_RESULT! NEQ 0 (
    echo [WARNING] MetaAds Daily Campaigns extraction failed (exit code: !METAADS_DAILY_RESULT!)
    echo [WARNING] MetaAds Daily Campaigns extraction failed (exit code: !METAADS_DAILY_RESULT!) >> "%LOG_FILE%"
    echo [WARNING] Check logs\pipeline_executor.log for detailed error information >> "%LOG_FILE%"
    set /a EXTRACTION_FAILURES+=1
) else (
    echo [INFO] OK: MetaAds Daily Campaigns extraction completed
    echo [INFO] OK: MetaAds Daily Campaigns extraction completed >> "%LOG_FILE%"
)

REM MetaAds Campaigns extractor not implemented yet - skipping
REM echo [INFO] - MetaAds Campaigns...
REM echo [INFO] - MetaAds Campaigns... >> "%LOG_FILE%"
REM cd /d "%PROJECT_ROOT%"
REM "%PYTHON_EXE%" src\common\run_with_auth_check.py --script src\metaads\extractors\meta_campaigns_extractor.py --service metaads-campaigns --log-level INFO
REM set METAADS_CAMPAIGNS_RESULT=!ERRORLEVEL!
REM if %METAADS_CAMPAIGNS_RESULT% NEQ 0 (
REM     echo [WARNING] MetaAds Campaigns extraction failed (exit code: %METAADS_CAMPAIGNS_RESULT%)
REM     echo [WARNING] MetaAds Campaigns extraction failed (exit code: %METAADS_CAMPAIGNS_RESULT%) >> "%LOG_FILE%"
REM     echo [WARNING] Check logs\pipeline_executor.log for detailed error information >> "%LOG_FILE%"
REM     set /a EXTRACTION_FAILURES+=1
REM ) else (
REM     echo [INFO] OK: MetaAds Campaigns extraction completed
REM     echo [INFO] OK: MetaAds Campaigns extraction completed >> "%LOG_FILE%"
REM )

REM MetaAds Impressions extractor not implemented yet - skipping
REM echo [INFO] - MetaAds Impressions...
REM echo [INFO] - MetaAds Impressions... >> "%LOG_FILE%"
REM cd /d "%PROJECT_ROOT%"
REM "%PYTHON_EXE%" src\common\run_with_auth_check.py --script src\metaads\extractors\meta_impressions_extractor.py --service metaads-impressions --log-level INFO
REM set METAADS_IMPRESSIONS_RESULT=!ERRORLEVEL!
REM if %METAADS_IMPRESSIONS_RESULT% NEQ 0 (
REM     echo [WARNING] MetaAds Impressions extraction failed (exit code: %METAADS_IMPRESSIONS_RESULT%)
REM     echo [WARNING] MetaAds Impressions extraction failed (exit code: %METAADS_IMPRESSIONS_RESULT%) >> "%LOG_FILE%"
REM     echo [WARNING] Check logs\pipeline_executor.log for detailed error information >> "%LOG_FILE%"
REM     set /a EXTRACTION_FAILURES+=1
REM ) else (
REM     echo [INFO] OK: MetaAds Impressions extraction completed
REM     echo [INFO] OK: MetaAds Impressions extraction completed >> "%LOG_FILE%"
REM )
echo.
echo. >> "%LOG_FILE%"

echo [INFO] Data extraction phase completed. Failures: %EXTRACTION_FAILURES%
echo [INFO] Data extraction phase completed. Failures: %EXTRACTION_FAILURES% >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

:CLEANERS
REM === STEP 4: DATA CLEANING PIPELINE ===
echo [STEP 4/6] ============================================
echo [STEP 4/6] ============================================ >> "%LOG_FILE%"
echo [STEP 4/6] Running Data Cleaners
echo [STEP 4/6] Running Data Cleaners >> "%LOG_FILE%"
echo [STEP 4/6] ============================================
echo [STEP 4/6] ============================================ >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

set CLEANER_FAILURES=0

cd /d "%PROJECT_ROOT%"
for /d %%P in (src\*) do (
    REM Ignore .playwright, common, and any hidden folders
    if /I not "%%~nxP"==".playwright" if /I not "%%~nxP"=="common" if not "%%~nxP:~0,1"=="." (
        REM Run all cleaners for this platform
        if exist "%%P\cleaners" (
            echo [INFO] Running cleaners for %%~nxP
            echo [INFO] Running cleaners for %%~nxP >> "%LOG_FILE%"
            
            REM Run cleaners in order: landing2raw, raw2staging, staging2curated
            for %%S in (landing2raw raw2staging staging2curated) do (
                if exist "%%P\cleaners\%%~nxP_%%S.py" (
                    echo [INFO]   - Running %%~nxP_%%S.py
                    echo [INFO]   - Running %%~nxP_%%S.py >> "%LOG_FILE%"
                    "%PYTHON_EXE%" src\common\run_with_auth_check.py --script "%%P\cleaners\%%~nxP_%%S.py" --service "%%~nxP-%%S" --log-level INFO
                    set CLEANER_RESULT=!ERRORLEVEL!
                    if !CLEANER_RESULT! NEQ 0 (
                        echo [WARNING]   - %%~nxP_%%S.py failed
                        echo [WARNING]   - %%~nxP_%%S.py failed >> "%LOG_FILE%"
                        echo [WARNING]   - Check logs\pipeline_executor.log for detailed error information >> "%LOG_FILE%"
                        set /a CLEANER_FAILURES+=1
                    ) else (
                        echo [INFO]   OK: %%~nxP_%%S.py completed
                        echo [INFO]   OK: %%~nxP_%%S.py completed >> "%LOG_FILE%"
                    )
                )
            )
            echo.
            echo. >> "%LOG_FILE%"
        )
    )
)

echo [INFO] Data cleaning phase completed. Failures: %CLEANER_FAILURES%
echo [INFO] Data cleaning phase completed. Failures: %CLEANER_FAILURES% >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

REM === STEP 5: DATA WAREHOUSE ETL PIPELINE (DISABLED) ===
REM The warehouse ETL is not ready yet - skipping this step
REM echo [STEP 5/6] ============================================
REM echo [STEP 5/6] ============================================ >> "%LOG_FILE%"
REM echo [STEP 5/6] Running Data Warehouse ETL Pipeline
REM echo [STEP 5/6] Running Data Warehouse ETL Pipeline >> "%LOG_FILE%"
REM echo [STEP 5/6] ============================================
REM echo [STEP 5/6] ============================================ >> "%LOG_FILE%"
echo [STEP 5/6] Data Warehouse ETL - SKIPPED (not ready yet)
echo [STEP 5/6] Data Warehouse ETL - SKIPPED (not ready yet) >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

REM Set warehouse error level to 0 since we're skipping it
set WAREHOUSE_ERRORLEVEL=0

REM === STEP 6: FINAL REPORTING AND MAINTENANCE ===
echo [STEP 6/6] ============================================
echo [STEP 6/6] ============================================ >> "%LOG_FILE%"
echo [STEP 6/6] Generating Reports and Maintenance
echo [STEP 6/6] Generating Reports and Maintenance >> "%LOG_FILE%"
echo [STEP 6/6] ============================================
echo [STEP 6/6] ============================================ >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

REM Calculate pipeline end time
set "CRON_END_TIME=%date% %time%"

REM Run final health check with cron statistics
echo [INFO] Running final health check with cron statistics...
echo [INFO] Running final health check with cron statistics... >> "%LOG_FILE%"

REM Calculate total failures for the report
set /a TOTAL_FAILURES=%EXTRACTION_FAILURES%+%CLEANER_FAILURES%

if exist "%PROJECT_ROOT%\src\common\pipeline_health_monitor.py" (
    "%PYTHON_EXE%" "%PROJECT_ROOT%\src\common\pipeline_health_monitor.py" --cron-start-time "%CRON_START_TIME%" --cron-end-time "%CRON_END_TIME%" --extraction-failures %EXTRACTION_FAILURES% --cleaner-failures %CLEANER_FAILURES% --total-failures %TOTAL_FAILURES% >> "%LOG_FILE%" 2>&1
    
    REM Check if HTML report was generated successfully
    if exist "%PROJECT_ROOT%\pipeline_health_report.html" (
        echo [INFO] Pipeline health report generated successfully
        echo [INFO] Pipeline health report generated successfully >> "%LOG_FILE%"
        
        REM Display report location
        echo [INFO] Report location: %PROJECT_ROOT%\pipeline_health_report.html
        echo [INFO] Report location: %PROJECT_ROOT%\pipeline_health_report.html >> "%LOG_FILE%"
    ) else (
        echo [WARNING] Pipeline health report was not generated
        echo [WARNING] Pipeline health report was not generated >> "%LOG_FILE%"
    )
)

REM Generate visual dashboard if available
if exist "%PROJECT_ROOT%\src\common\cookie_refresh\dashboard.py" (
    echo [INFO] Generating visual dashboard...
    echo [INFO] Generating visual dashboard... >> "%LOG_FILE%"
    "%PYTHON_EXE%" src\common\run_with_auth_check.py --script src\common\cookie_refresh\dashboard.py --service dashboard --log-level INFO -- --output pipeline_status.html
)

REM Archive old logs (keep last 30 days)
echo [INFO] Archiving old logs...
echo [INFO] Archiving old logs... >> "%LOG_FILE%"
forfiles /p "%PROJECT_ROOT%\logs" /s /m *.log /d -30 /c "cmd /c del @path" 2>nul

echo.
echo. >> "%LOG_FILE%"
echo ================================================================================
echo ================================================================================ >> "%LOG_FILE%"
echo                           PIPELINE EXECUTION SUMMARY
echo                           PIPELINE EXECUTION SUMMARY >> "%LOG_FILE%"
echo ================================================================================
echo ================================================================================ >> "%LOG_FILE%"
echo.
echo [TIMING]
echo [TIMING] >> "%LOG_FILE%"
echo   Started:   %CRON_START_TIME%
echo   Started:   %CRON_START_TIME% >> "%LOG_FILE%"
echo   Completed: %CRON_END_TIME%
echo   Completed: %CRON_END_TIME% >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

echo [RESULTS]
echo [RESULTS] >> "%LOG_FILE%"
echo   Extraction Phase:
echo   Extraction Phase: >> "%LOG_FILE%"
echo     - Services Attempted: 6 (Spotify, DistroKid, TikTok x2, TooLost, Linktree, MetaAds)
echo     - Services Attempted: 6 (Spotify, DistroKid, TikTok x2, TooLost, Linktree, MetaAds) >> "%LOG_FILE%"
echo     - Failures: %EXTRACTION_FAILURES%
echo     - Failures: %EXTRACTION_FAILURES% >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"
echo   Cleaning Phase:
echo   Cleaning Phase: >> "%LOG_FILE%"
echo     - Cleaners Run: Multiple (landing2raw, raw2staging, staging2curated)
echo     - Cleaners Run: Multiple (landing2raw, raw2staging, staging2curated) >> "%LOG_FILE%"
echo     - Failures: %CLEANER_FAILURES%
echo     - Failures: %CLEANER_FAILURES% >> "%LOG_FILE%"
echo.
echo. >> "%LOG_FILE%"

set /a TOTAL_FAILURES=%EXTRACTION_FAILURES%+%CLEANER_FAILURES%
if !WAREHOUSE_ERRORLEVEL! NEQ 0 set /a TOTAL_FAILURES+=1

echo [OVERALL STATUS]
echo [OVERALL STATUS] >> "%LOG_FILE%"
if %TOTAL_FAILURES% EQU 0 (
    echo   Result: SUCCESS - All pipeline components completed successfully!
    echo   Result: SUCCESS - All pipeline components completed successfully! >> "%LOG_FILE%"
    set "PIPELINE_STATUS=SUCCESS"
    set "STATUS_COLOR=green"
) else (
    echo   Result: WARNING - Pipeline completed with %TOTAL_FAILURES% failures
    echo   Result: WARNING - Pipeline completed with %TOTAL_FAILURES% failures >> "%LOG_FILE%"
    set "PIPELINE_STATUS=WARNING"
    set "STATUS_COLOR=orange"
)
echo.
echo. >> "%LOG_FILE%"

echo [GENERATED REPORTS]
echo [GENERATED REPORTS] >> "%LOG_FILE%"
echo   - Log File: %LOG_FILE%
echo   - Log File: %LOG_FILE% >> "%LOG_FILE%"

REM Check and display pipeline health report status
if exist "%PROJECT_ROOT%\pipeline_health_report.html" (
    echo   - Health Report: %PROJECT_ROOT%\pipeline_health_report.html [READY]
    echo   - Health Report: %PROJECT_ROOT%\pipeline_health_report.html [READY] >> "%LOG_FILE%"
    echo     ^> Open in browser to view detailed health metrics and visualizations
    echo     ^> Open in browser to view detailed health metrics and visualizations >> "%LOG_FILE%"
) else (
    echo   - Health Report: Not generated
    echo   - Health Report: Not generated >> "%LOG_FILE%"
)

REM Check for JSON report
if exist "%PROJECT_ROOT%\pipeline_health_report.json" (
    echo   - JSON Report: %PROJECT_ROOT%\pipeline_health_report.json [READY]
    echo   - JSON Report: %PROJECT_ROOT%\pipeline_health_report.json [READY] >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"

echo [RECOMMENDED ACTIONS]
echo [RECOMMENDED ACTIONS] >> "%LOG_FILE%"
if %TOTAL_FAILURES% EQU 0 (
    echo   1. No immediate action required - pipeline healthy
    echo   1. No immediate action required - pipeline healthy >> "%LOG_FILE%"
    echo   2. Review the HTML health report for detailed metrics
    echo   2. Review the HTML health report for detailed metrics >> "%LOG_FILE%"
) else (
    echo   1. IMPORTANT: Review the HTML health report for failure details
    echo   1. IMPORTANT: Review the HTML health report for failure details >> "%LOG_FILE%"
    echo   2. Check extractor logs for real errors; manual auth reminders are informational only
    echo   2. Check extractor logs for real errors; manual auth reminders are informational only >> "%LOG_FILE%"
    echo   3. Re-run failed extractors manually if an actual error was recorded:
    echo   3. Re-run failed extractors manually if an actual error was recorded: >> "%LOG_FILE%"
    echo      python src\common\run_with_auth_check.py --script [extractor_path]
    echo      python src\common\run_with_auth_check.py --script [extractor_path] >> "%LOG_FILE%"
)
echo.
echo. >> "%LOG_FILE%"
echo ================================================================================
echo ================================================================================ >> "%LOG_FILE%"

REM Auto-open the HTML report if it exists and there were failures
if exist "%PROJECT_ROOT%\pipeline_health_report.html" (
    if %TOTAL_FAILURES% GTR 0 (
        echo.
        echo [ACTION] Opening pipeline health report in browser due to failures...
        echo [ACTION] Opening pipeline health report in browser due to failures... >> "%LOG_FILE%"
        start "" "%PROJECT_ROOT%\pipeline_health_report.html"
    ) else (
        echo.
        echo [INFO] Pipeline health report available at:
        echo [INFO] Pipeline health report available at: >> "%LOG_FILE%"
        echo        %PROJECT_ROOT%\pipeline_health_report.html
        echo        %PROJECT_ROOT%\pipeline_health_report.html >> "%LOG_FILE%"
    )
)

endlocal
echo.
echo [INFO] Press any key to exit...
pause >nul
