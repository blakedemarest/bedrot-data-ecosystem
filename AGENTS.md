# Repository Guidelines

## Orientation
- The ecosystem is split into ``data_lake``, ``data_dashboard``, and ``data_warehouse``. Each directory maintains its own `.env` and agent guide-read ``<component>/AGENTS.md`` before editing code there.
- Load environment variables through ``python-dotenv`` or shell exports before running automation; every path, secret, and feature flag is designed to be configurable.

## Environment Variables You Must Rely On
- Global anchors: ``PROJECT_ROOT`` (per component) and ``DATA_ECOSYSTEM_PATH``. Build absolute paths off these constants rather than guessing directories.
- Cross-service pointers: ``DATA_LAKE_PATH``, ``DASHBOARD_PATH``, ``WAREHOUSE_PATH`` connect the stacks; use them when sharing artifacts or wiring integrations.
- Module-specific keys: zone names (lake), socket/API endpoints (dashboard), database/ETL toggles (warehouse). Consult each component guide for the full list and mirror new keys in `.env.example` files.
- Habit: validate required variables at startup, log the names discovered (never values), and short-circuit when configuration is incomplete.

## Project Structure
- ``data_lake/``: Python ETL that promotes source feeds across six zones.
- ``data_dashboard/``: Next.js frontend + FastAPI backend for KPIs and sockets.
- ``data_warehouse/``: SQLite analytics store, ETL loaders, and future APIs.
Shared documentation lives in ``docs/``; keep secrets in local `.env` copies only.

## Core Workflows
- Use virtual environments or Node installs per component (see local guides).
- Lake pipeline: ``cronjob/run_bedrot_pipeline.bat`` (or ``--automated``). Dashboard dev: ``npm run dev`` + ``uvicorn backend.main:app --reload``. Warehouse rebuild: ``python data_warehouse/comprehensive_etl.py``.
- When chaining services, prefer env-driven paths (e.g., ``Path(os.getenv("DATA_LAKE_PATH")) / os.getenv("CURATED_ZONE")``) so scripts run on any machine.

## Coding Standards
- Python: 4-space indent, snake_case modules, type hints, lint via ``black``, ``isort``, ``flake8``, ``mypy``.
- TypeScript/React: PascalCase components, camelCase hooks, Tailwind classes kept with JSX, lint via ``npm run lint`` / ``npm run type-check``.
- Respect existing `.gitignore` rules; log files, SQLite dumps, and CSV exports stay out of version control.

## Testing & Quality
- Run the component suites (`pytest`, `npm run lint`, `npm run type-check`) before raising PRs. Assert business rules (zone promotions, API shapes, warehouse constraints) in addition to unit logic.
- Document manual verification (screenshots, SQL snippets, replay steps) in change notes when automated coverage is unavailable.

## Security & Operations
- Never commit secrets; extend `.env.example` files when adding variables and describe how to populate them.
- Store large datasets in MinIO or ``backups/`` rather than git. Preserve the semi-manual authentication flow documented in ``data_lake/.claude/CLAUDE.md``.
- Emit actionable logs and monitoring where available, and highlight schema or contract changes so other services can adjust their configuration.

