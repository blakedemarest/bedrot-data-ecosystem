"""spotify_audience_extractor.py
Automates Spotify for Artists data extraction via Playwright.

Extracts two types of data:
1. Audience stats CSV (demographics, listener trends)
2. Song metrics JSON across 5 time periods (24h, 7d, 28d, 12m, all time)

Workflow:
1. Navigate to the artist homepage (https://artists.spotify.com/c/en/artist/<ARTIST_ID>).
2. Detect whether login is required; if so, waits for the user (and 2-FA) to finish.
3. Click the **Audience** navigation item.
4. Open **Filters** -> choose **12 months** -> click **Done**.
5. Click the CSV **download** button, capture the download, and write it to
   ``landing/spotify/audience`` with a timestamped filename.
6. Navigate to **Music/Songs** page.
7. For each time period (24h, 7d, 28d, 12m, all time):
   - Select the time filter
   - Intercept the API response containing song metrics
8. Save all captured JSON responses to ``landing/spotify/songs``.

Script follows the conventions in ``LLM_cleaner_guidelines.md`` and is modelled
on ``linktree_analytics_extractor.py``.

Usage
-----
$ python spotify_audience_extractor.py                     # default artists, full extraction
$ python spotify_audience_extractor.py --artists <ID1> <ID2>  # specific artists
$ python spotify_audience_extractor.py --skip-songs        # audience data only (no song metrics)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import re
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure PROJECT_ROOT is set and src/ is on sys.path for direct execution.
PROJECT_ROOT = os.environ.get("PROJECT_ROOT")
if not PROJECT_ROOT:
    raise EnvironmentError("PROJECT_ROOT environment variable must be set.")
SRC_PATH = str(Path(PROJECT_ROOT) / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from common.cookies import load_cookies  # noqa: E402

# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------
DEFAULT_ARTIST_IDS = [
    "62owJQCD2XzVB2o19CVsFM",  # a0
    "1Eu67EqPy2NutiM0lqCarw",  # pig1987
]
LANDING_DIR = Path(PROJECT_ROOT) / "1_landing" / "spotify" / "audience"
LANDING_DIR.mkdir(parents=True, exist_ok=True)

# Updated selectors based on current Spotify UI (2025-07-15)
AUDIENCE_NAV_SELECTOR = "span[data-encore-id='text']:has-text('Audience')"
# Filter button contains SVG with specific path data for sliders icon
FILTER_CHIP_SELECTOR = "button:has(svg[viewBox='0 0 16 16'] path[d*='M10.75 13.25'])"
# 12 months option - look for various possible selectors
FILTER_12M_LABEL = "label[for='1year'], :text('12 months'), input[value='1year'] + label"
# Done button with specific class pattern
FILTER_DONE_SELECTOR = "span:has-text('Done')[class*='button-primary__inner'], button:has-text('Done')"
# Download button contains SVG with circular download icon
CSV_DOWNLOAD_BUTTON = "button:has(svg[viewBox='0 0 24 24'] path[d*='M12 3a9'])"

# ---------------------------------------------------------------------------
# Song Metrics Constants
# ---------------------------------------------------------------------------
SONGS_LANDING_DIR = Path(PROJECT_ROOT) / "1_landing" / "spotify" / "songs"
SONGS_LANDING_DIR.mkdir(parents=True, exist_ok=True)

# Music/Songs page navigation
MUSIC_NAV_SELECTOR = "span[data-encore-id='text']:has-text('Music')"
SONGS_PAGE_URL_TEMPLATE = "https://artists.spotify.com/c/artist/{artist_id}/music/songs"

# Filter button on songs page
SONGS_FILTER_BUTTON_SELECTORS = [
    "button[aria-label='Select to further filter your results']",
    "button[data-encore-id='chipFilter']",
    "button:has-text('Filters')",
]

# Time period filter radio labels
TIME_PERIODS = {
    "1day": "label[for='1day']",
    "7day": "label[for='7day']",
    "28day": "label[for='28day']",
    "1year": "label[for='1year']",
    "all": "label[for='all']",
}

# API URL patterns for network interception
# Actual Spotify API endpoint (not Next.js page data)
SONGS_API_PATTERN = "generic.wg.spotify.com/catalog-view"
SONGS_API_TIME_FILTER_PARAM = "time-filter="


def _click(page, selector: str, desc: str | None = None, retries: int = 3) -> None:
    """Click the first element matching *selector* with basic retry."""
    for attempt in range(1, retries + 1):
        try:
            locator = page.locator(selector).first
            # Wait for element to be both attached and visible
            locator.wait_for(state="attached")
            locator.wait_for(state="visible")
            # Scroll into view if needed
            locator.scroll_into_view_if_needed()
            # Small delay for any animations
            time.sleep(0.5)
            locator.click(force=True)
            if desc:
                print(f"[INFO] Clicked {desc} -> {selector}")
            return
        except Exception as exc:
            print(f"[WARN] Attempt {attempt}/{retries} to click {selector} failed: {exc}")
            time.sleep(2)  # Longer wait between retries
    raise RuntimeError(f"Failed to click element: {selector}")


def _wait_for_audience_nav(page):
    """Ensure the Audience nav link is present – indicates authenticated state."""
    try:
        page.wait_for_selector(AUDIENCE_NAV_SELECTOR, timeout=30000)
        print("[INFO] Audience nav link detected – authentication complete.")
    except PWTimeout:
        raise RuntimeError("Audience nav link not found – are you logged in?")


def _login_if_needed(page, artist_url: str) -> None:
    """Navigate to *artist_url* and wait for login (incl. 2FA) if necessary."""
    print(f"[INFO] Navigating to {artist_url} ...")
    page.goto(artist_url, wait_until="domcontentloaded")

    try:
        _wait_for_audience_nav(page)
    except RuntimeError:
        print("[ACTION REQUIRED] Please log in to Spotify for Artists (2-FA if prompted)...")
        
        # Auto-fill email if environment variable is set
        spotify_email = os.environ.get("SPOTIFY_FOR_ARTISTS_EMAIL") or os.environ.get("SPOTIFY_EMAIL")
        if spotify_email:
            try:
                # Wait for login form to be present
                page.wait_for_selector("#login-username", timeout=10000)
                
                # Wait a moment for the page to fully load
                time.sleep(0.5)
                
                # Fill in the email
                email_input = page.locator("#login-username")
                
                # Clear any existing value first
                email_input.clear()
                time.sleep(0.1)
                
                # Fill the email
                email_input.fill(spotify_email)
                
                # Small delay to ensure the value registers
                time.sleep(0.2)
                
                print(f"[INFO] Auto-filled email: {spotify_email}")
                
                # Note: Password requires manual entry for security
                print("[ACTION REQUIRED] Please enter your password and complete login...")
            except Exception as e:
                print(f"[WARN] Could not auto-fill email: {e}")
        
        # Poll until Audience nav becomes visible or user aborts.
        try:
            _wait_for_audience_nav(page)
        except RuntimeError:
            raise RuntimeError("Login not completed within timeout.")


def _apply_12_month_filter(page):
    """Ensure the audience chart is filtered to the last 12 months."""
    print("[INFO] Opening filter controls...")
    _click(page, FILTER_CHIP_SELECTOR, desc="Filters chip")
    page.wait_for_timeout(1000)

    twelve_months_selected = False

    # Try accessible radio buttons first
    try:
        radio_option = page.get_by_role("radio", name=re.compile(r"12\s*months", re.IGNORECASE))
        radio_option.first.wait_for(state="visible", timeout=4000)
        radio_option.first.check(force=True)
        twelve_months_selected = True
        print("[INFO] Selected 12-month radio option")
    except Exception:
        pass

    if not twelve_months_selected:
        option_selectors = [
            "label:has-text('Last 12 months')",
            "label:has-text('12 months')",
            "button:has-text('Last 12 months')",
            "button:has-text('12 months')",
            "[role='option']:has-text('12 months')",
            "[role='menuitem']:has-text('12 months')",
        ]
        for selector in option_selectors:
            locator = page.locator(selector).first
            try:
                locator.wait_for(state="visible", timeout=4000)
                locator.click(force=True)
                twelve_months_selected = True
                print(f"[INFO] Selected 12-month option via {selector}")
                break
            except Exception:
                continue

    if not twelve_months_selected:
        raise RuntimeError("Unable to locate 12-month time range option in Spotify filters")

    page.wait_for_timeout(800)

    dismiss_selectors = [
        "button:has-text('Done')",
        "button:has-text('Apply')",
        "button:has-text('Update')",
    ]
    dismissed = False
    for selector in dismiss_selectors:
        locator = page.locator(selector).first
        try:
            locator.wait_for(state="visible", timeout=2000)
            locator.click()
            print(f"[INFO] Closed filter panel via {selector}")
            dismissed = True
            break
        except Exception:
            continue

    if not dismissed:
        try:
            page.keyboard.press("Escape")
            print("[INFO] Dismissed filter panel with Escape")
        except Exception:
            print("[WARN] Could not find explicit close control for filters")

    summary_selectors = [
        "text='Last 12 months'",
        "text='12 months'",
    ]
    summary_confirmed = False
    for attempt in range(6):
        for selector in summary_selectors:
            locator = page.locator(selector).first
            try:
                locator.wait_for(state="visible", timeout=200)
                summary_confirmed = True
                print("[INFO] Confirmed 12-month time range is active")
                break
            except Exception:
                continue
        if summary_confirmed:
            break
        page.wait_for_timeout(800)
    if not summary_confirmed:
        print("[WARN] Could not confirm 12-month time range; continuing anyway")

    page.wait_for_selector(CSV_DOWNLOAD_BUTTON)



def _download_csv(page, artist_id: str) -> Path:
    """Trigger CSV download and return path of saved file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suggested_name = f"spotify_audience_{artist_id}_{timestamp}.csv"
    dest_path = LANDING_DIR / suggested_name

    with page.expect_download() as dl_info:
        _click(page, CSV_DOWNLOAD_BUTTON, desc="CSV download button")
    download = dl_info.value
    download.save_as(dest_path)
    print(f"[SAVED] CSV -> {dest_path.relative_to(PROJECT_ROOT)}")
    return dest_path


