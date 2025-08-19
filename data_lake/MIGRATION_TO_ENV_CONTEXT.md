# Migration Guide: Using .env.context and zones.py

## Overview
This guide explains how to migrate hardcoded paths and URLs to use the new centralized configuration system.

## Quick Start

### 1. Import the zones module
```python
from common.zones import (
    PROJECT_ROOT, LANDING_ZONE, RAW_ZONE, STAGING_ZONE, 
    CURATED_ZONE, ARCHIVE_ZONE, get_service_url
)
```

### 2. Replace hardcoded paths

#### ❌ OLD (Hardcoded)
```python
STAGING_DIR = PROJECT_ROOT / "3_staging" / "spotify" / "audience"
CURATED_DIR = PROJECT_ROOT / "4_curated"
ARCHIVE_DIR = PROJECT_ROOT / "5_archive" / "spotify" / "audience"
```

#### ✅ NEW (Using zones module)
```python
from common.zones import get_staging_path, CURATED_ZONE, get_archive_path

STAGING_DIR = get_staging_path("spotify", "audience")
CURATED_DIR = CURATED_ZONE
ARCHIVE_DIR = get_archive_path("spotify", "audience")
```

### 3. Replace hardcoded URLs

#### ❌ OLD (Hardcoded)
```python
self.login_url = 'https://distrokid.com/signin'
self.dashboard_url = 'https://distrokid.com/stats/?data=streams'
```

#### ✅ NEW (Using zones module)
```python
from common.zones import get_service_url

self.login_url = get_service_url('distrokid', 'login')
self.dashboard_url = get_service_url('distrokid', 'dashboard')
```

## Migration Examples by File Type

### Extractors
```python
# Before
LANDING_DIR = Path(PROJECT_ROOT) / "1_landing" / "spotify" / "audience"

# After
from common.zones import get_landing_path
LANDING_DIR = get_landing_path("spotify", "audience")
```

### Cleaners (landing2raw)
```python
# Before
LANDING = PROJECT_ROOT / "1_landing"
RAW = PROJECT_ROOT / "2_raw"

# After
from common.zones import LANDING_ZONE, RAW_ZONE
LANDING = LANDING_ZONE
RAW = RAW_ZONE
```

### Cleaners (staging2curated)
```python
# Before
STAGING_DIR = PROJECT_ROOT / "3_staging" / "tiktok"
CURATED_DIR = PROJECT_ROOT / "4_curated"
ARCHIVE_DIR = PROJECT_ROOT / "5_archive" / "tiktok"

# After
from common.zones import get_staging_path, CURATED_ZONE, get_archive_path
STAGING_DIR = get_staging_path("tiktok")
CURATED_DIR = CURATED_ZONE
ARCHIVE_DIR = get_archive_path("tiktok")
```

### Cookie Refresh Strategies
```python
# Before
self.login_url = 'https://linktr.ee/login'
self.cookie_path = PROJECT_ROOT / "src" / "linktree" / "cookies" / "linktree_cookies.json"

# After
from common.zones import get_service_url, get_cookie_path
self.login_url = get_service_url('linktree', 'login')
self.cookie_path = get_cookie_path('linktree')
```

## Environment Variable Defaults

The zones module handles missing environment variables gracefully:

```python
# If STAGING_ZONE is not set, defaults to "3_staging"
STAGING_ZONE = PROJECT_ROOT / os.getenv("STAGING_ZONE", "3_staging")
```

## Files Requiring Updates

### High Priority (Core functionality)
1. `src/archive_old_data.py`
2. All files in `*/cleaners/` directories
3. All files in `*/extractors/` directories
4. `src/common/pipeline_health_monitor.py`
5. `src/common/monitor_pipeline_health.py`

### Medium Priority (Cookie refresh system)
1. `src/common/cookie_refresh/strategies/*.py`
2. `src/common/cookie_refresh/dashboard.py`
3. `src/common/cookie_refresh/metrics_exporter.py`

### Low Priority (Utilities and tests)
1. Migration scripts
2. Test files
3. Documentation

## Testing the Migration

After updating a file:

1. **Import Test**: Ensure the file imports without errors
```bash
python -c "import src.spotify.extractors.spotify_audience_extractor"
```

2. **Path Test**: Verify paths are created correctly
```python
from common.zones import get_staging_path
print(get_staging_path("spotify", "audience"))
# Should output: /path/to/project/3_staging/spotify/audience
```

3. **URL Test**: Verify URLs load from environment
```python
from common.zones import get_service_url
print(get_service_url('spotify', 'login'))
# Should output: https://artists.spotify.com
```

## Rollback Plan

If issues occur:
1. The old hardcoded values still work as fallbacks
2. You can gradually migrate file by file
3. The .env.context file can be modified without code changes

## Benefits of Migration

1. **Flexibility**: Change paths/URLs without modifying code
2. **Consistency**: All configuration in one place
3. **Environment-specific**: Different settings for dev/prod
4. **Maintainability**: Easier to update when services change
5. **Security**: Sensitive values can be kept out of code

## Next Steps

1. Start with one service (e.g., Spotify) as a pilot
2. Test thoroughly before moving to the next service
3. Update documentation as you go
4. Consider adding validation to ensure all required env vars are set