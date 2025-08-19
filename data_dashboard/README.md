# BEDROT Data Dashboard

Real-time analytics dashboard for music streaming, revenue, and marketing data.

## Overview

The BEDROT Data Dashboard provides comprehensive insights into:
- **Revenue Analytics**: Platform-specific earnings, artist breakdown, distributor comparison
- **Streaming Metrics**: Daily streams, growth trends, platform distribution
- **Social Media Performance**: TikTok engagement, follower growth
- **Marketing ROI**: Meta Ads campaign performance, cost per acquisition
- **Payment Tracking**: Expected vs actual revenue with 2-month delay modeling

## Architecture

```
data_dashboard/
├── backend/           # FastAPI backend
│   ├── api/          # REST API endpoints
│   ├── services/     # Business logic
│   ├── data/         # CSV data loader with caching
│   └── utils/        # Environment loaders
├── src/              # React frontend (coming soon)
└── venv/             # Python virtual environment
```

## Quick Start

### Backend Setup

1. **Install Dependencies**:
```bash
cd data_dashboard
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

pip install -r backend/requirements.txt
```

2. **Configure Environment**:
- `.env.context` - Contains paths and configuration
- `.env.secrets` - Add any API keys or secrets here

3. **Start the Server**:
```bash
# Linux/Mac
./run_backend.sh

# Windows
run_backend.bat

# Or manually
python backend/main.py
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Test the API

```bash
# Run the test suite
python backend/test_api.py
```

## API Endpoints

### KPIs
- `GET /api/kpis/summary` - Summary KPIs for dashboard
- `GET /api/kpis/realtime` - Real-time metrics
- `GET /api/kpis/goals` - Goal tracking
- `GET /api/kpis/alerts` - KPI alerts

### Revenue
- `GET /api/revenue/platform` - Revenue by platform
- `GET /api/revenue/artist` - Revenue by artist
- `GET /api/revenue/distributor` - Revenue by distributor
- `GET /api/revenue/monthly` - Monthly revenue with expected vs actual
- `GET /api/revenue/delays` - Payment delay analysis
- `GET /api/revenue/rps-rates` - Revenue per stream rates

### Streaming
- `GET /api/streaming/daily` - Daily streaming data
- `GET /api/streaming/summary` - Streaming summary
- `GET /api/streaming/growth` - Growth metrics
- `GET /api/streaming/spotify-audience` - Spotify audience data

### Data Access
- `GET /api/data/files` - List available files
- `GET /api/data/file/{filename}` - Get file data
- `GET /api/data/metadata/{filename}` - Get file metadata
- `GET /api/data/schema` - Get data schemas
- `POST /api/data/reload-cache` - Force cache reload

## Key Features

### 1. Revenue Tracking by Distributor
- **DistroKid**: Primary distributor (66.5% of data)
- **TooLost**: Secondary distributor (33.5% of data)
- Automatic expected revenue calculation based on streaming data
- 2-month payment delay modeling

### 2. AI-Safe API Design
All endpoints return structured responses with:
- `success`: Boolean status
- `data`: Actual data payload
- `metadata`: Context for AI agents including:
  - Data sources
  - Limitations
  - Last updated timestamp
  - Calculation methods

### 3. Data Caching
- 5-minute TTL cache for CSV files
- Automatic cache invalidation
- Force reload capability
- Optimized for performance

### 4. Comprehensive Metrics
- **Financial**: Revenue, RPS rates, payment delays
- **Streaming**: Daily/monthly trends, platform breakdown
- **Social**: TikTok engagement, follower growth
- **Marketing**: Ad spend, impressions, ROI

## Data Sources

Data is loaded from the curated zone of the Data Lake:
- `dk_bank_details.csv` - DistroKid revenue transactions
- `tidy_daily_streams.csv` - Consolidated streaming metrics
- `tiktok_analytics_curated_*.csv` - TikTok analytics
- `metaads_campaigns_daily.csv` - Meta Ads performance
- `spotify_audience_curated_*.csv` - Spotify audience data

## Development

### Running Tests
```bash
# Backend unit tests
pytest backend/tests/

# API integration tests
python backend/test_api.py
```

### Adding New Endpoints
1. Create router in `backend/api/routers/`
2. Add business logic in `backend/services/`
3. Include router in `backend/main.py`
4. Test with `test_api.py`

### Environment Variables

**Context Variables** (`.env.context`):
- `PROJECT_ROOT` - Dashboard root directory
- `DATA_LAKE_PATH` - Path to data lake
- `CURATED_DATA_PATH` - Path to curated data
- `BACKEND_PORT` - API server port (default: 8000)
- `CACHE_TTL` - Cache time-to-live in seconds

**Secrets** (`.env.secrets`):
- Add any API keys or sensitive data here

## Monitoring

Logs are stored in `logs/` directory with daily rotation:
- `dashboard_YYYY-MM-DD.log` - Application logs
- 7-day retention policy

## Known Limitations

1. **No Artist Attribution in Streaming Data**: The `tidy_daily_streams.csv` file contains platform-level totals without artist separation
2. **Payment Delay**: Actual revenue has a 2-month reporting delay from streaming services
3. **TooLost Data**: Limited to streaming metrics only, no revenue data available

## Future Enhancements

- [ ] WebSocket support for real-time updates
- [ ] React frontend with interactive charts
- [ ] SQLite data warehouse integration
- [ ] Artist-level streaming attribution
- [ ] Automated alerting system
- [ ] Export functionality (Excel, PDF)

## Support

For issues or questions, check:
- API Documentation: http://localhost:8000/docs
- Logs: `logs/dashboard_*.log`
- Test Suite: `python backend/test_api.py`