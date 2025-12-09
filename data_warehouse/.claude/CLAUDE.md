# CLAUDE.md - Data Warehouse

This file provides guidance to Claude Code (claude.ai/code) when working with the BEDROT Data Warehouse component.

## Directory Overview

The data_warehouse directory is the analytical database component of the BEDROT Data Ecosystem. It provides normalized data storage, ETL pipelines, and API endpoints for the dashboard.

## Current Status (August 2025)

**⚠️ RECENTLY REINITIALIZED**: This component was completely reset on 2025-08-04. The previous implementation was removed, preserving only:
- Virtual environment (`.venv/`)
- Requirements file (`requirements.txt`)
- Environment configuration (`.env`, `.env.example`)
- SQLite database (`bedrot_analytics.db`)

## Environment Configuration

The warehouse uses a structured .env file following the data_lake pattern:

```env
# Core paths (Windows format)
PROJECT_ROOT=C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_warehouse
DATA_ECOSYSTEM_PATH=C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem
DATA_LAKE_PATH=C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake
DASHBOARD_PATH=C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_dashboard

# Database settings
DATABASE_PATH=bedrot_analytics.db
DATABASE_BACKUP_PATH=backups

# Data Lake Integration (relative paths)
CURATED_ZONE=4_curated
STAGING_ZONE=3_staging
RAW_ZONE=2_raw
LANDING_ZONE=1_landing
```

## Planned Architecture

### Database Schema (SQLite)
- **Artists Table**: Artist master data with IDs and metadata
- **Tracks Table**: Track catalog with ISRC codes
- **Platforms Table**: Streaming and social platforms
- **Streaming Performance**: Daily streaming metrics
- **Financial Transactions**: Revenue and expense data
- **Social Media Metrics**: Engagement and reach data
- **Marketing Campaigns**: Ad spend and performance

### ETL Pipeline Structure
```
data_lake/4_curated/ → ETL Scripts → SQLite Database → API Layer
```

### Integration Points
- **Input**: Reads from data_lake curated zone (`4_curated/`)
- **Processing**: Python ETL scripts for data transformation
- **Storage**: SQLite database with normalized schema
- **Output**: API endpoints for dashboard consumption

## Development Guidelines

### Virtual Environment
```bash
cd data_warehouse
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Database Operations
- Use transactions for bulk inserts
- Create indexes on frequently queried columns
- Implement proper foreign key constraints
- Regular VACUUM for optimization

### ETL Best Practices
- Validate data before insertion
- Log all transformations
- Handle duplicates with UPSERT logic
- Maintain data lineage tracking

## Dependencies

Current `requirements.txt`:
```
pandas>=2.0.0,<3.0.0
numpy>=1.24.0,<2.0.0
python-dateutil>=2.8.2,<3.0.0
```

Additional dependencies to consider:
- `sqlalchemy` - ORM and database abstraction
- `alembic` - Database migrations
- `fastapi` - API framework
- `pydantic` - Data validation
- `pytest` - Testing framework

## Next Steps

1. **Create Core Structure**:
   - `src/` - Source code directory
   - `src/database/` - Database models and connections
   - `src/etl/` - ETL pipeline scripts
   - `src/api/` - API endpoints
   - `tests/` - Test suite

2. **Initialize Database**:
   - Create schema initialization script
   - Set up migration system
   - Import existing data from curated zone

3. **Implement ETL Pipelines**:
   - Streaming data ETL
   - Financial data ETL
   - Social media data ETL
   - Master data management

4. **Build API Layer**:
   - FastAPI application
   - RESTful endpoints for dashboard
   - WebSocket support for real-time updates

## Common Issues and Solutions

### "No module named 'src'"
- Ensure PROJECT_ROOT is set in environment
- Add src to Python path in scripts

### "Database locked"
- Close other connections to SQLite
- Implement connection pooling
- Use WAL mode for concurrent access

### "Data type mismatch"
- Validate data types before insertion
- Use pandas dtype specifications
- Implement data cleaning in ETL

## Integration with Dashboard

The warehouse provides data to the dashboard via:
1. Direct SQLite connection (for development)
2. FastAPI endpoints (for production)
3. WebSocket for real-time updates

Dashboard expects:
- `/api/kpis` - Key performance indicators
- `/api/streaming` - Streaming metrics
- `/api/financial` - Revenue data
- `/ws` - WebSocket connection

## Security Considerations

- Never expose database credentials
- Implement API authentication
- Sanitize all inputs
- Use parameterized queries
- Regular backups to `DATABASE_BACKUP_PATH`