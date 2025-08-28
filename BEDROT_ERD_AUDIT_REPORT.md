# BEDROT ERD Audit Report: Data Redundancy & ETL Risk Analysis

## 🚨 CRITICAL ISSUES IDENTIFIED

### 1. **MASSIVE Spotify Double-Counting Risk**

**Problem**: Three different Spotify stream sources that WILL create confusion:
- `tidy_daily_streams.csv`: `spotify_streams` column (distributor data)
- `spotify_audience_curated_*.csv`: `streams` column (API data) 
- `dk_bank_details.csv`: Financial transactions that also represent streams

**Current Schema Weakness**:
```sql
-- PROBLEMATIC: These could all refer to the same streams!
DAILY_STREAMS: stream_count (from tidy_daily_streams.spotify_streams)
SPOTIFY_AUDIENCE: streams_28d (from spotify_audience.streams) 
ROYALTY_TRANSACTIONS: quantity (from dk_bank_details.Quantity)
```

**ETL Disaster Scenario**:
```python
# This would TRIPLE-COUNT the same Spotify streams:
total_streams = daily_streams.sum() + spotify_audience.sum() + royalty_quantity.sum()
# Result: Completely wrong analytics, impossible to debug
```

### 2. **Track Identity Crisis**

**Problem**: No reliable track matching across data sources
- `tidy_daily_streams`: NO track information (aggregated only)
- `spotify_audience`: NO track breakdown (artist-level only)
- `dk_bank_details`: Has track title + ISRC but inconsistent naming

**Schema Weakness**:
```sql
-- DAILY_STREAMS.track_id will be NULL for most records!
-- How do you attribute streams to specific tracks?
```

**Real Data Evidence**:
```csv
# tidy_daily_streams.csv - NO track info
date,spotify_streams,apple_streams,combined_streams,source
2024-08-23,40,0,40,distrokid

# dk_bank_details.csv - HAS track info but different granularity  
Date,Store,Artist,Title,ISRC,Quantity,Earnings
2025-08-13,Luna,PIG1987,KEYGEN,QZWFK2497196,1,0.00018304
```

### 3. **Artist Matching Hell**

**Problem**: Inconsistent artist identifiers across sources
- `spotify_audience`: Uses `artist_id` (1Eu67EqPy2NutiM0lqCarw) + `artist_name` (pig1987)
- `dk_bank_details`: Uses `Artist` (PIG1987) - different casing!
- `tidy_daily_streams`: NO artist info at all

**ETL Failure Point**:
```python
# This join will FAIL due to case sensitivity:
spotify_data['artist'] = 'pig1987'  # lowercase
financial_data['Artist'] = 'PIG1987'  # uppercase
# Result: Data appears to be for different artists!
```

### 4. **Temporal Data Alignment Issues**

**Problem**: Different data sources have different time granularities
- `tidy_daily_streams`: Daily data
- `spotify_audience`: Daily data BUT with 28-day rolling streams
- `dk_bank_details`: Transaction reporting dates vs. actual sale dates
- `metaads`: Daily performance but campaigns span weeks

**Schema Risk**:
```sql
-- When joining by date, what are you actually joining?
SELECT * FROM daily_streams ds
JOIN spotify_audience sa ON ds.stream_date = sa.snapshot_date
-- Are these the same "day" of activity? NO!
```

## 🔧 SCHEMA FIXES NEEDED

### Fix #1: Explicit Stream Source Tracking
```sql
-- MODIFIED DAILY_STREAMS TABLE
CREATE TABLE daily_streams (
    stream_record_id INTEGER PRIMARY KEY,
    stream_date DATE NOT NULL,
    track_id INTEGER, -- Will be NULL for aggregated data!
    platform_id INTEGER NOT NULL,
    territory_id INTEGER NOT NULL,
    data_source VARCHAR(20) NOT NULL, -- 'distrokid_aggregated', 'spotify_api', 'financial'
    data_granularity VARCHAR(20) NOT NULL, -- 'track_level', 'artist_level', 'platform_level'
    stream_count BIGINT NOT NULL,
    revenue_usd DECIMAL(12,4),
    source_file VARCHAR(200), -- Track which CSV file this came from
    is_estimated BOOLEAN DEFAULT FALSE, -- Flag for attributed/estimated data
    -- Add constraints to prevent mixing incompatible data
    CHECK (
        (data_source = 'distrokid_aggregated' AND track_id IS NULL) OR
        (data_source = 'spotify_api' AND data_granularity = 'artist_level') OR
        (data_source = 'financial' AND track_id IS NOT NULL)
    )
);
```

