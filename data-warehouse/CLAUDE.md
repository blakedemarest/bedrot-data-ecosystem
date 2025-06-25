# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Data Warehouse** component of the BEDROT DATA ECOSYSTEM, a normalized SQLite database that serves analytics-ready data for BEDROT PRODUCTIONS' music business intelligence. The warehouse receives processed data from the data lake's curated zone and provides structured access for reporting and real-time dashboards.

## Development Commands

### Database Management
```bash
# Create/recreate SQLite database with full schema
python create_database.py

# Load master data (Artists, Platforms, Tracks)
python etl_master_data.py

# Run complete ETL pipeline from data lake
cd ../data_lake/etl
python run_all_etl.py

# Check database status and record counts
python -c "from create_database import show_database_info; show_database_info()"
```

### Testing
```bash
# Run warehouse-specific tests
pytest tests/ -v

# Test database connectivity and schema
python -c "import sqlite3; conn = sqlite3.connect('bedrot_analytics.db'); print('Tables:', [t[0] for t in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()])"
```

### Code Quality
```bash
# Format and lint warehouse code
black *.py
isort *.py
flake8 *.py
mypy *.py
```

## Architecture

### Database Schema (3NF Normalized)
The warehouse uses a normalized relational schema with 10 main tables:

**Master Data:**
- `artists` - Musical artists and metadata
- `platforms` - Streaming/social/advertising platforms  
- `tracks` - Songs/albums with ISRC/UPC codes

**Performance Data:**
- `streaming_performance` - Daily streaming metrics per track/platform
- `social_media_performance` - Social engagement and audience data
- `advertising_performance` - Ad campaign metrics and spend
- `meta_pixel_events` - Meta/Facebook pixel tracking events
- `link_analytics` - Linktree/social link performance

**Financial Data:**
- `financial_transactions` - Revenue, expenses, and payouts
- `campaigns` - Marketing campaign definitions

### Data Flow Integration
```
Data Lake (curated/) → Data Warehouse ETL → SQLite Database → Dashboard API
```

The warehouse sits between the data lake's curated zone and the real-time dashboard, providing:
- Data validation and type conversion
- Foreign key relationship enforcement
- Optimized query performance for analytics
- Historical data preservation

### ETL Pipeline Architecture
- **Master Data ETL** (`etl_master_data.py`) - Loads reference data (artists, platforms, tracks)
- **Performance ETL** (`../data_lake/etl/run_all_etl.py`) - Orchestrates all performance data loading
- **Incremental Updates** - ETL processes handle both full refreshes and incremental updates

## Key Conventions

### Database File Location
- Primary database: `bedrot_analytics.db` (160KB typical size)
- Backup location: Created automatically during ETL processes
- Connection string: `sqlite:///bedrot_analytics.db`

### Data Types and Formats
- Dates: YYYY-MM-DD format in DATE columns
- Timestamps: ISO format with timezone info
- Currency: Decimal types for financial precision
- Text encoding: UTF-8 throughout

### Foreign Key Relationships
All performance tables reference master data:
- `artist_id` → `artists.id`
- `platform_id` → `platforms.id` 
- `track_id` → `tracks.id` (where applicable)

### ETL Error Handling
- Failed ETL runs preserve existing data
- Validation errors logged with specific record details
- Duplicate detection based on composite keys
- Archive previous data before major updates

## Integration Points

### Data Lake Connection
The warehouse ETL reads from data lake curated files:
- `../data_lake/curated/spotify_audience_curated_*.csv` - Spotify audience data
- `../data_lake/curated/tiktok_analytics_curated_*.csv` - TikTok analytics metrics
- `../data_lake/curated/metaads_campaigns_performance_log.csv` - Meta advertising performance
- `../data_lake/curated/dk_bank_details.csv` - DistroKid financial transactions
- `../data_lake/curated/submithub_links_analytics_*.csv` - SubmitHub campaign data

### Dashboard Integration
The warehouse serves the data dashboard via:
- Direct SQLite connections from Python FastAPI backend
- Optimized queries for real-time KPI calculations
- JSON exports for dashboard chart data

## Dependencies
Core packages in `requirements.txt`:
- `pandas` - Data manipulation and ETL processing
- `numpy` - Numerical operations and data validation
- `python-dateutil` - Date parsing and timezone handling
- `sqlite3` - Database connectivity (built-in to Python)

## Current Data Status
The warehouse typically contains:
- **5 Artists** - BEDROT PRODUCTIONS roster
- **19 Tracks** - Released songs with ISRC codes
- **10 Platforms** - Integrated streaming/social/ad platforms
- **2,500+ Records** - Performance metrics across all platforms