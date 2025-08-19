# BEDROT Data Dashboard Frontend

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ installed
- Backend API running on http://localhost:8000

### Installation & Running

```bash
# 1. Navigate to dashboard directory
cd data_dashboard

# 2. Install dependencies (if not already done)
npm install

# 3. Start the backend first (in a separate terminal)
./run_backend.sh  # Linux/Mac
# OR
run_backend.bat    # Windows

# 4. Start the frontend development server
npm run dev
# OR use the startup scripts:
./run_frontend.sh  # Linux/Mac
run_frontend.bat   # Windows
```

The dashboard will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
data_dashboard/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Main dashboard page
│   ├── globals.css        # Global styles with Tailwind
│   └── providers.tsx      # React Query provider
├── components/            # React components
│   ├── Dashboard.tsx      # Main dashboard container
│   ├── KPICard.tsx       # KPI metric cards
│   ├── RevenueChart.tsx  # Monthly revenue line chart
│   ├── StreamingChart.tsx # Streaming area chart
│   ├── DistributorPieChart.tsx # Distributor breakdown
│   └── PaymentStatusTable.tsx  # Payment tracking table
├── lib/                   # Utilities and services
│   ├── api.ts            # API service layer
│   └── utils.ts          # Formatting utilities
├── backend/              # FastAPI backend (Python)
├── public/               # Static assets
└── configuration files   # next.config.js, tsconfig.json, etc.
```

## 🎨 Features Implemented

### Dashboard Components

1. **KPI Cards** - Display key metrics
   - Total Revenue ($1,889.26)
   - Total Streams (1.1M+)
   - Average Revenue per Stream ($0.00248)
   - Artist Count with top performer

2. **Revenue Chart** - Line chart showing:
   - Actual revenue (solid green line)
   - Expected revenue (dashed blue line)
   - Monthly trends for last 12 months

3. **Streaming Chart** - Area chart displaying:
   - Spotify streams (green gradient)
   - Apple Music streams (red gradient)
   - Daily performance over 30 days

4. **Distributor Pie Chart** - Shows revenue split:
   - DistroKid: 80.7% (~$2,104)
   - TooLost: 19.3% (~$497)

5. **Payment Status Table** - Tracks:
   - Expected vs Actual revenue
   - Payment status (Paid/Pending)
   - 2-month payment delay modeling
   - Variance calculations

### Technical Stack

- **Frontend Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with dark mode
- **Charts**: Recharts
- **Data Fetching**: TanStack Query (React Query)
- **Icons**: Lucide React
- **State Management**: React hooks

### API Integration

The frontend connects to the FastAPI backend via:
- REST API endpoints
- Automatic error handling
- 30-second auto-refresh for KPIs
- Type-safe API service layer

## 🔧 Development Commands

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm run start

# Type checking
npm run type-check

# Linting
npm run lint
```

## 🎯 Key Features

### Real-time Updates
- Auto-refresh every 30 seconds
- Live timestamp display
- React Query caching

### Responsive Design
- Mobile-friendly layout
- Dark mode support
- Hover effects and transitions

### Data Visualization
- Interactive charts with tooltips
- Custom color schemes
- Formatted numbers and currency

### Performance
- Optimized bundle size
- Code splitting
- Image optimization
- Lazy loading

## 🐛 Troubleshooting

### Frontend won't start
1. Ensure Node.js 18+ is installed
2. Delete `node_modules` and `.next` folders
3. Run `npm install` again
4. Check port 3000 is not in use

### No data showing
1. Verify backend is running on port 8000
2. Check browser console for errors
3. Ensure CSV files exist in data_lake/4_curated
4. Try refreshing the cache: POST to /api/data/reload-cache

### Charts not rendering
1. Clear browser cache
2. Check for JavaScript errors
3. Verify Recharts is installed

## 📊 Data Sources

The dashboard pulls data from:
- `dk_bank_details.csv` - Revenue transactions
- `tidy_daily_streams.csv` - Streaming metrics
- `tiktok_analytics_curated_*.csv` - Social metrics
- `metaads_campaigns_daily.csv` - Marketing data

## 🚧 Next Steps

### High Priority
- [ ] WebSocket for real-time updates
- [ ] User authentication
- [ ] Data export functionality

### Medium Priority
- [ ] Additional chart types
- [ ] Filtering and date ranges
- [ ] Mobile app version

### Low Priority
- [ ] Email alerts
- [ ] PDF reports
- [ ] API rate limiting

## 📝 Notes

- The dashboard uses mock data for some real-time features
- Payment delays are modeled at 2 months average
- All monetary values are in USD
- Streaming data lacks artist-level attribution

## 🔗 Related Documentation

- [Backend API Docs](http://localhost:8000/docs)
- [Main README](../README.md)
- [Implementation Plan](../DASHBOARD_IMPLEMENTATION_GAMEPLAN.md)

## 💻 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 📄 License

Proprietary - BEDROT PRODUCTIONS