# Spotify Song Metrics Extraction - Investigation Notes

**Status**: In Progress
**Last Updated**: 2025-12-02
**Purpose**: Document network behavior and UI selectors for extracting individual song metrics across multiple time periods.

---

## Overview

Extending the Spotify audience extractor to capture individual song performance metrics. The goal is to collect song-level data across 5 time periods:
- 24 hours
- 7 days
- 28 days
- 12 months
- All time

---

## New Workflow (Steps 5.5 - Between Audience Download and Multi-Artist Loop)

### Step 5.5.1: Navigate to Music/Songs Page

**URL Pattern**:
```
https://artists.spotify.com/c/artist/{ARTIST_ID}/music/songs
```

**Alternative Navigation** - Click the "Music" button:
```html
<span class="e-9935-text encore-text-body-small encore-internal-color-text-base sc-c7d3249f-2 cpsZQQ"
      data-encore-id="text">Music</span>
```

**Suggested Selector**:
```python
MUSIC_NAV_SELECTOR = "span[data-encore-id='text']:has-text('Music')"
```

---

### Step 5.5.2: Open Filters Menu

**Filter Button HTML**:
```html
<button class="Chip__ChipComponent-sc-ry3uox-0 iwPnvk sc-84f1dbd7-0 eBYbPq"
        role="button"
        aria-checked="false"
        data-encore-id="chipFilter"
        tabindex="0"
        aria-disabled="false"
        aria-label="Select to further filter your results">
    <span class="e-9935-text encore-text-body-small Label-sc-k61801-0 dbQbRT" data-encore-id="text">
        <div class="sc-7bca2fd7-1 jRYKDh">Filters</div>
    </span>
    <span class="Icon__IconSpacer-sc-1hpzz1n-0 kOxhPE">
        <svg data-encore-id="icon" role="img" aria-hidden="true"
             class="e-9935-icon e-9935-baseline" viewBox="0 0 16 16">
            <path d="M10.75 13.25a1.5 1.5 0 1 0 .001-2.998 1.5 1.5 0 0 0-.001 2.998m4.5-.75h-1.595a3.001 3.001 0 0 1-5.81 0H.75a.75.75 0 0 1 0-1.5h7.095a3.001 3.001 0 0 1 5.81 0h1.595a.75.75 0 0 1 0 1.5M5.353 5.747a1.5 1.5 0 1 0-.206-2.993 1.5 1.5 0 0 0 .206 2.993M15.25 5H8.155a3.001 3.001 0 0 1-5.81 0H.75a.75.75 0 0 1 0-1.5h1.595a3.001 3.001 0 0 1 5.81 0h7.095a.75.75 0 0 1 0 1.5"></path>
        </svg>
    </span>
</button>
```

**Suggested Selectors**:
```python
# Primary - by aria-label
SONGS_FILTER_BUTTON = "button[aria-label='Select to further filter your results']"

# Fallback - by data-encore-id
SONGS_FILTER_BUTTON_ALT = "button[data-encore-id='chipFilter']"

# Fallback - by text content
SONGS_FILTER_BUTTON_TEXT = "button:has-text('Filters')"
```

---

### Step 5.5.3: Time Period Filter Menu Structure

**Menu Container**:
```html
<div class="sc-bf1bee9-0 jSuOJg">
    <div data-testid="time-filter" class="sc-bf1bee9-0 hjTXWd">
        <div aria-label="Select to view results from each time period"
             aria-activedescendant="28 days"
             data-encore-id="formGroup"
             class="Group-sc-u9bcx5-0 jZRYDy">
            <!-- Radio buttons here -->
        </div>
    </div>
</div>
```

**Time Period Radio Buttons**:

| Time Period | Input ID | Input Name | Label Text |
|-------------|----------|------------|------------|
| 24 hours    | `1day`   | `24 hours` | 24 hours   |
| 7 days      | `7day`   | `7 days`   | 7 days     |
| 28 days     | `28day`  | `28 days`  | 28 days    |
| 12 months   | `1year`  | `12 months`| 12 months  |
| All time    | `all`    | `All time` | All time   |

**Radio Button HTML Pattern**:
```html
<div data-encore-id="formRadio" class="Radio-sc-tr5kfi-0 jTShvD">
    <input type="radio" id="1day" name="24 hours"
           class="e-9935-visually-hidden" data-encore-id="visuallyHidden">
    <label for="1day" class="Label-sc-17gd8mo-0 bbdvyE">
        <span class="Indicator-sc-hjfusp-0 iTKfcw"></span>
        <span class="e-9935-text encore-text-body-small TextForLabel-sc-1wen0a8-0 emGrMR"
              data-encore-id="text">24 hours</span>
    </label>
</div>
```

