# BEDROT Data Ecosystem Documentation Index

## Overview Documents
- [BEDROT Ecosystem Analysis](BEDROT_ECOSYSTEM_ANALYSIS.md) - Comprehensive system overview
- [BEDROT Repository Analysis](BEDROT_Repository_Analysis.md) - Detailed technical analysis
- [BEDROT Data Lake Design v1.2](BEDROT_DATA_LAKE_DESIGN_v1.2.md) - Original design document
- [Claude Enhancement Summary](CLAUDE_enhancement_summary.md) - AI integration improvements

## Component Documentation

### Data Lake (`../data_lake/`)
- [Data Lake README](../data_lake/README.md) - Executive summary and architecture
- [Data Lake CLAUDE.md](../data_lake/CLAUDE.md) - AI agent guidance
- [Data Lake Docs](../data_lake/docs/) - Detailed documentation folder
  - Authentication workflows
  - Cookie management systems
  - Pipeline troubleshooting
  - Service integration guides

### Data Warehouse (`../data-warehouse/`)
- [Data Warehouse README](../data-warehouse/README.md) - Database architecture
- [Data Warehouse CLAUDE.md](../data-warehouse/CLAUDE.md) - AI agent guidance
- [Data Warehouse Docs](../data-warehouse/docs/) - Detailed documentation
  - Attribution logic
  - Power BI connection guide
  - Data cleanup summaries

### Data Dashboard (`../data_dashboard/`)
- [Dashboard README](../data_dashboard/README.md) - Frontend/backend architecture
- [Dashboard CLAUDE.md](../data_dashboard/CLAUDE.md) - AI agent guidance
- [Python Backend README](../data_dashboard/PYTHON_BACKEND_README.md) - FastAPI details
- [Style Guide](../data_dashboard/style-guide/) - UI/UX standards

## Quick Links

### Getting Started
1. [Root CLAUDE.md](../CLAUDE.md) - Start here for development commands
2. [Root README](../README.md) - Project overview and quick start

### Common Tasks
- **Running the pipeline**: See Data Lake CLAUDE.md → Development Commands
- **Refreshing cookies**: See Data Lake docs → COOKIE_REFRESH_README.md
- **Debugging issues**: See Data Lake docs → TROUBLESHOOTING.md
- **Database queries**: See Data Warehouse docs → Power BI Connection Guide

### Architecture Diagrams
- System architecture: BEDROT_ECOSYSTEM_ANALYSIS.md
- Data flow: BEDROT_Repository_Analysis.md
- Database schema: Data Lake docs → database_design_report.md

## Documentation Standards

All documentation follows these conventions:
- **README.md**: High-level overview for new developers
- **CLAUDE.md**: Detailed guidance for AI agents (Claude Code)
- **docs/**: Component-specific detailed documentation
- **changelog*.md**: Version history and updates

Last updated: July 14, 2025