# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with the BEDROT Data Lake. Last updated: 2025-08-04

## Critical Path Warning ⚠️

AI agents often confuse these directories:

**WRONG**: `C:\Users\Earth\BEDROT PRODUCTIONS\BEDROT DATA LAKE`  
**CORRECT**: `C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake`

The correct ecosystem path is: `C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\`
- Data Lake: `bedrot-data-ecosystem\data_lake\`
- Data Warehouse: `bedrot-data-ecosystem\data-warehouse\`

Always verify you're in the correct directory before running commands!

## Project Overview

The BEDROT Data Lake is a production-grade ETL platform processing music industry data through a structured 6-zone architecture.

### Zone Architecture
1. **1_landing/** - Raw data ingestion, timestamped files from extractors
2. **2_raw/** - Validated, immutable copies in NDJSON/CSV format
3. **3_staging/** - Cleaned, transformed, standardized data
4. **4_curated/** - Business-ready datasets for analytics/dashboards
5. **5_archive/** - Long-term storage (7+ year retention)
6. **6_automated_cronjob/** - Master pipeline orchestration scripts

### Service Implementation Status
| Service | Extractors | Cleaners | Priority | Critical Notes |
|---------|------------|----------|----------|----------------|
| TooLost | ✅ Multiple variants | ✅ All 3 | CRITICAL | JWT expires every 7 days! |
| Spotify | ✅ audience_extractor | ✅ All 3 | HIGH | Artists API |
| TikTok | ✅ 2 accounts | ✅ All 3 | HIGH | zonea0 + pig1987 |
| DistroKid | ✅ dk_auth | ✅ All 3 | MEDIUM | Streams + financials |
| Linktree | ✅ analytics_extractor | ✅ All 3 | MEDIUM | GraphQL |
| MetaAds | ✅ daily_campaigns | ✅ All 3 | LOW | Graph API |
| Instagram | ❌ Empty dirs | ❌ | - | Not implemented |
| YouTube | ❌ Empty dirs | ❌ | - | Not implemented |
| MailChimp | ❌ Empty dirs | ❌ | - | Not implemented |

The ecosystem serves as the central repository for BEDROT PRODUCTIONS' streaming analytics, marketing metrics, and audience data.

## Important Context: Semi-Manual Authentication Design

### Authentication Philosophy
**CRITICAL**: The BEDROT Data Lake operates as a **semi-manual system by design**. This is not a limitation but a deliberate choice for compliance and security:

1. **Extractors NEVER authenticate automatically** - All authentication is handled manually by the user
2. **2FA Compliance** - All services use two-factor authentication, requiring human interaction
3. **Cookie Management is Convenience, Not Critical** - Expired cookies mean manual re-authentication, not system failure
4. **User-Driven Process** - The system respects service terms by requiring explicit user authentication

### Cookie Management Role
The cookie system exists to **reduce** manual work, not eliminate it:
- **Storage**: Preserves authentication state between runs
- **Monitoring**: Warns when cookies are expiring
- **Refresh Assistance**: Helps guide re-authentication when needed
- **NOT Critical Infrastructure**: Cookie failures are inconveniences, not emergencies

### Interpreting Cookie-Related Failures
When you see extraction failures due to cookies:
1. **This is EXPECTED behavior** - The system is working as designed
2. **Not a critical error** - Just means manual authentication is needed
3. **Part of the workflow** - Semi-manual means user intervention is normal
4. **Compliance-friendly** - Ensures we're not automating around security measures

## Development Commands

### Testing
```bash
# Run all tests with coverage
pytest -ra --cov=src --cov-report=term-missing

# Run tests for specific service
pytest tests/spotify/ -v

# Run cookie refresh tests
pytest tests/test_cookie_refresh.py -v
pytest tests/test_integration.py -v
pytest tests/test_e2e_scenarios.py -v
```

### Code Quality
```bash
# Format code
black src/
isort src/

# Lint code  
flake8 src/
mypy src/
```

### Cookie Refresh System (NEW)

#### Automated Cookie Management
```bash
# Check cookie status for all services
python src/common/cookie_refresh/check_status.py

# Manually refresh cookies for a specific service
python src/common/cookie_refresh/manual_refresh.py --service spotify

# Start cookie refresh scheduler
python src/common/cookie_refresh/scheduler.py