# ---------------------------------------------------------------------------
# Song Metrics Extraction Functions
# ---------------------------------------------------------------------------
def _setup_song_metrics_capture(page) -> dict:
    """Set up network response interception for song metrics API calls.

    Returns a dictionary that will be populated with captured responses
    keyed by time period (1day, 7day, 28day, 1year, all).
    """
    captured_responses = {}

    def handle_response(response):
        url = response.url
        # Check if this is a songs API response with time-filter parameter
        if SONGS_API_PATTERN in url and SONGS_API_TIME_FILTER_PARAM in url:
            try:
                # Extract the time-filter value from URL
                match = re.search(r'time-filter=(\w+)', url)
                if match:
                    period = match.group(1)
                    # In sync Playwright, response.json() works directly
                    try:
                        json_data = response.json()
                        captured_responses[period] = {
                            "data": json_data,
                            "url": url,
                            "status": response.status,
                            "timestamp": datetime.now().isoformat()
                        }
                        print(f"[CAPTURED] Song metrics for period: {period}")
                    except Exception:
                        # Fallback to body() if json() fails
                        body = response.body()
                        captured_responses[period] = {
                            "data": body.decode('utf-8'),
                            "url": url,
                            "status": response.status,
                            "timestamp": datetime.now().isoformat(),
                            "raw_body": True
                        }
                        print(f"[CAPTURED] Song metrics (raw) for period: {period}")
            except Exception as e:
                print(f"[WARN] Failed to capture song metrics response: {e}")

    page.on("response", handle_response)
    return captured_responses


