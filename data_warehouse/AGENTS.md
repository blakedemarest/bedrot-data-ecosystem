# Repository Guidelines

## Orientation
- The warehouse was reset on 2025-08-04; evolve it according to `.claude/CLAUDE.md` so schema, ETL, and API layers stay aligned with the lake and dashboard.
- Core assets include ``bedrot_analytics.db``, schema files (``create_schema.sql``, ``seed_master_data.sql``), orchestrator ``comprehensive_etl.py``, and integration coverage in ``test_with_real_data.py``.

## Environment Variables (Reference Them Religiously)
- Paths: ``PROJECT_ROOT`` (workspace), ``DATA_ECOSYSTEM_PATH`` (monorepo root), ``DATA_LAKE_PATH`` (curated inputs), ``DASHBOARD_PATH`` (downstream consumer). Use ``Path(os.getenv(...))`` for every filesystem reference and fail fast if missing.
- Database knobs: ``DATABASE_PATH``, ``DATABASE_BACKUP_PATH``, ``DATABASE_POOL_SIZE``, ``DATABASE_MAX_OVERFLOW``. Parameterize engine creation with these values and respect backup directories when copying SQLite files.
- Zone mapping: ``CURATED_ZONE``, ``STAGING_ZONE``, ``RAW_ZONE``, ``LANDING_ZONE``-never hard-code folder names when ingesting from the lake.
- ETL tuning: ``ETL_BATCH_SIZE``, ``ETL_LOG_LEVEL``, ``ETL_LOG_PATH``, ``ETL_ENABLE_VALIDATION``, ``ETL_MAX_RETRIES``. Surface them in CLI entry points and log which settings are active.
- API/ops (future-ready): ``API_HOST``, ``API_PORT``, ``API_RELOAD``, ``API_DEBUG``, ``API_CORS_ORIGINS`` plus caching/monitoring flags (``ENABLE_CACHING``, ``CACHE_TTL_SECONDS``, ``ENABLE_QUERY_PROFILING``, ``ENABLE_HEALTH_CHECKS``, ``HEALTH_CHECK_INTERVAL_SECONDS``, ``ENABLE_METRICS``, ``METRICS_PORT``). Even if dormant, keep references ready and document deltas when enabling features.
- Conventions: load ``dotenv`` immediately in scripts, log presence (not values) for troubleshooting, and guard optional settings with sensible defaults.

## ETL Workflow
- Execute ``python comprehensive_etl.py`` after the lake pipeline populates ``%DATA_LAKE_PATH%\%CURATED_ZONE%``. Stage new loaders in ``src/etl/`` and record lineage (source file ? staging table ? warehouse table) in docstrings or structured logs.
- Wrap multi-table loads in transactions, leverage UPSERT patterns for idempotency, and emit row counts keyed by table name/intended change.

## Testing & Validation
- Run ``pytest -v`` and targeted integration checks ``pytest test_with_real_data.py -k integration``. Tests should copy ``DATABASE_PATH`` to a temp file referenced by env variables to avoid clobbering prod data.
- Assert schema contracts (primary/foreign keys, unique constraints), data types, aggregation accuracy, and row-level business rules. Maintain >80% coverage and document any exclusions in PRs.
- Troubleshoot with `.claude/CLAUDE.md`: ensure ``src`` is on ``PYTHONPATH``, close lingering SQLite connections, enable WAL when concurrency is expected, and tighten pandas dtypes to prevent mismatches.

## Security & Operations
- Never print credential values; scrub logs before sharing. When backups run, use ``DATABASE_BACKUP_PATH`` + timestamps and summarize retention plans in release notes.
- Vacuum databases post-migration, update `.env.example` when adding configuration knobs, and notify dashboard/lake owners of any schema contract changes.
- If you expose an API, wire health checks and metrics around the env flags so deploys honor the same configuration model as local development.