### Fix #2: Robust Artist Identity Management
```sql
-- NEW ARTIST_ALIASES TABLE
CREATE TABLE artist_aliases (
    alias_id INTEGER PRIMARY KEY,
    artist_id INTEGER NOT NULL,
    alias_name VARCHAR(100) NOT NULL,
    source_system VARCHAR(50), -- 'spotify_api', 'distrokid', 'financial'
    is_primary BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
);

-- Insert all known variations
INSERT INTO artist_aliases (artist_id, alias_name, source_system, is_primary) VALUES
(1, 'PIG1987', 'primary', TRUE),
(1, 'pig1987', 'spotify_api', FALSE),
(1, 'PIG 1987', 'social_media', FALSE);
```

### Fix #3: Track Attribution Logic
```sql
-- NEW STREAM_ATTRIBUTION_RULES TABLE
CREATE TABLE stream_attribution_rules (
    rule_id INTEGER PRIMARY KEY,
    data_source VARCHAR(20),
    attribution_method VARCHAR(50), -- 'by_revenue_share', 'equal_split', 'historical_pattern'
    is_active BOOLEAN DEFAULT TRUE
);

-- For handling aggregated data without track info
CREATE TABLE estimated_track_streams (
    estimate_id INTEGER PRIMARY KEY,
    stream_record_id INTEGER,
    track_id INTEGER,
    estimated_stream_count BIGINT,
    attribution_confidence DECIMAL(3,2), -- 0.0 to 1.0
    attribution_method VARCHAR(50),
    FOREIGN KEY (stream_record_id) REFERENCES daily_streams(stream_record_id),
    FOREIGN KEY (track_id) REFERENCES tracks(track_id)
);
```

## 🚨 ETL FAILURE SCENARIOS TO PREVENT

### Scenario 1: "The Great Stream Inflation"
```python
# WRONG ETL LOGIC (will happen without proper constraints)
def load_streaming_data():
    # Load distributor data
    distrokid_streams = load_csv('tidy_daily_streams.csv')
    
    # Load Spotify API data  
    spotify_streams = load_csv('spotify_audience_curated.csv')
    
    # DISASTER: Add them together!
    total_streams = distrokid_streams['spotify_streams'].sum() + spotify_streams['streams'].sum()
    
    # Result: 2x to 3x actual stream counts!
    return total_streams  # COMPLETELY WRONG

# CORRECT ETL LOGIC
def load_streaming_data():
    # Choose ONE source per platform per time period
    if data_source == 'distributor':
        return load_distributor_data()  # Use this for cross-platform totals
    elif data_source == 'spotify_api':
        return load_spotify_api_data()   # Use this for Spotify-specific analytics
    else:
        raise ValueError("Must specify single data source!")
```

### Scenario 2: "The Artist Identity Crisis"
```python
# WRONG: Case-sensitive artist matching
def match_artists_wrong():
    spotify_artist = 'pig1987'    # lowercase from API
    financial_artist = 'PIG1987'  # uppercase from DistroKid
    
    if spotify_artist == financial_artist:  # FALSE!
        return "match"
    else:
        return "different_artists"  # WRONG CONCLUSION

# CORRECT: Use alias table
def match_artists_correct():
    def get_canonical_artist_id(alias_name):
        # Query artist_aliases table
        return db.query("""
            SELECT artist_id FROM artist_aliases 
            WHERE LOWER(alias_name) = LOWER(?)
        """, [alias_name])[0]
    
    spotify_id = get_canonical_artist_id('pig1987')    # Returns 1
    financial_id = get_canonical_artist_id('PIG1987')  # Returns 1
    
    return spotify_id == financial_id  # TRUE!
```

