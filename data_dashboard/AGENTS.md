# Repository Guidelines

## Orientation
- The dashboard was reset on 2025-08-04; follow the slim Next.js + FastAPI architecture described in `.claude/CLAUDE.md` and keep features modular.
- Frontend code resides in ``src/`` (App Router), shared UI in ``components/``, hooks/utilities in ``lib/`` and ``src/hooks``. The backend FastAPI app lives entirely in ``backend/`` with routers, services, models, monitoring, and tests.

## Environment Variables (Load Them Constantly)
- Core paths: ``PROJECT_ROOT``, ``DATA_ECOSYSTEM_PATH``, ``DATA_LAKE_PATH``, ``WAREHOUSE_PATH``-resolve assets and sibling data via these instead of brittle relatives.
- Frontend config: ``NEXT_PUBLIC_API_URL``, ``NEXT_PUBLIC_WEBSOCKET_URL``, ``NEXT_PUBLIC_REFRESH_INTERVAL``, ``NEXT_PUBLIC_ENABLE_DEBUG``. Use them via ``process.env`` to drive fetch clients, sockets, and feature flags.
- Backend server knobs: ``BACKEND_HOST``, ``BACKEND_PORT``, ``BACKEND_RELOAD``, ``BACKEND_DEBUG``, ``BACKEND_LOG_LEVEL``. Surface them in ``uvicorn`` and logging setup.
- Data sources: ``DATABASE_PATH``, ``DATABASE_POOL_SIZE``, ``DATABASE_POOL_TIMEOUT`` plus CSV fallbacks ``CURATED_DATA_PATH``, ``STAGING_DATA_PATH``, ``ENABLE_CSV_FALLBACK``. Read with ``os.getenv`` and validate before queries.
- Infrastructure toggles: WebSocket (``WS_HEARTBEAT_INTERVAL``, ``WS_MAX_CONNECTIONS``, ``WS_MESSAGE_QUEUE_SIZE``), caching (``ENABLE_CACHE``, ``CACHE_TTL_SECONDS``, ``CACHE_BACKEND``, ``REDIS_URL``), CORS (``CORS_*``), auth (``ENABLE_AUTH``, ``JWT_*``), monitoring (``ENABLE_METRICS``, ``METRICS_PORT``, ``ENABLE_TRACING``). Guard new features behind these keys and document defaults when editing `.env.example`.
- Pattern: load ``dotenv`` for the backend, check for missing variables at startup, and rely on ``process.env`` or config modules to fan values through React/Next.js.

## Frontend Workflow
- Install deps with ``npm install``; run ``npm run dev`` for local iteration, ``npm run lint`` and ``npm run type-check`` before committing.
- Keep charts in ``components/charts`` and KPI tiles in ``components/kpis`` per the CLAUDE plan. Fetch data through React Query hooks that reference ``NEXT_PUBLIC_*`` vars, not hardcoded URLs.
- When introducing KPIs, record business constants (e.g., stream revenue ``0.003062``) in config modules and cite the data source in code comments.

## Backend Workflow
- Launch the API via ``uvicorn backend.main:app --reload --host %BACKEND_HOST% --port %BACKEND_PORT%``. Routes ship under ``/api/revenue``, ``/api/streaming``, ``/api/kpis``, ``/api/data`` with ``/health`` for probes.
- WebSocket handlers must respect the ``subscribe``/``unsubscribe``/``refresh`` contract; add integration tests or simulators whenever payloads change. Use env knobs to tune heartbeat or queue sizes.
- Read ``DATABASE_PATH`` with ``Path`` and funnel queries through service modules that emit Pydantic models and log latency via ``monitoring/`` utilities.

## Quality & Observability
- Extend ``backend/test_api.py`` for every API change; add mocked socket tests when feasible. Capture manual UI verification (screenshots/video) until automated coverage arrives.
- Ensure Tailwind themes support light/dark out of the box. If client telemetry or metrics are enabled, write to the path referenced by ``BACKEND_LOG_LEVEL``/``ENABLE_METRICS`` and scrub secrets before sharing logs.

## Security & Deployment
- Never hard-code credentials; update `.env.example` whenever you introduce new keys and explain how to populate them. Validate ``ENABLE_AUTH`` flows before flipping defaults.
- Production rollout: ``npm run build``, ``npm run start``, and ``uvicorn backend.main:app --host 0.0.0.0 --port %BACKEND_PORT%`` (without reload). Note schema or data-lake dependencies in release notes and keep CORS lists in sync with deployments.

