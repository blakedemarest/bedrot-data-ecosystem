# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Path Warning ⚠️

**CRITICAL**: The correct ecosystem path has changed!

**OLD/WRONG**: `C:\Users\Earth\BEDROT PRODUCTIONS\BEDROT DATA LAKE`  
**NEW/CORRECT**: `C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem`

Component paths:
- Data Lake: `bedrot-data-ecosystem\data_lake\`
- Data Warehouse: `bedrot-data-ecosystem\data_warehouse\`
- Dashboard: `bedrot-data-ecosystem\data_dashboard\`

Always verify you're in the correct directory before running commands!

## Project Overview

BEDROT Data Ecosystem is a production-grade analytics infrastructure for music industry data, consisting of three integrated components:

- **Data Lake** (`data_lake/`): Multi-zone ETL architecture for ingesting data from Spotify, TikTok, Meta Ads, DistroKid, Linktree, TooLost, YouTube, MailChimp
- **Data Warehouse** (`data_warehouse/`): SQLite-based analytical database with normalized tables for streaming, financial, and social media metrics  
- **Data Dashboard** (`data_dashboard/`): Real-time Next.js/FastAPI dashboard displaying 20+ KPIs with live WebSocket updates

## Development Commands

### Data Lake

```bash
# Testing
pytest -ra --cov=src --cov-report=term-missing
pytest tests/spotify/ -v  # Service-specific tests

# Code Quality
black src/
isort src/
flake8 src/
mypy src/

# Pipeline Execution - RECOMMENDED
cd data_lake
run_pipeline_windows.bat  # Full pipeline with all services
run_pipeline_simple.bat   # Simplified pipeline execution
# Alternative: Use automated cronjob scripts
6_automated_cronjob\run_datalake_cron.bat  # Full automated pipeline
6_automated_cronjob\run_datalake_cron_no_extractors.bat  # Cleaners only

# Health Monitoring
python src\common\pipeline_health_monitor.py
python src\common\run_with_auth_check.py --check-only

# Cookie Management
python src/common/cookie_refresh/check_status.py
python src/common/cookie_refresh/manual_refresh.py --service spotify
python src/common/cookie_refresh/scheduler.py  # Automated refresh

# Cookie Refresh System Components
# Located in src/common/cookie_refresh/
# - strategies/ - Service-specific refresh implementations
# - dashboard.py - Web dashboard for cookie status
# - refresher.py - Main refresh orchestration
# - notifier.py - Notification system for expiring cookies
```

### Data Dashboard

```bash
# Frontend (Next.js)
cd data_dashboard
npm install
npm run dev        # Port 3000 with custom Socket.IO server
npm run build
npm run start
npm run lint
npm run type-check

# Backend (FastAPI)
cd data_dashboard/backend
pip install -r requirements.txt
python main.py     # Port 8000 with WebSocket support
```

### Data Warehouse

```bash
cd data_warehouse
# Currently being reinitialized - structure pending
# Virtual environment preserved at .venv/
# Requirements preserved at requirements.txt
```

## Architecture

### System Data Flow
```
External APIs → Data Lake → Data Warehouse → Dashboard → Business Insights
     ↓             ↓             ↓              ↓              ↓
  [Collect]    [Process]    [Normalize]    [Visualize]    [Decide]
```

### Data Lake Zones
```
landing/ → raw/ → staging/ → curated/ → archive/
   ↓        ↓        ↓          ↓          ↓
[Ingest] [Validate] [Clean] [Transform] [Preserve]
```

### ⚠️ CRITICAL Data Caveat: Spotify Stream Double-Counting
**IMPORTANT**: The curated zone contains Spotify streaming data from TWO separate sources:
1. **tidy_daily_streams.csv** - Spotify + Apple Music streams from distributors (DistroKid/TooLost)
2. **spotify_audience_curated_*.csv** - Spotify-only metrics from Spotify for Artists API

**Never combine these datasets when calculating Spotify totals** - you would be double-counting!
- For total platform streams: Use `tidy_daily_streams` (includes both Spotify and Apple)
- For Spotify-specific analytics: Use `spotify_audience_curated` 
- **DO NOT** add values from both datasets together

### Key Components

**Data Lake Organization** (`src/<platform>/`):
- `extractors/` - API/web scraping scripts
- `cleaners/` - Zone promotion scripts (follow naming: `<service>_landing2raw.py`)
- `cookies/` - Authentication cookies

**Additional Directories**:
- `6_automated_cronjob/` - Automated pipeline execution scripts
- `src/common/cookie_refresh/` - Cookie refresh system with service strategies
- Root CSV files - Ad campaign and catalog data exports

**Data Warehouse** (Currently being reinitialized):
- SQLite database: `bedrot_analytics.db`
- Preserved virtual environment and requirements
- Will integrate with data_lake curated zone

**Dashboard Architecture**:
- Frontend: Next.js 14, React 18, TypeScript, Tailwind CSS
- Backend: FastAPI with WebSocket support
- Real-time updates via Socket.IO

## Cookie Authentication System

### Service-Specific Expiration
| Service | Max Age | Refresh Interval | Strategy | 2FA |
|---------|---------|------------------|----------|-----|
| Spotify | 30 days | 7 days | OAuth | No |
| TikTok | 30 days | 7 days | Playwright | Yes |
| DistroKid | 12 days | 10 days | JWT | No |
| TooLost | 7 days | 5 days | JWT | No |
| Linktree | 30 days | 14 days | Playwright | No |
| MetaAds | 60 days | 30 days | OAuth | No |

### Cookie Management
```bash
# Check all services
python src/common/cookie_refresh/check_status.py