### Scenario 3: "The Track Attribution Disaster"
```python
# WRONG: Assuming track-level data exists everywhere
def attribute_streams_wrong():
    daily_streams = load_csv('tidy_daily_streams.csv')  # NO track info!
    
    # This will crash - no 'track' column exists
    track_performance = daily_streams.groupby('track')['spotify_streams'].sum()
    
    return track_performance  # CRASH!

# CORRECT: Handle aggregated data
def attribute_streams_correct():
    daily_streams = load_csv('tidy_daily_streams.csv')
    
    if 'track' not in daily_streams.columns:
        # Use attribution algorithm based on financial data
        return estimate_track_attribution(daily_streams)
    else:
        return daily_streams.groupby('track')['streams'].sum()
```

## 🛡️ ETL SAFETY MEASURES

### 1. Data Source Validation
```python
def validate_data_source_consistency():
    """Prevent mixing incompatible data sources"""
    rules = {
        'spotify_streams': ['distrokid', 'toolost'],  # Never mix with 'spotify_api'
        'spotify_api_streams': ['spotify_api'],        # Never mix with distributors
        'financial_streams': ['distrokid', 'toolost'] # These are payments, not streams
    }
    
    # Enforce mutual exclusivity
    for metric, allowed_sources in rules.items():
        if multiple_sources_detected(metric, allowed_sources):
            raise DataIntegrityError(f"Cannot mix {metric} from multiple sources!")
```

### 2. Temporal Alignment Validation
```python
def validate_temporal_alignment():
    """Ensure date fields represent the same thing"""
    checks = [
        ('daily_streams.stream_date', 'Date streams occurred'),
        ('spotify_audience.snapshot_date', 'Date data was captured'),
        ('royalty_transactions.sale_month', 'Month of original sale'),
        ('royalty_transactions.reporting_date', 'Date payment was processed')
    ]
    
    # Don't join different temporal concepts!
    for field, meaning in checks:
        log.warning(f"{field} represents: {meaning}")
```

### 3. Required ETL Constraints
```sql
-- Prevent impossible data combinations
ALTER TABLE daily_streams ADD CONSTRAINT prevent_spotify_double_count
CHECK (
    NOT (data_source IN ('distrokid', 'toolost') AND 
         EXISTS (SELECT 1 FROM daily_streams ds2 
                 WHERE ds2.stream_date = stream_date 
                 AND ds2.platform_id = platform_id 
                 AND ds2.data_source = 'spotify_api'))
);

-- Ensure attribution percentages sum to 100%
CREATE TRIGGER validate_attribution_total
    AFTER INSERT ON estimated_track_streams
BEGIN
    SELECT CASE 
        WHEN (SELECT SUM(attribution_confidence) 
              FROM estimated_track_streams 
              WHERE stream_record_id = NEW.stream_record_id) > 1.01
        THEN RAISE(ABORT, 'Attribution confidence cannot exceed 100%')
    END;
END;
```

## 📊 RECOMMENDED SCHEMA UPDATES

1. **Add explicit data lineage tracking**: Every record knows its source file
2. **Implement artist alias resolution**: Handle all name variations
3. **Create stream attribution engine**: Deal with aggregated data properly  
4. **Add temporal alignment warnings**: Prevent meaningless date joins
5. **Enforce mutual exclusivity**: One Spotify source per analysis

## 💡 IMPLEMENTATION PRIORITY

1. **IMMEDIATE (Week 1)**: Fix Spotify double-counting prevention
2. **HIGH (Week 2)**: Implement artist alias system
3. **MEDIUM (Week 3)**: Build stream attribution logic
4. **LOW (Week 4)**: Add advanced temporal validation

Your current schema is solid conceptually, but these data quality issues will destroy your analytics if not addressed early!