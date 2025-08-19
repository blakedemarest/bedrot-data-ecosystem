# 🧠 BEDROT Data Lake - Codebase Audit Report

**Project Root**: `/mnt/c/Users/Earth/BEDROT PRODUCTIONS/bedrot-data-ecosystem/data_lake`  
**Audit Date**: 2025-07-16  
**Total Files Scanned**: 77 Python files, 5 batch files  
**Function Registry**: `__data_lake__function_registry.json`

---

## 📍 PROJECT ANALYSIS OVERVIEW

The BEDROT Data Lake codebase consists of:
- **77 Python files** containing 313 functions
- **5 batch files** for pipeline automation
- Multi-service ETL pipeline (Spotify, TikTok, DistroKid, TooLost, Linktree, MetaAds)
- Cookie refresh automation system
- Zone-based data processing (1_landing → 2_raw → 3_staging → 4_curated → 5_archive)

---

## 🧩 A. POTENTIAL DUPLICATE OR NEAR-DUPLICATE FUNCTIONS (41 found)

### Critical Duplications:
1. **Data Freshness Checking**
   - `_check_data_freshness()` in `src/common/integrity_checks.py`
   - `check_data_freshness()` in `src/common/monitor_pipeline_health.py`
   - **Recommendation**: Consolidate into single function in common utilities

2. **Logging Setup**
   - `setup_logging()` in `src/common/logging_config.py`
   - `_setup_logging()` in `src/common/cookie_refresh/refresher.py`
   - **Recommendation**: Use central logging configuration

3. **Cookie Status Checking**
   - `check_cookie_status()` in `src/toolost/extractors/toolost_scraper_cron.py`
   - `status()` in `src/common/cookie_refresh/storage.py`
   - **Recommendation**: Use unified cookie management system

4. **Report Saving**
   - `save_report()` in `src/common/monitor_pipeline_health.py`
   - `_save_reports()` in `src/common/pipeline_health_monitor.py`
   - **Recommendation**: Merge into single reporting module

### Name Collision Issues:
- Multiple `format()` functions across different modules (8 occurrences)
- Multiple `filter()` functions with different purposes
- **Recommendation**: Use more descriptive, unique function names

---

## 🗃️ B. DUPLICATE OR REDUNDANT SCRIPTS (5 batch files found)

### Pipeline Execution Scripts:
1. `6_automated_cronjob/run_datalake_cron.bat`
2. `6_automated_cronjob/run_datalake_cron_no_extractors.bat`
3. `run_pipeline_simple.bat`
4. `run_pipeline_windows.bat`

**Analysis**: Multiple batch files serve similar purposes (running the pipeline) with slight variations:
- Some include extractors, others don't
- Some have authentication checks, others don't
- **Recommendation**: Consolidate into single parameterized script

### Cookie Management:
5. `setup_cookie_refresh.bat` - Standalone cookie refresh setup
   - **Recommendation**: Integrate into main pipeline script

---

## 🧨 C. HARDCODED FILE PATHS (30+ found)

**Critical Issue**: Despite using `PROJECT_ROOT`, many files hardcode the zone directories instead of using environment variables:

### Hardcoded Numbered Paths:
```python
# Examples found:
ARCHIVE = PROJECT_ROOT / "5_archive"  # src/archive_old_data.py
STAGING_DIR = PROJECT_ROOT / "3_staging" / "spotify"  # Multiple files
CURATED_DIR = PROJECT_ROOT / "4_curated"  # Multiple files
```

### Affected Files:
- `src/archive_old_data.py`
- Multiple files in `metaads/cleaners/`
- Multiple files in `spotify/cleaners/`
- Multiple files in `tiktok/cleaners/`
- `src/tiktok/migrate_reach_to_views.py`

### Other Issues:
- Old zone names ("staging", "curated") still referenced in monitoring scripts
- Relative path navigation (`../../../`) in `dk_auth.py`
- Inconsistent use of environment variables

**See HARDCODED_PATHS_AUDIT.md for detailed analysis**

**Recommendation**: Create central `zones.py` module and update all hardcoded paths.

---

## 🔐 D. HARDCODED SECRETS OR API-LIKE VALUES (0 found)

**Excellent Security Practice**: No hardcoded API keys, tokens, or secrets found in source code.

The codebase properly uses:
- Cookie files for authentication
- Environment variables for sensitive data
- Separate cookie storage per service

---

## 🧪 E. .ENV MISUSE OR OMISSION (27 found)

### Hardcoded URLs (Should be in environment/config):
1. **Cookie Refresh Strategies**:
   ```python
   # src/common/cookie_refresh/strategies/distrokid.py
   self.login_url = 'https://distrokid.com/signin'
   self.dashboard_url = 'https://distrokid.com/stats/?data=streams'
   
   # src/common/cookie_refresh/strategies/spotify.py
   self.artists_url = 'https://artists.spotify.com'
   
   # src/common/cookie_refresh/strategies/tiktok.py
   self.login_url = 'https://www.tiktok.com/login'
   ```
   **Recommendation**: Move all service URLs to configuration file or environment variables

2. **Server Configuration**:
   ```python
   # src/common/cookie_refresh/metrics_exporter.py
   self.app.run(host='0.0.0.0', port=self.port, debug=False)
   ```
   **Recommendation**: Use environment variables for host/port configuration

3. **API Endpoints**:
   - Multiple instances of hardcoded API URLs across extractors
   - **Recommendation**: Create service-specific configuration files

---

## 📊 SUMMARY METRICS

| Violation Type      | Count | Severity |
|---------------------|-------|----------|
| Duplicate Functions |   41  | Medium   |
| Redundant Scripts   |    5  | Low      |
| Hardcoded Paths     |  30+  | High     |
| Secret Violations   |    0  | N/A      |
| .env Misuse         |   27  | Medium   |

---

## ✅ RECOMMENDATIONS

### Immediate Actions:
1. **Consolidate duplicate functions** - Especially data freshness and logging setup
2. **Create central configuration** - Move all hardcoded URLs to config files
3. **Unify pipeline scripts** - Create single parameterized pipeline runner

### Best Practices to Implement:
1. **Function Naming**: Avoid generic names like `format()`, `filter()`
2. **Configuration Management**: Use `.env.context` for all environment-specific values
3. **Path Management**: Continue using `PROJECT_ROOT` pattern consistently
4. **Documentation**: Update all docs to reflect new numbered directory structure

### Security Considerations:
1. Continue excellent practice of no hardcoded secrets
2. Consider encrypting cookie files at rest
3. Implement cookie rotation schedule

---

## 🎯 NEXT STEPS

1. Review and merge duplicate functions
2. Create comprehensive `.env.context` file with all service URLs
3. Consolidate batch files into single configurable script
4. Update documentation for new directory structure
5. Implement automated tests for common utilities

---

**Function Registry Generated**: `__data_lake__function_registry.json` (313 functions cataloged)