# Manual refresh
python src/common/cookie_refresh/manual_refresh.py --service toolost

# View dashboard (http://localhost:8080)
python src/common/cookie_refresh/start_dashboard.py
```

## Common Tasks

### Adding a New Data Source

1. Create directory structure:
   ```bash
   mkdir -p src/newservice/{extractors,cleaners,cookies}
   touch src/newservice/__init__.py
   ```

2. Implement extractor (`src/newservice/extractors/newservice_extractor.py`)
3. Create three cleaners following naming convention
4. Add tests in `tests/newservice/`
5. No registration needed - pipelines auto-discover

### Running a Single Test
```bash
# Specific test file
pytest tests/spotify/test_spotify_extractor.py -v

# Specific test function
pytest tests/spotify/test_spotify_extractor.py::test_extract_data -v

# With coverage for module
pytest tests/spotify/ --cov=src.spotify --cov-report=term-missing
```

### Debugging Failed Extractors
```bash
# Set environment and run with debug
cd data_lake
set PROJECT_ROOT=%cd%
python src/spotify/extractors/spotify_audience_extractor.py --debug

# Check cookies
python -c "from common.cookies import validate_cookies; print(validate_cookies('spotify'))"

# View logs
type logs\extractor_YYYYMMDD.log
```

## Key Conventions

- **Environment**: `PROJECT_ROOT` must be set for all scripts
- **File Naming**: Timestamps as `YYYYMMDD_HHMMSS`
- **Data Formats**: NDJSON for structured data, CSV for tabular
- **Testing**: pytest with coverage targets
- **Authentication**: Cookie-based with automatic refresh system
- **Deployment**: Supports both Windows batch files and Linux scripts

## WebSocket Events (Dashboard)

```javascript
// Client → Server
socket.emit('subscribe', { channel: 'kpis' })
socket.emit('unsubscribe', { channel: 'kpis' })

// Server → Client  
socket.on('kpi:update', (data) => { /* New KPI data */ })
socket.on('connection:status', (status) => { /* Connected/Disconnected */ })
```

## Data Quality Standards

- SHA-256 hash deduplication tracked in `_hashes.json`
- Archive existing curated files before overwriting
- Validate data types and constraints in cleaners
- Log all operations with timestamps
- Handle errors gracefully with descriptive messages

## Performance Optimization

**Data Lake**:
- Parallel processing for different services
- Batch operations (1000 records/chunk)
- Generator patterns for large files

**Data Warehouse**:
- Indexes on frequently queried columns
- Regular VACUUM operations
- Batch inserts with transactions

**Dashboard**:
- React.memo for expensive components
- WebSocket throttling (max 1/second)
- Query result caching

## Security Considerations

- Store credentials in environment variables only
- Never commit cookies or API keys
- Hash PII data before storage
- Use HTTPS for all external APIs
- Implement authentication for dashboard access

## Current Status (August 2025)

### Pipeline Health
- **Working**: Check current status with `python src/common/pipeline_health_monitor.py`
- **Cookie Status**: Monitor with `python src/common/cookie_refresh/check_status.py`
- **Dashboard**: View at http://localhost:8080 via `python src/common/cookie_refresh/start_dashboard.py`

### Recent Changes (August 2025)
- Enhanced cookie refresh system with service-specific strategies
- Automated cronjob scripts in `6_automated_cronjob/` directory
- Improved pipeline execution with simplified batch files
- Added comprehensive monitoring and health check tools
- **Reinitialized data_warehouse and data_dashboard** (clean slate, preserved requirements/venv)
- **Updated .env configuration** to match data_lake pattern with absolute paths

### Known Issues
- TooLost JWT expires every 7 days
- Some services have data stuck in landing/raw zones
- Need weekly reminder for TooLost refresh