# Configure automatic refresh
python src/common/cookie_refresh/configure.py
```

#### Cookie Refresh Monitoring
```bash
# View refresh dashboard (http://localhost:8080)
python src/common/cookie_refresh/start_dashboard.py

# Check refresh history
python src/common/cookie_refresh/view_history.py --service all --days 7

# Test notifications
python src/common/cookie_refresh/test_notifications.py
```

### Data Pipeline Execution

#### New Semi-Manual Pipeline with Authentication (Recommended)
```bash
# Interactive mode - prompts for manual auth when needed
cd "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"
cronjob\run_bedrot_pipeline.bat

# Automated mode - skips services needing auth
cronjob\run_bedrot_pipeline.bat --automated

# Alternative with data warehouse ETL
cronjob\run_pipeline_with_auth.bat
```

#### Legacy Pipeline Commands
```bash
# Run full data lake pipeline (Windows)
data_lake/cronjob/run_datalake_cron.bat

# Run pipeline without extractors (cleaners only)
data_lake/cronjob/run_datalake_cron_no_extractors.bat

# Manual Python execution requires PROJECT_ROOT environment variable
set PROJECT_ROOT=%cd%
python src/spotify/extractors/spotify_audience_extractor.py
```

#### Health Monitoring & Diagnostics
```bash
# Check pipeline health
python src\common\pipeline_health_monitor.py

# Check authentication status
python src\common\run_with_auth_check.py --check-only

# Run specific services with auth check
python src\common\run_with_auth_check.py spotify toolost

