# Repository Guidelines

## Orientation
- Confirm the working directory is ``%PROJECT_ROOT%`` (``C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake`` by default) before executing commands; similar names have caused destructive mistakes.
- Read `.claude/CLAUDE.md` whenever you pick up new work. It tracks zone contracts, platform readiness, and the semi-manual authentication policy that governs every extractor.

## Environment Variables (Use Them Every Time)
- ``PROJECT_ROOT`` and ``DATA_ECOSYSTEM_PATH`` anchor every path lookup; resolve files with ``os.getenv``/``Path`` instead of hardcoding.
- Zone routing depends on ``LANDING_ZONE``, ``RAW_ZONE``, ``STAGING_ZONE``, ``CURATED_ZONE``, ``ARCHIVE_ZONE``, and ``SANDBOX_ZONE``-use them when writing/reading pipeline outputs.
- Integration pointers: ``DASHBOARD_PATH`` and ``DATA_ECOSYSTEM_PATH`` let you hand data to sibling services without brittle relative paths.
- Automation helpers: ``PLAYWRIGHT_SESSION_DIR`` (cookie cache), credential placeholders (``DK_EMAIL``/``DK_PASSWORD``, ``TOOLOST_EMAIL``/``TOOLOST_PASSWORD``, ``SPOTIFY_EMAIL``, ``LINKTREE_USERNAME``), and API tokens (``GITHUB_ACCESS_TOKEN``, ``META_ACCESS_TOKEN``, ``META_AD_ACCOUNT_ID``). Reference them via environment lookups and keep secrets out of code.
- Pattern: load ``dotenv`` early in CLIs, log which variables were found (never their values), and bail fast if a required key is missing.

## Architecture & Ownership
- Six zones drive the lifecycle: ``1_landing`` -> ``2_raw`` -> ``3_staging`` -> ``4_curated`` -> ``5_archive`` with ``6_automated_cronjob`` orchestrating runs.
- Source code: ``src/<platform>/extractors`` (ingest), ``src/<platform>/cleaners`` (promotion), ``src/common`` (shared utilities, cookie refresh suite). Tests mirror the structure under ``tests/<platform>/``.
- Active platforms: TooLost, Spotify, TikTok, DistroKid, Linktree, MetaAds. Instagram/YouTube/MailChimp remain stubs-flag scope creep before implementing.

## Runbook & Quality Gates
- Bootstrap: ``python -m venv .venv && .venv\Scripts\activate`` then ``pip install -r requirements.txt`` (ensure the venv respects ``PROJECT_ROOT``).
- Pipelines: ``6_automated_cronjob\run_datalake_cron.bat`` (full pipeline) or ``6_automated_cronjob\run_datalake_cron_no_extractors.bat`` (cleaners only / automated mode to skip services awaiting re-auth).
- Testing: ``pytest -ra --cov=src --cov-report=term-missing`` plus focused suites (``pytest tests/<platform>/ -v``). Bake zone assertions and checksum guards into new tests.
- Style: ``black src/``, ``isort src/``, ``flake8 src/``, ``mypy src/``. Emit structured logs that include zone names and record counts.
- **IMPORTANT!!!** Playwright discipline: run every Playwright-driven extractor **non-headless** so Cloudflare and auth challenges render and succeed; do not toggle headless on for any service.

## Authentication & Cookie Discipline
- Semi-manual by design: extractors never bypass MFA. Expect cookies to expire and prompt users for new credentials.
- Use ``src/common/cookie_refresh/check_status.py`` and ``manual_refresh.py`` (with ``--service``) to manage sessions. Schedule refreshes via ``scheduler.py`` but never store raw secrets.
- Document authentication events in PR notes and purge residual cookie files from commits.

## Data Stewardship
- Write outputs using the zone env variables-no literal paths. Validate directory existence at runtime and fail fast if the environment is misconfigured.
- Archive heavy artifacts in ``backups/`` or MinIO; summarize retention decisions in ``changelog.md``.
- When onboarding a new platform, update the service table in `.claude/CLAUDE.md`, extend tests, and describe the env keys your code consumes.