def _extract_song_metrics(page, artist_id: str, skip_songs: bool = False) -> list:
    """Extract song metrics for all time periods and save to landing zone.

    Args:
        page: Playwright page object
        artist_id: Spotify artist ID
        skip_songs: If True, skip song metrics extraction entirely

    Returns:
        List of paths to saved JSON files
    """
    if skip_songs:
        print("[INFO] Skipping song metrics extraction (--skip-songs flag)")
        return []

    saved_files = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Set up response capture before any navigation
    captured_responses = _setup_song_metrics_capture(page)

    # Navigate to songs page
    songs_url = SONGS_PAGE_URL_TEMPLATE.format(artist_id=artist_id)
    print(f"[INFO] Navigating to songs page: {songs_url}")
    page.goto(songs_url, wait_until="domcontentloaded")

    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        print("[WARN] Network did not fully settle, continuing...")

    # Open the filters menu
    filter_clicked = False
    for selector in SONGS_FILTER_BUTTON_SELECTORS:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=5000)
            locator.click(force=True)
            print(f"[INFO] Opened filters menu via: {selector}")
            filter_clicked = True
            time.sleep(1)  # Wait for menu to open
            break
        except Exception as e:
            print(f"[WARN] Filter selector failed: {selector} - {e}")
            continue

    if not filter_clicked:
        print("[ERROR] Could not open filters menu on songs page")
        return saved_files

    # Click each time period filter and wait for response
    for period_key, label_selector in TIME_PERIODS.items():
        try:
            print(f"[INFO] Selecting time period: {period_key}")

            # Click the radio label
            label = page.locator(label_selector).first
            label.wait_for(state="visible", timeout=5000)
            label.click(force=True)

            # Wait for network activity to settle (API response)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            time.sleep(1)  # Additional buffer for response capture

        except Exception as e:
            print(f"[WARN] Failed to select time period {period_key}: {e}")
            continue

    # Dismiss the filter menu
    try:
        page.keyboard.press("Escape")
        time.sleep(0.5)
    except Exception:
        pass

    # Save all captured responses
    for period, response_data in captured_responses.items():
        try:
            filename = f"spotify_songs_{artist_id}_{period}_{timestamp}.json"
            filepath = SONGS_LANDING_DIR / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)

            print(f"[SAVED] Song metrics -> {filepath.relative_to(PROJECT_ROOT)}")
            saved_files.append(filepath)

        except Exception as e:
            print(f"[ERROR] Failed to save song metrics for {period}: {e}")

    # Report any missing periods
    expected_periods = set(TIME_PERIODS.keys())
    captured_periods = set(captured_responses.keys())
    missing = expected_periods - captured_periods
    if missing:
        print(f"[WARN] Missing song metrics for periods: {missing}")

    return saved_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Spotify Audience extractor")
    parser.add_argument("--artists", nargs="*", default=DEFAULT_ARTIST_IDS, help="Space-separated list of Spotify Artist IDs")
    parser.add_argument("--skip-songs", action="store_true", help="Skip song metrics extraction (only extract audience data)")
    args = parser.parse_args()
    artist_ids: list[str] = args.artists
    skip_songs: bool = args.skip_songs

    print(f"[INFO] Starting Spotify Audience extractor for {len(artist_ids)} artist(s)...")
    
    # Set up session directory for persistent context
    SESSION_DIR = Path(PROJECT_ROOT) / "src" / ".playwright_spotify_session"
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        # Use persistent context like other extractors
        context = p.chromium.launch_persistent_context(
            str(SESSION_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            # Disable proxy to avoid "no healthy upstream" errors
            proxy=None,
            ignore_default_args=["--enable-automation"],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process"
            ]
        )
        
        # Load cookies into the persistent context
        load_cookies(context, "spotify")
        
        # Get the first page or create a new one
        page = context.pages[0] if context.pages else context.new_page()

        try:
            for aid in artist_ids:
                artist_url = f"https://artists.spotify.com/c/en/artist/{aid}"
                _login_if_needed(page, artist_url)
                _click(page, AUDIENCE_NAV_SELECTOR, desc="Audience nav link")
                page.wait_for_load_state("domcontentloaded")
                print(f"[INFO] Audience page loaded for {aid}.")
                _apply_12_month_filter(page)
                _download_csv(page, aid)

                # Extract song metrics across all time periods
                try:
                    song_files = _extract_song_metrics(page, aid, skip_songs=skip_songs)
                    if song_files:
                        print(f"[INFO] Saved {len(song_files)} song metrics files for {aid}")
                except Exception as e:
                    print(f"[WARN] Song metrics extraction failed for {aid}: {e}")
                    # Continue with next artist - don't fail the entire run

                # Navigate back to generic home between iterations to reset state
                page.goto("https://artists.spotify.com/home", wait_until="domcontentloaded")
        except KeyboardInterrupt:
            print("[INFO] Interrupted by user.")
        except Exception as exc:
            print(f"[ERROR] Extraction failed: {exc}")
            # Add more context for network errors
            if "no healthy upstream" in str(exc).lower():
                print("[ERROR] Network/proxy error detected. Possible causes:")
                print("  - Corporate proxy blocking the connection")
                print("  - Spotify blocking automated browsers")
                print("  - Network connectivity issues")
                print("  Try running with VPN disabled or on a different network")
            raise
        finally:
            try:
                context.close()
            except Exception:
                pass
            print("[INFO] Browser closed. Extraction complete.")


if __name__ == "__main__":
    main()