**Suggested Selectors**:
```python
TIME_FILTER_SELECTORS = {
    "24h": "input#1day",      # or label[for='1day']
    "7d":  "input#7day",      # or label[for='7day']
    "28d": "input#28day",     # or label[for='28day']
    "12m": "input#1year",     # or label[for='1year']
    "all": "input#all",       # or label[for='all']
}

# Alternative using labels (more clickable)
TIME_FILTER_LABELS = {
    "24h": "label[for='1day']",
    "7d":  "label[for='7day']",
    "28d": "label[for='28day']",
    "12m": "label[for='1year']",
    "all": "label[for='all']",
}
```

---

## Network Request Behavior

### Request Pattern

When a time filter radio button is clicked, the page generates a network request:

**URL Pattern**:
```
/songs?time-filter={filter_value}
```

**Filter Values**:
| UI Label    | Query Parameter Value |
|-------------|----------------------|
| 24 hours    | `1day`               |
| 7 days      | `7day`               |
| 28 days     | `28day`              |
| 12 months   | `1year`              |
| All time    | `all`                |

**Example Full URLs**:
```
https://artists.spotify.com/c/artist/62owJQCD2XzVB2o19CVsFM/music/songs?time-filter=1day
https://artists.spotify.com/c/artist/62owJQCD2XzVB2o19CVsFM/music/songs?time-filter=7day
https://artists.spotify.com/c/artist/62owJQCD2XzVB2o19CVsFM/music/songs?time-filter=28day
https://artists.spotify.com/c/artist/62owJQCD2XzVB2o19CVsFM/music/songs?time-filter=1year
https://artists.spotify.com/c/artist/62owJQCD2XzVB2o19CVsFM/music/songs?time-filter=all
```

---

## Data Capture Strategy

### Option A: Intercept Network Responses (Recommended)

Use Playwright's `page.route()` or `page.on('response')` to intercept the API responses:

```python
# Pseudocode
async def capture_song_metrics(page, artist_id):
    captured_data = {}

    def handle_response(response):
        if '/songs?' in response.url and 'time-filter=' in response.url:
            # Extract filter value from URL
            # Parse JSON response
            # Store in captured_data
            pass

    page.on('response', handle_response)

    # Click through each time filter
    for period, selector in TIME_FILTER_LABELS.items():
        page.click(selector)
        page.wait_for_load_state('networkidle')

    return captured_data
```

### Option B: Direct URL Navigation

Navigate directly to each URL and scrape the resulting page/API response:

```python
TIME_PERIODS = ['1day', '7day', '28day', '1year', 'all']

for period in TIME_PERIODS:
    url = f"https://artists.spotify.com/c/artist/{artist_id}/music/songs?time-filter={period}"
    page.goto(url)
    # Capture response or scrape table
```

---

## Landing Zone Output Structure

**Proposed File Naming**:
```
1_landing/spotify/songs/
    spotify_songs_{artist_id}_{time_period}_{timestamp}.json
```

**Examples**:
```
spotify_songs_62owJQCD2XzVB2o19CVsFM_1day_20251202_143022.json
spotify_songs_62owJQCD2XzVB2o19CVsFM_7day_20251202_143025.json
spotify_songs_62owJQCD2XzVB2o19CVsFM_28day_20251202_143028.json
spotify_songs_62owJQCD2XzVB2o19CVsFM_1year_20251202_143031.json
spotify_songs_62owJQCD2XzVB2o19CVsFM_all_20251202_143034.json
```

---

## Expected Response Data Structure

**TBD**: Capture actual network response to document:
- Response headers
- JSON schema
- Field names and types
- Available metrics per song

---

## Implementation Checklist

- [ ] Capture sample network responses for each time period
- [ ] Document JSON response schema
- [x] Implement network interception in extractor
- [x] Create landing directory structure for songs data
- [x] Add song metrics extraction to main workflow
- [ ] Create cleaners for song metrics (landing2raw, raw2staging, staging2curated)
- [ ] Add tests for new functionality

---

## Notes

- The "Locations" filter requires navigating to a specific song/release detail page first
- Default selection appears to be "28 days" based on `checked=""` attribute
- Radio buttons use visually-hidden inputs with visible labels - click the labels
- Network requests may require authentication headers from the session

---

## Related Files

- Extractor: `src/spotify/extractors/spotify_audience_extractor.py`
- Cookie utilities: `src/common/cookies.py`
- Spotify CLAUDE.md: `src/spotify/CLAUDE.md`
