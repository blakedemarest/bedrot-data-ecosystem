# CLAUDE.md - Data Dashboard

This file provides guidance to Claude Code (claude.ai/code) when working with the BEDROT Data Dashboard component.

## Directory Overview

The data_dashboard directory is the visualization and user interface component of the BEDROT Data Ecosystem. It provides real-time KPI monitoring, interactive charts, and business intelligence for music industry metrics.

## Current Status (August 2025)

**⚠️ RECENTLY REINITIALIZED**: This component was completely reset on 2025-08-04. The previous implementation was removed, preserving only:
- Environment configuration (`.env`, `.env.example`)
- Package dependencies (`package.json`, `package-lock.json`)
- Backend requirements (`backend/requirements.txt`)
- Configuration files (`tsconfig.json`, `tailwind.config.js`, etc.)

## Environment Configuration

The dashboard uses a structured .env file following the data_lake pattern:

```env
# Core paths (Windows format)
PROJECT_ROOT=C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_dashboard
DATA_ECOSYSTEM_PATH=C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem
DATA_LAKE_PATH=C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake
WAREHOUSE_PATH=C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_warehouse

# Frontend settings
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8001/ws

# Backend settings
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8001
DATABASE_PATH=../data_warehouse/bedrot_analytics.db
```

## Technology Stack

### Frontend (Next.js)
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Real-time**: Socket.IO client
- **State Management**: React hooks

### Backend (FastAPI)
- **Framework**: FastAPI
- **Database**: SQLite (via data_warehouse)
- **Real-time**: WebSocket support
- **Data Processing**: Pandas
- **Validation**: Pydantic

## Planned Architecture

### Component Structure
```
data_dashboard/
├── src/                    # Frontend source
│   ├── app/               # Next.js app directory
│   ├── components/        # React components
│   │   ├── charts/       # Chart components
│   │   ├── kpis/         # KPI cards
│   │   └── layout/       # Layout components
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utilities
│   └── types/            # TypeScript types
├── backend/               # FastAPI backend
│   ├── main.py           # FastAPI app
│   ├── routers/          # API routes
│   ├── services/         # Business logic
│   ├── models/           # Pydantic models
│   └── utils/            # Utilities
└── public/               # Static assets
```

### Data Flow
```
SQLite DB → FastAPI → WebSocket/REST → Next.js → User Interface
     ↓          ↓           ↓            ↓           ↓
[Storage]  [Process]   [Transport]   [Render]    [Display]
```

## Key Performance Indicators (KPIs)

### Streaming Metrics
- Total streams (all-time, monthly, daily)
- Revenue per stream ($0.003062 from DistroKid data)
- Top performing tracks
- Platform distribution (Spotify, Apple Music, etc.)

### Financial Metrics
- Total revenue (streaming + other)
- Monthly recurring revenue (MRR)
- Revenue by artist
- Expense tracking

### Social Media Metrics
- TikTok engagement rate
- Instagram reach
- Linktree clicks
- Meta Ads ROI

### Growth Metrics
- Month-over-month growth
- New listener acquisition
- Market penetration by region

## Development Commands

### Frontend Development
```bash
cd data_dashboard
npm install
npm run dev        # Start development server (port 3000)
npm run build      # Build for production
npm run start      # Start production server
npm run lint       # Run ESLint
npm run type-check # TypeScript validation
```

### Backend Development
```bash
cd data_dashboard/backend
pip install -r requirements.txt
python main.py     # Start FastAPI server (port 8001)

# Or with uvicorn
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

### Full Stack Development
```bash
# Terminal 1: Backend
cd data_dashboard/backend
python main.py

# Terminal 2: Frontend
cd data_dashboard
npm run dev
```

## API Endpoints (Planned)

### RESTful Endpoints
```
GET  /api/health          # Health check
GET  /api/kpis            # All KPIs
GET  /api/streaming       # Streaming data
GET  /api/financial       # Financial data
GET  /api/social          # Social media metrics
POST /api/refresh         # Trigger data refresh
```

### WebSocket Events
```javascript
// Client → Server
socket.emit('subscribe', { metrics: ['streams', 'revenue'] })
socket.emit('unsubscribe', { metrics: ['streams'] })
socket.emit('refresh', { force: true })

// Server → Client
socket.on('update', (data) => { /* New metrics */ })
socket.on('error', (error) => { /* Handle error */ })
socket.on('status', (status) => { /* Connection status */ })
```

## Component Guidelines

### Chart Components
- Use Recharts for consistency
- Implement responsive design
- Add loading states
- Include error boundaries
- Support dark/light themes

### KPI Cards
- Display current value prominently
- Show trend indicators (↑↓)
- Include sparklines for context
- Add period comparisons
- Implement click-through to details

### Data Tables
- Use virtualization for large datasets
- Implement sorting and filtering
- Add export functionality
- Support column customization
- Include pagination

## Performance Optimization

### Frontend
- Use React.memo for expensive components
- Implement code splitting
- Optimize bundle size
- Use Next.js Image component
- Cache API responses

### Backend
- Implement query result caching
- Use database indexes effectively
- Batch WebSocket updates
- Implement request throttling
- Use connection pooling

## Testing Strategy

### Frontend Tests
```bash
npm run test          # Run all tests
npm run test:watch    # Watch mode
npm run test:coverage # Coverage report
```

### Backend Tests
```bash
pytest                # Run all tests
pytest --cov         # With coverage
pytest -v            # Verbose output
```

## Deployment Considerations

### Environment Variables
- Use `.env.production` for production settings
- Never commit sensitive credentials
- Validate all environment variables on startup

### Database Connection
- Use connection pooling in production
- Implement retry logic
- Handle connection failures gracefully

### WebSocket Scaling
- Consider using Redis for pub/sub in production
- Implement heartbeat for connection monitoring
- Handle reconnection on client side

## Common Issues and Solutions

### "Cannot connect to backend"
- Verify backend is running on port 8001
- Check CORS configuration
- Ensure DATABASE_PATH is correct

### "WebSocket connection failed"
- Check WebSocket URL configuration
- Verify firewall settings
- Ensure backend WebSocket endpoint is active

### "Data not updating"
- Check database connection
- Verify ETL pipelines have run
- Check caching settings

## Next Steps

1. **Create Frontend Structure**:
   - Set up Next.js app directory
   - Create base components
   - Implement routing
   - Add authentication scaffolding

2. **Build Backend API**:
   - Create FastAPI application
   - Implement database connection
   - Build API endpoints
   - Add WebSocket support

3. **Develop Core Features**:
   - KPI dashboard
   - Streaming analytics view
   - Financial reports
   - Social media metrics

4. **Add Advanced Features**:
   - User authentication
   - Custom date ranges
   - Export functionality
   - Alerting system

## Security Considerations

- Implement authentication before production
- Use HTTPS in production
- Sanitize all user inputs
- Implement rate limiting
- Add request validation
- Use secure WebSocket (WSS)