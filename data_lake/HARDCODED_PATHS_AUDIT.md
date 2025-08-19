# 🔍 Hardcoded File Paths - Detailed Audit

## Summary
After thorough analysis, I found **multiple types of hardcoded paths** that were missed in the initial audit:

### 1. **Hardcoded Numbered Directory Paths** (30+ occurrences)
These should use environment variables instead:

```python
# ❌ BAD - Hardcoded
ARCHIVE = PROJECT_ROOT / "5_archive"
STAGING_DIR = PROJECT_ROOT / "3_staging" / "spotify" / "audience"
CURATED_DIR = PROJECT_ROOT / "4_curated"

# ✅ GOOD - Using environment variables
STAGING = PROJECT_ROOT / os.getenv("STAGING_ZONE", "3_staging")
```

**Files with hardcoded numbered paths:**
- `src/archive_old_data.py` - hardcoded "5_archive"
- `src/metaads/cleaners/metaads_daily_raw2staging.py` - hardcoded "3_staging"
- `src/metaads/cleaners/metaads_daily_staging2curated.py` - hardcoded "3_staging", "4_curated", "5_archive"
- `src/spotify/cleaners/spotify_landing2staging.py` - hardcoded "3_staging"
- `src/spotify/cleaners/spotify_staging2curated.py` - hardcoded "3_staging", "4_curated", "5_archive"
- `src/tiktok/cleaners/tiktok_raw2staging.py` - hardcoded "3_staging"
- `src/tiktok/cleaners/tiktok_staging2curated.py` - hardcoded "3_staging", "4_curated", "5_archive"
- `src/tiktok/migrate_reach_to_views.py` - hardcoded "3_staging", "4_curated", "5_archive"

### 2. **Old Directory Names in String Literals** (20+ occurrences)
References to old names in:
- Comments and docstrings
- Log messages
- Variable names

```python
# Found in src/common/monitor_pipeline_health.py
self.zones = ["landing", "raw", "staging", "curated"]  # ❌ Should be updated

# Found in src/linktree/cleaners/linktree_raw2staging.py
STAGING_ZONE = os.environ.get("STAGING_ZONE", "staging")  # ❌ Default should be "3_staging"
```

### 3. **Relative Path Navigation** (1 occurrence)
```python
# src/distrokid/extractors/dk_auth.py
os.path.join(os.path.dirname(__file__), "../../../1_landing/distrokid/streams")
```
This uses relative path navigation (`../../../`) which is fragile and breaks if file is moved.

### 4. **Mixed Approach - Some Using Env, Some Not**
The codebase is inconsistent:
- Some files use `os.getenv("STAGING_ZONE", "3_staging")`
- Others hardcode `PROJECT_ROOT / "3_staging"`

## Recommendations

### 1. **Standardize Zone References**
Create a central configuration module:
```python
# src/common/zones.py
import os
from pathlib import Path

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "."))

LANDING_ZONE = PROJECT_ROOT / os.getenv("LANDING_ZONE", "1_landing")
RAW_ZONE = PROJECT_ROOT / os.getenv("RAW_ZONE", "2_raw")
STAGING_ZONE = PROJECT_ROOT / os.getenv("STAGING_ZONE", "3_staging")
CURATED_ZONE = PROJECT_ROOT / os.getenv("CURATED_ZONE", "4_curated")
ARCHIVE_ZONE = PROJECT_ROOT / os.getenv("ARCHIVE_ZONE", "5_archive")
```

### 2. **Update All Hardcoded Paths**
Replace all instances of:
- `PROJECT_ROOT / "1_landing"` → Use `LANDING_ZONE` from common.zones
- `PROJECT_ROOT / "2_raw"` → Use `RAW_ZONE` from common.zones
- etc.

### 3. **Fix Environment Variable Defaults**
Update all occurrences of:
- `os.getenv("STAGING_ZONE", "staging")` → `os.getenv("STAGING_ZONE", "3_staging")`
- Similar for other zones

### 4. **Update String References**
Update monitoring scripts that reference old zone names:
- `self.zones = ["landing", "raw", "staging", "curated"]`
- Should be: `self.zones = ["1_landing", "2_raw", "3_staging", "4_curated"]`

## Impact Assessment
- **High Priority**: 30+ hardcoded numbered paths that bypass environment configuration
- **Medium Priority**: 20+ references to old directory names in strings/comments
- **Low Priority**: Documentation and comment updates

This represents a significant technical debt that should be addressed to ensure consistency and maintainability.