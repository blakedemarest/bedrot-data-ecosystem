# Zones and Environment Variables - BEDROT Data Lake

This document defines the canonical data lake zones and the environment variables that control their locations. Treat this file, together with `.env.context` and `src/common/zones.py`, as the source of truth for paths and configuration.

## Zone Directories

The data lake uses numbered zone directories under `PROJECT_ROOT`:

- `1_landing/` — Initial ingestion of raw files from external services.
- `2_raw/` — Validated, immutable copies of landing data.
- `3_staging/` — Cleaned, standardized, and enriched data.
- `4_curated/` — Business‑ready datasets for analytics, dashboards, and ML.
- `5_archive/` — Canonical archive zone for historical data.

There is also an `archive/` directory at the project root. This is a legacy/auxiliary archive area used by some older scripts; the canonical archive zone for new work is always `5_archive/`.

Pipeline orchestration scripts live in:

- `6_automated_cronjob/` — Windows batch and shell scripts for running the full pipeline and cleaners‑only variants.

## Environment Variables

Core env vars (see `.env.example` and `.env.context`):

- `PROJECT_ROOT` — Absolute path to `data_lake/`. All other paths are resolved from here.
- `DATA_ECOSYSTEM_PATH` — Absolute path to the monorepo root (parent of `data_lake/`).
- `DASHBOARD_PATH` — Absolute path to the dashboard project.

Zone routing env vars (consumed by `src/common/zones.py`):

- `LANDING_ZONE` — Defaults to `1_landing`.
- `RAW_ZONE` — Defaults to `2_raw`.
- `STAGING_ZONE` — Defaults to `3_staging`.
- `CURATED_ZONE` — Defaults to `4_curated`.
- `ARCHIVE_ZONE` — Defaults to `5_archive`.
- `SANDBOX_ZONE` — Optional sandbox area for experiments.

Logging:

- `LOG_DIR` — Defaults to `logs` under `PROJECT_ROOT`.

Cookie filenames (loaded by `common.zones.get_cookie_path` and `.env.context`):

- `SPOTIFY_COOKIE_FILE`, `TIKTOK_COOKIE_FILE_*`, `DISTROKID_COOKIE_FILE`, `TOOLOST_COOKIE_FILE`, `LINKTREE_COOKIE_FILE`, `METAADS_COOKIE_FILE`.

## Zones Helper Module

`src/common/zones.py` centralizes all zone and URL logic. Typical usage:

```python
from common.zones import (
    PROJECT_ROOT,
    LANDING_ZONE,
    RAW_ZONE,
    STAGING_ZONE,
    CURATED_ZONE,
    ARCHIVE_ZONE,
    get_landing_path,
    get_raw_path,
    get_staging_path,
    get_curated_path,
    get_archive_path,
    get_cookie_path,
)
```

Examples:

```python
# Landing path for a service
landing_dir = get_landing_path("spotify", "audience")

# Staging CSV output for a service
staging_dir = get_staging_path("metaads")

# Canonical curated directory
curated_dir = CURATED_ZONE

# Archive path for a service
archive_dir = get_archive_path("tiktok")
```

When adding new code:

- Prefer `get_*_path` helpers over hardcoded `"3_staging"` / `"4_curated"` string literals.
- Use env vars for service URLs via `get_service_url(service, url_type)` where appropriate.
- Do not introduce new hardcoded `landing/`, `raw/`, `staging/`, or `curated/` strings for filesystem paths; always go through `common.zones`.