# Test pipeline components
python test_pipeline_components.py
```

## Architecture

### Data Lake Zones
The data lake follows a multi-zone architecture:
- `landing/` - Raw ingested data (HTML, JSON, CSV files)
- `raw/` - Validated and standardized data (NDJSON, CSV)
- `staging/` - Cleaned and processed data
- `curated/` - Business-ready datasets for analytics
- `archive/` - Historical snapshots with timestamps

### Data Warehouse
The data warehouse (`../data-warehouse/`) provides:
- **SQLite Database**: `bedrot_analytics.db` with 3NF normalized schema
- **10 Tables**: Artists, Platforms, Tracks, Campaigns, Financial Transactions, etc.
- **ETL Pipelines**: Located in `data_lake/etl/` directory
- **Business Analytics**: Ready-to-query performance metrics and financial data

### Data Lake ETL Organization
Code is organized by platform under `src/<platform>/`:
- `extractors/` - Scripts that download/scrape data into `landing/`
- `cleaners/` - Scripts that promote data through zones (landing→raw→staging→curated)
- `cookies/` - JSON cookie files for Playwright-based extractors

Example platforms: `distrokid/`, `spotify/`, `tiktok/`, `metaads/`, `linktree/`, `toolost/`

### Repository Structure
The data_lake root directory is organized as follows:
- `src/` - Source code for extractors, cleaners, and common utilities
- `tests/` - Test suites for all services and components (includes Meta API tests)
- `sandbox/` - Experimental and exploratory code
  - `analysis/` - Business metrics and revenue analysis scripts
  - `verified/` - Tested and verified Jupyter notebooks
- `scripts/` - Utility scripts and tools
  - `cookie_management/` - Cookie refresh and status scripts
  - `deployment/` - Deployment and environment setup scripts
  - `testing/` - Test runners and validation scripts
- `docs/` - Documentation and architecture diagrams (includes data flow diagrams)
- `etl/` - Data warehouse ETL pipelines
- `6_automated_cronjob/` - Automated pipeline execution scripts
- `config/` - Configuration files for various services
- `logs/` - Pipeline execution and error logs

### Data Warehouse ETL Pipelines
Located in `etl/` directory:
- `etl_master_data.py` - Load artists, platforms, and tracks (master data)
- `etl_financial_data.py` - Load financial transactions from DistroKid and Capitol One
- `etl_streaming_performance.py` - Load Spotify audience and performance metrics
- `etl_social_media_performance.py` - Load TikTok analytics and engagement data
- `run_all_etl.py` - Master orchestrator that runs all pipelines in sequence

### Automated Pipelines
**Data Lake Pipeline** (`cronjob/run_datalake_cron.bat`) automatically:
1. Creates/activates Python virtual environment
2. Loops through all `src/<platform>/` directories
3. Executes all `extractors/*.py` scripts
4. Executes all `cleaners/*.py` scripts in order
5. Generates final consolidated reports

**Data Warehouse Pipeline** (`etl/run_all_etl.py`) automatically:
1. Loads master data (artists, tracks, platforms)
2. Processes financial transactions
3. Loads streaming performance metrics
4. Loads social media performance data
5. Generates analytics-ready database

## Key Conventions

### Environment Setup
- All scripts expect `PROJECT_ROOT` environment variable (set via `.env`)
- Virtual environment: `.venv/` in project root
- Python path includes `src/` for `from common...` imports

### Cleaner Naming Pattern
Follow strict naming for automatic execution order:
- `<service>_landing2raw.py`
- `<service>_raw2staging.py` 
- `<service>_staging2curated.py`

### File Formats
- Raw data: NDJSON for structured data, CSV for tabular
- All files: UTF-8 encoding
- Timestamps: ISO format `YYYYMMDD_HHMMSS` in filenames

### Service Integration
To add a new data source:
1. Create `src/<service>/extractors/`, `src/<service>/cleaners/`, `src/<service>/cookies/`
2. Follow extractor template using Playwright/requests
3. Implement three cleaner scripts following naming convention
4. Add placeholder tests in `tests/<service>/`
5. No manual registration required - cron job auto-discovers new services

### Common Utilities
- `common/cookies.py` - Cookie loading for Playwright extractors
- `common/utils/hash_helpers.py` - Data deduplication utilities
- `common/extractors/tiktok_shared.py` - Shared TikTok functionality
- `etl/` - Data warehouse ETL pipelines and orchestration

## Data Quality
- Use pandas/polars for data processing
- Implement data validation in cleaner scripts
- Archive old data before overwriting curated files
- Log all ETL operations with timestamps
- Normalize artist names consistently across all pipelines
- Handle ISRC/UPC code uniqueness constraints
- Deduplicate tracks and performance records

### ⚠️ CRITICAL: Avoiding Double-Counting Spotify Streams
**IMPORTANT**: The data lake contains Spotify stream data from TWO different sources:
1. **tidy_daily_streams.csv** - Contains `spotify_streams` column from distributor data (DistroKid/TooLost)
2. **spotify_audience_curated_*.csv** - Contains `streams_28d` from Spotify for Artists API

**DO NOT combine these datasets** when calculating total Spotify streams - you would be double-counting!
- Use `tidy_daily_streams` for cross-platform analysis (Spotify + Apple Music)
- Use `spotify_audience_curated` for Spotify-specific metrics and demographics
- NEVER add `tidy_daily_streams.spotify_streams` + `spotify_audience_curated.streams_28d`

## Dependencies
Key packages in `requirements.txt`:
- Data processing: pandas, polars, pyarrow
- Database: sqlite3 (built-in), sqlalchemy
- Web scraping: playwright, requests  
- Testing: pytest, pytest-cov
- Code quality: black, isort, flake8, mypy

Data warehouse dependencies in `../data-warehouse/requirements.txt`:
- pandas, numpy, python-dateutil (minimal set for ETL processing)

## Current Pipeline Status (July 8, 2025)

### Critical Issues Resolved
1. **TikTok Zone A0 Authentication**: Fixed QR code requirement by properly configuring cookies
   - Zone A0 cookies now stored at: `src/tiktok/cookies/tiktok_cookies_zonea0.json`
   - Both pig1987 and zone.a0 accounts now work without manual QR code
   
2. **TooLost Data Pipeline**: Fixed directory mismatch issue
   - Cleaner (`toolost_raw2staging.py`) now checks both `raw/toolost/` and `raw/toolost/streams/`
   - Latest data (July 4) can now flow through to curated zone
   - JWT token expires every 7 days - requires weekly refresh

3. **Semi-Manual Authentication Workflow**: Implemented comprehensive solution
   - `run_bedrot_pipeline.bat` - Interactive pipeline with auth checks
   - `pipeline_health_monitor.py` - Shows data freshness and cookie status
   - `run_with_auth_check.py` - Manages authentication for all services

### Current Data Status
- **DistroKid**: Up to date (July 4 data processed)
- **Spotify**: Data current but needs cleaners run
- **TikTok**: 13 days old, needs extraction and cleaning
- **TooLost**: 32 days old, cookies expired (last success: May 26)
- **Linktree**: 5 days old, needs cleaning
- **MetaAds**: 13 days old, no cookies configured

### Authentication Status
- ✅ **Spotify**: Cookies valid (21 days old, max 30)
- ✅ **TikTok**: Cookies fresh (0 days old)
- ✅ **Linktree**: Cookies valid (26 days old, max 30)
- ❌ **TooLost**: Cookies expired (26 days old, max 7)
- ❌ **DistroKid**: Cookies expired (26 days old, max 14)
- ❌ **MetaAds**: No cookies found

### Data Warehouse Status
- **Database**: `../data-warehouse/bedrot_analytics.db` (160 KB)
- **Artists**: 5 (PIG1987, ZONE A0, IWARY, collaborations)
- **Tracks**: 19 (with ISRC codes)
- **Streaming Records**: 1,800 (Spotify performance data)
- **Social Media Records**: 765 (TikTok analytics)
- **Platforms**: 10 (Spotify, TikTok, Meta Ads, etc.)

## Understanding Log Outputs

### Log File Locations
The data pipeline generates several types of logs in the `logs/` directory:

1. **Pipeline Execution Logs** (`pipeline_YYYYMMDD_HHMM.log`)
   - Main pipeline execution log from cron job runs
   - Contains step-by-step execution details
   - Includes cookie checks, extractor runs, cleaner runs, and health reports

2. **Pipeline Executor Logs** (Enhanced logging as of 2025-07-15)
   - `pipeline_executor.log` - Detailed execution log with timestamps
   - `pipeline_executor_errors.log` - Error-only log for quick debugging
   - `pipeline_executor_structured.jsonl` - JSON-formatted logs for programmatic parsing

3. **Service-Specific Logs**
   - `cookie_refresh.log` - Cookie refresh operations
   - `bedrot_pipeline.log` - Semi-manual pipeline runs
   - `bedrot_pipeline_errors.log` - Error-only view

### Reading Pipeline Logs

#### Main Pipeline Log Structure
```
[INFO] Pipeline started at Thu 07/24/2025  4:30:03.32 
[STEP 1/6] Cookie Status Check and Auto-Refresh
[STEP 2/6] Pipeline Health Check with Auto-Remediation
[STEP 3/6] Running Data Extractors
[STEP 4/6] Running Data Cleaners
[STEP 5/6] Data Warehouse ETL - SKIPPED
[STEP 6/6] Generating Reports and Maintenance
```

#### Error Identification
Look for these patterns:
- `[ERROR]` - Critical failures requiring attention
- `[WARNING]` - Non-critical issues (e.g., expired cookies)
- `[FAIL]` - Service-specific failures
- Exit codes: Non-zero values indicate failures

#### Structured Log Format (JSONL)
Each line in `pipeline_executor_structured.jsonl` contains:
```json
{
  "timestamp": "2025-07-24T11:34:32.493542Z",
  "level": "ERROR",
  "service": "spotify",
  "message": "Script execution failed",
  "correlation_id": "unique-id",
  "exit_code": 1,
  "duration_seconds": 62.26
}
```

### Interpreting Common Log Patterns

#### Cookie Expiration Warnings
```
SPOTIFY
----------------------------------------
  spotify: EXPIRED: 9 cookies expired - refresh needed!
  Last updated: 2025-07-11 08:18 (12 days ago)
```
**Action**: Run the extractor manually or use cookie refresh system

#### Extraction Failures
```
[WARNING] Spotify extraction failed (exit code: 1)
[WARNING] Check logs\pipeline_executor.log for detailed error information
```
**Action**: Check `pipeline_executor.log` for full error traceback

#### Health Check Results
```
SERVICE HEALTH SUMMARY (Sorted by Priority)
--------------------------------------------------------------------------------
Service      Status   Score  Priority   Issues                        
--------------------------------------------------------------------------------
toolost      [FAIL]     0%   CRITICAL   12d STALE, 3 blocks           
spotify      [XX]      52%   HIGH       12d STALE, 1 blocks
```
**Interpretation**:
- `[FAIL]` = Service completely broken
- `[XX]` = Service partially working but needs attention
- `[OK]` = Service functioning normally
- Score % = Overall health (100% is perfect)
- STALE = Data age exceeds threshold
- blocks = Number of data processing bottlenecks

### Quick Debugging Commands

```bash
# View latest pipeline log
type logs\pipeline_*.log | more

# Search for errors in all logs
findstr /i "error" logs\*.log

# View structured logs with jq (if installed)
jq '. | select(.level=="ERROR")' logs\pipeline_executor_structured.jsonl

# Get last 50 errors
powershell -Command "Get-Content logs\pipeline_executor_errors.log -Tail 50"

# Find specific service errors
findstr /i "spotify.*failed" logs\pipeline_*.log
```

### Log Monitoring Best Practices

1. **Check logs after each pipeline run** for warnings/errors
2. **Monitor structured logs** for programmatic alerting
3. **Archive old logs** (automatic after 30 days)
4. **Use correlation IDs** to trace specific execution flows
5. **Check both stdout and stderr** in executor logs

### Common Error Resolutions

| Error Pattern | Likely Cause | Resolution | Severity |
|--------------|--------------|------------|----------|
| `TimeoutError: Page.wait_for_selector` | Page didn't load or login required | Run manual auth - this is NORMAL | Low |
| `No cookies found` | Missing authentication | Run extractor manually to login | Low |
| `Multiple extraction failures` | Cookies expired across services | Batch re-authenticate all services | Low |
| `attempted relative import` | Script run incorrectly | Use proper execution method | High |
| `no healthy upstream` | Network/proxy issue | Check network, disable proxy | High |
| `STALE data` | Extraction hasn't run recently | Run specific extractor with auth | Medium |

### Understanding Failure Severity

**Low Severity (Cookie/Auth Issues)**:
- Expected in semi-manual system
- Requires user intervention
- Not a system failure
- Part of normal workflow

**High Severity (System Issues)**:
- Actual infrastructure problems
- Code/configuration errors
- Network connectivity issues
- These need immediate fixing

**Medium Severity (Data Issues)**:
- Data quality concerns
- Processing bottlenecks
- May indicate auth OR system issues

## Recent Improvements (August 2025)

### New Pipeline Tools
1. **Pipeline Health Monitor** (`src/common/pipeline_health_monitor.py`)
   - Comprehensive health scores for each service
   - Data freshness tracking across all zones
   - Cookie expiration warnings
   - Bottleneck detection
   - Actionable recommendations

2. **Authentication Wrapper** (`src/common/run_with_auth_check.py`)
   - Checks cookie freshness before running extractors
   - Prompts for manual auth when needed
   - Supports both interactive and automated modes
   - Service-specific cookie expiration tracking

3. **Improved Batch Files**
   - `run_pipeline_windows.bat` - Simple test pipeline for Spotify
   - `run_pipeline_simple.bat` - Basic pipeline runner
   - `6_automated_cronjob/run_datalake_cron.bat` - Master consolidated pipeline with 6-step execution
   - `6_automated_cronjob/run_datalake_cron_no_extractors.bat` - Cleaners-only variant

### Cookie Management
- **TikTok**: Now supports multiple accounts (zone.a0, pig1987)
- **Cookie Helper**: `src/tiktok/manage_cookies.py` for cookie management
- **Per-Service Storage**: Cookies stored in `src/<service>/cookies/`
- **Expiration Tracking**: Different expiration times per service

## Cookie Refresh Automation System

### Overview
The Cookie Refresh System provides automated management of authentication cookies across all services, eliminating manual intervention for most authentication scenarios.

### Key Features
- **Automated Refresh**: Scheduled checks and proactive cookie renewal
- **2FA Support**: Interactive handling of two-factor authentication
- **Service Strategies**: Custom refresh logic per service (OAuth, Playwright, JWT)
- **Monitoring Dashboard**: Real-time status and history tracking
- **Notifications**: Email/Slack alerts for failures and expirations
- **Concurrent Processing**: Efficient parallel refresh with configurable limits

### Quick Start
```bash
# Check cookie status for all services
cd data_lake
python -m common.cookie_refresh.refresher --check-only

# Refresh all services that need it
python -m common.cookie_refresh.refresher

# Force refresh specific service
python -m common.cookie_refresh.refresher --service spotify

# View dashboard (if dashboard.py exists)
python src/common/cookie_refresh/dashboard.py
# Access at http://localhost:8080
```

### Service-Specific Cookie Expiration
| Service | Strategy | Max Age | Refresh Interval | Priority | Notes |
|---------|----------|---------|------------------|----------|-------|
| TooLost | JWT Manual | 7 days | 5 days | CRITICAL | Requires weekly manual refresh |
| Spotify | OAuth Manual | 30 days | 7 days | HIGH | Artists API access |
| TikTok Zone A0 | QR/Manual | 30 days | 7 days | HIGH | Account: zone.a0 |
| TikTok PIG1987 | QR/Manual | 30 days | 7 days | HIGH | Account: pig1987 |
| DistroKid | Automated | 90 days | 10 days | MEDIUM | Auto-login with credentials |
| Linktree | Standard | 30 days | 14 days | MEDIUM | GraphQL analytics |
| MetaAds | OAuth | 60 days | 30 days | LOW | Facebook Graph API |

### Manual Cookie Refresh
```bash
# Check cookie status
python src/common/cookie_refresh/check_status.py

# Refresh specific service
python src/common/cookie_refresh/manual_refresh.py --service toolost

# Force refresh all expired
python src/common/cookie_refresh/manual_refresh.py --all --force

# Test refresh without saving (dry run)
python src/common/cookie_refresh/manual_refresh.py --service spotify --dry-run
```

### Configuration
Edit `config/cookie_refresh_config.json`:
```json
{
  "global": {
    "check_interval_minutes": 60,
    "max_retry_attempts": 3,
    "notification_channels": ["email", "slack"]
  },
  "services": {
    "spotify": {
      "enabled": true,
      "refresh_interval_hours": 168,
      "strategy": "oauth",
      "priority": 1
    }
  }
}
```

### Windows Task Scheduler Integration
```powershell
# Create scheduled task (run as Administrator)
Register-ScheduledTask -TaskName "BEDROT Cookie Refresh" `
  -Action (New-ScheduledTaskAction -Execute "python.exe" `
    -Argument "src\common\cookie_refresh\scheduler.py") `
  -Trigger (New-ScheduledTaskTrigger -Daily -At 3:00AM) `
  -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable)
```

### Troubleshooting Cookie Issues
```bash
# View detailed logs
python src/common/cookie_refresh/view_logs.py --service spotify --verbose

# Test authentication without refresh
python src/common/cookie_refresh/test_auth.py --service tiktok

# Clear and retry
python src/common/cookie_refresh/clear_cookies.py --service toolost
python src/common/cookie_refresh/manual_refresh.py --service toolost

# Restore from backup
python src/common/cookie_refresh/restore_backup.py --service distrokid --latest
```

### Cookie Refresh Strategies

#### OAuth Strategy (Spotify, MetaAds)
- Uses refresh tokens for seamless renewal
- No user interaction required
- Handles token expiration gracefully

#### Playwright Strategy (TikTok, Linktree)
- Browser automation for login flows
- Supports 2FA with user prompts
- Handles captchas and security checks

#### JWT Strategy (DistroKid, TooLost)
- API-based authentication
- Monitors JWT expiration in cookies
- Automatic token renewal

### Monitoring & Alerts
```bash
# Check system health
python src/common/cookie_refresh/health_check.py

# View refresh metrics
python src/common/cookie_refresh/view_metrics.py --days 30

# Configure notifications
python src/common/cookie_refresh/setup_notifications.py
```

### Best Practices
1. **Regular Monitoring**: Check dashboard weekly for service health
2. **Proactive Refresh**: Don't wait for expiration - refresh at 80% of max age
3. **Backup Strategy**: Always backup cookies before manual changes
4. **Security**: Use environment variables for credentials, never commit
5. **Testing**: Run dry-run tests before production changes

### Known Issues & Next Steps
1. **Immediate Actions Needed**:
   - Refresh TooLost cookies (run `python src/toolost/extractors/toolost_scraper.py`)
   - Refresh DistroKid cookies (run `python src/distrokid/extractors/dk_auth.py`)
   - Configure MetaAds authentication
   - Run cleaners for all services to catch up on processing

2. **Data Quality Improvements**:
   - Several services have data stuck in landing/raw zones
   - Need to run full cleaner pipeline to promote to curated
   - Consider automating cookie refresh reminders

3. **Future Enhancements**:
   - Implement automated cookie refresh notifications
   - Add data quality metrics to health monitor
   - Create unified dashboard for pipeline status
   - Implement retry logic for failed extractors