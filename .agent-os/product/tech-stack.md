# Tech Stack

## Current Implementation

### Backend
- **Language**: Python 3.9+
- **Framework**: FastAPI 0.104+
- **Data Processing**: Pandas 2.0+, Polars 0.19+, NumPy 1.24+
- **Database ORM**: SQLAlchemy 2.0+
- **Task Queue**: Celery 5.3+ with Redis
- **Web Scraping**: Playwright 1.40+, BeautifulSoup4 4.12+
- **API Clients**: httpx 0.25+, aiohttp 3.9+

### Frontend
- **Framework**: Next.js 14.0+
- **Language**: TypeScript 5.2+
- **UI Library**: React 18.2+
- **Styling**: Tailwind CSS 3.3+
- **Charts**: Chart.js 4.4+, Recharts 2.10+
- **State Management**: Zustand 4.4+
- **Real-time**: Socket.IO Client 4.7+

### Databases
- **Analytical**: SQLite 3.43+ (current)
- **Production**: PostgreSQL 16+ (migration planned)
- **Caching**: Redis 7.2+ (planned)
- **Object Storage**: MinIO RELEASE.2024+

### Data Lake Architecture
- **Landing Zone**: Raw file storage (JSON, CSV, TSV)
- **Raw Zone**: Partitioned by source/date
- **Staging Zone**: Cleaned and validated data
- **Curated Zone**: Business-ready datasets
- **Archive Zone**: Historical data with compression

### Infrastructure
- **Operating System**: Windows 11 / WSL2 Ubuntu
- **Process Management**: PM2 5.3+
- **Reverse Proxy**: Nginx 1.24+
- **Containerization**: Docker 24+ (optional)
- **Version Control**: Git with GitHub

### Data Quality & Testing
- **Validation**: Great Expectations 0.18+
- **Testing**: pytest 7.4+, pytest-asyncio
- **Code Quality**: black, flake8, mypy
- **Documentation**: Sphinx, MkDocs

### Monitoring & Logging
- **Logging**: Python logging with JSON formatter
- **Metrics**: Prometheus + Grafana (planned)
- **Error Tracking**: Sentry (planned)
- **APM**: OpenTelemetry (planned)

### Authentication & Security
- **Auth Method**: Cookie-based with Playwright
- **2FA Support**: TOTP via pyotp
- **Secrets Management**: python-dotenv, .env files
- **Encryption**: cryptography library

### Development Tools
- **IDE**: VS Code with Python/TS extensions
- **Package Management**: pip, npm
- **Virtual Environment**: venv (named .venv)
- **API Testing**: Postman, HTTPie
- **Browser Automation**: Playwright

## Planned Upgrades

### Q1 2025
- PostgreSQL 16+ migration
- Redis 7.2+ caching layer
- Airflow 2.7+ orchestration

### Q2 2025
- Kubernetes deployment
- Apache Kafka streaming
- Elasticsearch for search

### Q3 2025
- GraphQL API layer
- Apache Spark for big data
- Terraform infrastructure as code

### Q4 2025
- LangChain for AI features
- Vector database (Pinecone/Weaviate)
- Edge computing with Cloudflare

## Technology Decisions

### Why FastAPI?
- Async support for concurrent requests
- Automatic API documentation
- Type hints and validation
- WebSocket support built-in
- High performance

### Why Next.js?
- Server-side rendering for SEO
- Built-in optimization
- TypeScript support
- API routes included
- Excellent developer experience

### Why PostgreSQL? (Migration Target)
- ACID compliance for financial data
- Advanced indexing options
- Partitioning for time-series data
- Full-text search capabilities
- Proven scalability

### Why MinIO?
- S3-compatible API
- Self-hosted option
- High performance
- Cost-effective storage
- Easy backup/replication

## Development Standards

### Code Style
- Python: black, PEP 8
- TypeScript: ESLint, Prettier
- SQL: Uppercase keywords, snake_case
- Git: Conventional commits

### Testing Requirements
- Unit test coverage: > 80%
- Integration tests for APIs
- E2E tests for critical paths
- Performance benchmarks

### Documentation
- API: OpenAPI/Swagger specs
- Code: Docstrings and comments
- Architecture: Decision records
- User: README and guides