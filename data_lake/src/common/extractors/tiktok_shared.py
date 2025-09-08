import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from playwright.sync_api import Playwright


VALID_SAMESITE = {"Strict", "Lax", "None"}

# API patterns that may contain follower data
FOLLOWER_API_PATTERNS = [
    'api/user/detail',
    'api/creator', 
    'api/analytics',
    'tiktokstudio/api',
    'aweme/v1/user'
]


def _import_cookies(context, cookies_path: str, marker_path: str) -> None:
    """Import cookies once per user data directory."""
    if not os.path.exists(cookies_path) or os.path.exists(marker_path):
        return
    with open(cookies_path, "r") as f:
        cookies = json.load(f)
    for cookie in cookies:
        if "sameSite" in cookie and cookie["sameSite"] not in VALID_SAMESITE:
            cookie["sameSite"] = "Lax"
    context.add_cookies(cookies)
    with open(marker_path, "w") as marker:
        marker.write("imported")


def _extract_follower_from_json(json_data: Dict) -> Optional[int]:
    """Extract follower count from API JSON response."""
    def search_for_follower_count(obj, path=""):
        """Recursively search for follower count in nested JSON."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Direct follower field matches
                key_lower = key.lower()
                if any(term in key_lower for term in ['follower', 'fan']):
                    if isinstance(value, (int, float)) and value > 0:
                        return int(value)
                
                # Common TikTok API patterns
                if key in ['followerCount', 'fans', 'follower_count']:
                    if isinstance(value, (int, float)) and value > 0:
                        return int(value)
                
                # Recurse into nested objects
                if isinstance(value, (dict, list)):
                    result = search_for_follower_count(value, current_path)
                    if result is not None:
                        return result
        
        elif isinstance(obj, list):
            for item in obj:
                result = search_for_follower_count(item, path)
                if result is not None:
                    return result
        
        return None
    
    return search_for_follower_count(json_data)


def _capture_follower_data(page, artist_name: str, output_dir: Path) -> Optional[Dict]:
    """Capture follower count via network interception."""
    follower_data = {}
    captured_responses = []
    
    def handle_response(response):
        """Handle network responses to find follower data."""
        url = response.url
        
        # Check if this response might contain follower data
        for pattern in FOLLOWER_API_PATTERNS:
            if pattern in url:
                try:
                    json_data = response.json()
                    follower_count = _extract_follower_from_json(json_data)
                    
                    if follower_count:
                        print(f"[FOLLOWER] Found count {follower_count} in {pattern} API")
                        follower_data['count'] = follower_count
                        follower_data['source_url'] = url
                        follower_data['timestamp'] = datetime.now().isoformat()
                        follower_data['artist'] = artist_name
                    
                    # Store response for debugging
                    captured_responses.append({
                        'url': url,
                        'pattern': pattern,
                        'follower_count': follower_count,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    print(f"[DEBUG] Failed to parse {pattern} response: {e}")
                break
    
    # Set up response interception
    page.on('response', handle_response)
    
    # Navigate to profile to trigger API calls
    profile_url = f"https://www.tiktok.com/@{artist_name}"
    try:
        print(f"[FOLLOWER] Navigating to {profile_url} for follower data...")
        page.goto(profile_url)
        page.wait_for_load_state('networkidle', timeout=10000)
        
        # Wait for API calls to complete
        time.sleep(3)
        
        # Try scrolling to trigger more API calls
        page.evaluate("window.scrollBy(0, 300)")
        time.sleep(2)
        
    except Exception as e:
        print(f"[WARN] Profile navigation failed: {e}")
    
    # Save captured data for debugging
    if captured_responses:
        debug_file = output_dir / f"follower_debug_{artist_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(debug_file, 'w') as f:
            json.dump(captured_responses, f, indent=2)
        print(f"[DEBUG] Saved follower debug data to {debug_file.name}")
    
    # Validate follower count against page display
    if follower_data.get('count'):
        try:
            # Look for follower count displayed on page
            follower_selectors = [
                '[data-e2e="followers-count"]',
                'strong:has-text("Followers")',
                '.follower-count',
                '[class*="follower"]'
            ]
            
            for selector in follower_selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=2000):
                        page_text = element.inner_text()
                        print(f"[VALIDATION] Page shows follower text: {page_text}")
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"[DEBUG] Page validation failed: {e}")
    
    return follower_data if follower_data.get('count') else None


def _wait_for_analytics_page(context, analytics_prefix: str) -> Optional["Page"]:
    tracked_pages = set(context.pages)

    def on_new_page(page):
        tracked_pages.add(page)

    context.on("page", on_new_page)
    found_page = None
    while True:
        tracked_pages = {p for p in tracked_pages if not p.is_closed()}
        if not tracked_pages:
            return None
        for p in tracked_pages:
            if p.url.startswith(analytics_prefix):
                found_page = p
                break
        if found_page:
            break
        time.sleep(1)
    return found_page


def run_extraction(
    playwright: Playwright,
    user_data_dir: str,
    analytics_url: str,
    output_dir: Path,
    cookies_path: Optional[str] = None,
    marker_path: Optional[str] = None,
    capture_followers: bool = True,
    artist_name: Optional[str] = None,
    date_range_days: int = 365,  # NEW: Specify desired date range
) -> Dict:
    """Run the shared TikTok analytics extraction routine with follower capture.
    
    Args:
        date_range_days: Number of days to extract (7, 28, 60, 180, or 365)
    """
    os.makedirs(user_data_dir, exist_ok=True)
    context = playwright.chromium.launch_persistent_context(
        user_data_dir,
        headless=False,
        viewport={"width": 1440, "height": 900},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        args=["--disable-blink-features=AutomationControlled"],
    )

    page = context.pages[0] if context.pages else context.new_page()
    
    # Initialize result dictionary
    extraction_result = {
        'csv_downloaded': False,
        'csv_path': None,
        'follower_data': None,
        'timestamp': datetime.now().isoformat()
    }

    if cookies_path and marker_path:
        _import_cookies(context, cookies_path, marker_path)

    # Step 1: Capture follower data if requested
    follower_data = None
    if capture_followers and artist_name:
        print(f"[INFO] Capturing follower data for {artist_name}...")
        follower_data = _capture_follower_data(page, artist_name, output_dir)
        extraction_result['follower_data'] = follower_data
        
        if follower_data:
            print(f"[SUCCESS] Captured follower count: {follower_data['count']}")
            # Save follower data to JSON file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            follower_file = output_dir / f"{artist_name}_followers_{timestamp}.json"
            with open(follower_file, 'w') as f:
                json.dump(follower_data, f, indent=2)
            print(f"[FOLLOWER] Saved to {follower_file.name}")
        else:
            print(f"[WARN] Could not capture follower data for {artist_name}")

    # Step 2: Navigate to analytics for CSV download
    page.goto(analytics_url)
    
    # Check if we need to authenticate
    analytics_prefix = analytics_url.split("/analytics")[0] + "/analytics"
    
    # Wait for either analytics page or login page
    max_wait_time = 300  # 5 minutes for manual authentication
    start_time = time.time()
    authenticated = False
    
    print("[INFO] Checking authentication status...")
    
    while (time.time() - start_time) < max_wait_time:
        # Check if we're on the analytics page
        if page.url.startswith(analytics_prefix):
            authenticated = True
            print("[INFO] Successfully authenticated and on analytics page")
            break
        
        # Check if we're on a login page
        if "login" in page.url.lower() or "signin" in page.url.lower():
            print("[ACTION REQUIRED] Please log in to TikTok manually in the browser window")
            print(f"[INFO] Waiting up to {int(max_wait_time - (time.time() - start_time))} more seconds...")
        
        time.sleep(2)
    
    if not authenticated:
        print("[ERROR] Authentication timeout - please try again")
        print("[INFO] Browser remains open for manual intervention")
        input("Press Enter when you have manually authenticated...")
        
        # Check one more time after manual intervention
        if page.url.startswith(analytics_prefix):
            authenticated = True
            print("[INFO] Authentication successful after manual intervention")
    
    if not authenticated:
        print("[ERROR] Could not authenticate to TikTok analytics")
        return extraction_result
    
    # Now wait for the analytics page to fully load
    page = _wait_for_analytics_page(context, analytics_prefix)
    if page is None:
        print("Analytics page not found after authentication.")
        return extraction_result

    # IMPORTANT: After login, the page needs more time to stabilize
    print("[INFO] Waiting for analytics page to fully load after authentication...")
    time.sleep(5)  # Initial wait
    
    # Wait for network to be idle - important after fresh login
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
        print("[INFO] Page network activity settled")
    except:
        print("[WARN] Network didn't fully settle, continuing anyway")
    
    # Additional wait to ensure all JavaScript has executed
    time.sleep(3)
    import random

    # Try multiple strategies to click the date range button
    date_clicked = False
    
    # First, take a screenshot for debugging
    debug_screenshot = output_dir / f"tiktok_analytics_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    try:
        page.screenshot(path=str(debug_screenshot))
        print(f"[DEBUG] Saved screenshot to {debug_screenshot.name}")
    except Exception as e:
        print(f"[DEBUG] Could not save screenshot: {e}")
    
    # Strategy 1: Look for date selector button with "Last X days" text
    for attempt in range(3):
        try:
            # Wait a bit before each attempt to let the page stabilize
            if attempt > 0:
                time.sleep(2)
            
            # Try the actual TikTok selector structure - look for ANY date button
            date_button_selectors = [
                # More generic selectors to find ANY date button
                "div.Button__content:has-text('days')",
                "div.Button__content:has-text('Last')",
                "*:has-text('Last'):has-text('days')",
                "button:has-text('days')",
                "[role='button']:has-text('days')",
                # Also try without "Last" in case it shows current selection
                "div:has-text('365 days')",
                "div:has-text('180 days')",
                "div:has-text('60 days')",
                "div:has-text('28 days')",
                "div:has-text('7 days')",
            ]
            
            for selector in date_button_selectors:
                try:
                    elements = page.locator(selector).all()
                    if elements:
                        # Wait for the element to be stable before clicking
                        elements[0].wait_for(state="visible", timeout=2000)
                        elements[0].click()
                        print(f"[INFO] Clicked date selector using: {selector}")
                        date_clicked = True
                        break
                except:
                    pass
            
            if date_clicked:
                break
                
        except Exception as e:
            print(f"[DEBUG] Date selector attempt {attempt + 1} failed: {e}")
            time.sleep(2)
    
    # Strategy 2: Look for any date range button with more selectors
    if not date_clicked:
        for attempt in range(3):
            try:
                # Look for buttons containing "days" or common date patterns
                selectors = [
                    "button:has-text('7 days')",
                    "button:has-text('days')", 
                    "[role='button']:has-text('7')",
                    ".date-selector button",
                    "[data-testid*='date'] button",
                    # New selectors based on common TikTok patterns
                    "button:has-text('Last')",
                    "span:has-text('Last 7 days')",
                    "div[class*='DatePicker'] button",
                    "div[class*='date-picker'] button",
                    "div[class*='datePicker'] button",
                    # Try clicking on parent elements
                    "div:has-text('Last 7 days'):visible",
                    "*:has-text('Last 7 days'):visible"
                ]
                
                for selector in selectors:
                    try:
                        elements = page.locator(selector).all()
                        if elements:
                            print(f"[DEBUG] Found {len(elements)} elements matching: {selector}")
                            elements[0].click()
                            print(f"[INFO] Clicked date button using selector: {selector}")
                            date_clicked = True
                            break
                    except:
                        pass
                
                if date_clicked:
                    break
                    
            except Exception as e:
                print(f"[DEBUG] Alternative date selector attempt {attempt + 1} failed: {e}")
                time.sleep(2)
    
    # Strategy 3: Try to find any clickable element with date-related text
    if not date_clicked:
        try:
            # Log all visible text on page for debugging
            print("[DEBUG] Searching for date-related elements on page...")
            date_patterns = ["days", "Days", "date", "Date", "period", "Period", "range", "Range"]
            for pattern in date_patterns:
                try:
                    elements = page.locator(f"*:has-text('{pattern}'):visible").all()
                    if elements:
                        print(f"[DEBUG] Found {len(elements)} elements containing '{pattern}'")
                        for i, elem in enumerate(elements[:3]):  # Check first 3 matches
                            try:
                                text = elem.inner_text()
                                print(f"[DEBUG]   Element {i+1}: {text[:50]}...")
                            except:
                                pass
                except:
                    pass
            
            # Try a more general approach - look for the date display element
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2)
            
            # Click anywhere on the date display area
            date_display_selectors = [
                "div:has-text('Last'):has-text('days')",
                "*[class*='date']:has-text('days')",
                "*[class*='Date']:has-text('days')"
            ]
            
            for selector in date_display_selectors:
                try:
                    elem = page.locator(selector).first
                    if elem.is_visible():
                        elem.click()
                        print(f"[INFO] Clicked date display area using: {selector}")
                        date_clicked = True
                        break
                except:
                    pass
                    
        except Exception as e:
            print(f"[DEBUG] Strategy 3 failed: {e}")
    
    if not date_clicked:
        print(f"[WARN] Could not find date selector button. Will try direct {date_range_days} days selection...")
        # NEW: Try to directly select desired days even without clicking the date button first
        # This handles cases where the dropdown might already be open or accessible
        try:
            time.sleep(2)
            # Try clicking anywhere on the page to potentially trigger dropdowns
            page.mouse.click(500, 300)  # Click in a neutral area
            time.sleep(1)
        except:
            pass
    
    # Try to select desired date range regardless of whether we clicked the date selector
    # This is more robust and handles various UI states
    if True:  # Always attempt date range selection
        # Wait for dropdown and select desired days
        time.sleep(2)
        
        # Try to find and click desired days option
        days_selected = False
        for attempt in range(3):
            try:
                # First wait a bit for dropdown to appear
                page.wait_for_timeout(1000)
                
                # Build selectors based on requested date range and TikTok's HTML structure
                date_range_str = str(date_range_days)
                
                # TikTok may not have exactly 365 days - try closest available options
                if date_range_days == 365:
                    # Try 365 first, then fall back to 180 days (max TikTok typically offers)
                    date_options = ["365", "180", "60", "28", "7"]
                else:
                    date_options = [str(date_range_days)]
                
                for days_option in date_options:
                    date_selectors = [
                        f"span.TUXText:has-text('Last {days_option} days')",
                        f"span[data-tt*='TUXText']:has-text('Last {days_option} days')",
                        f"text=Last {days_option} days",
                        f":text('Last {days_option} days')",
                        f"*:has-text('Last {days_option} days'):visible",
                        # Also try without "Last" prefix
                        f"span.TUXText:has-text('{days_option} days')",
                        f"text={days_option} days",
                    ]
                    
                    # Try multiple methods to find and click the desired date range
                    for selector in date_selectors:
                        if page.locator(selector).count() > 0:
                            page.locator(selector).first.click()
                            print(f"[INFO] Selected '{days_option} days' (requested {date_range_str}) using: {selector}")
                            days_selected = True
                            break
                    
                    if days_selected:
                        break
                
                if days_selected:
                    break
            except Exception as e:
                print(f"[DEBUG] {date_range_days} days selection attempt {attempt + 1} failed: {e}")
                # Try alternative selectors
                try:
                    alt_selectors = [
                        f"span.TUXText:has-text('Last {date_range_days} days')",
                        f"span[data-tt*='TUXText']:has-text('Last {date_range_days} days')",
                        f"text={date_range_days} days",
                        f"text=Last {date_range_days} days",
                        f"button:has-text('{date_range_days}')",
                        f"[role='option']:has-text('{date_range_days}')",
                        f"div:has-text('{date_range_days} days')",
                        f"span:has-text('{date_range_days}')",
                        f"*:has-text('Last {date_range_days} days'):visible",
                        f"li:has-text('{date_range_days}')",
                        f"[data-value='{date_range_days}']",
                        f"option:has-text('{date_range_days}')"
                    ]
                    for selector in alt_selectors:
                        if page.locator(selector).first.is_visible():
                            page.locator(selector).first.click()
                            print(f"[INFO] Selected {date_range_days} days using: {selector}")
                            days_selected = True
                            break
                    if days_selected:
                        break
                except Exception:
                    pass
                time.sleep(2)
        
        if not days_selected:
            print(f"[WARN] Could not select {date_range_days} days using dropdown method")
            print(f"[INFO] Attempting alternative methods to select {date_range_days} days...")
            
            # NEW: Try keyboard navigation as a last resort
            try:
                # Press Tab to navigate through elements
                for _ in range(10):
                    page.keyboard.press("Tab")
                    time.sleep(0.2)
                    # Check if we've focused on something with the desired days
                    try:
                        focused = page.evaluate("document.activeElement.innerText")
                        if str(date_range_days) in str(focused):
                            page.keyboard.press("Enter")
                            print(f"[INFO] Selected {date_range_days} days using keyboard navigation")
                            days_selected = True
                            break
                    except:
                        pass
            except Exception as e:
                print(f"[DEBUG] Keyboard navigation failed: {e}")
            
            if not days_selected:
                print(f"[ERROR] Failed to select {date_range_days} days after all attempts")
                print("[WARN] Data will be limited to default range (usually 7 days)")
    
    # Wait for the data to reload after date range change
    print("[INFO] Waiting for data to reload with new date range...")
    time.sleep(5)  # Give TikTok time to load the data
    
    # Debug: Check what date range is actually selected
    try:
        # Look for the current date range display
        current_range_selectors = [
            "div.Button__content:has-text('days')",
            "*:has-text('Last'):has-text('days')",
        ]
        for selector in current_range_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible():
                    current_text = element.inner_text()
                    print(f"[DEBUG] Current date range shown: {current_text}")
                    break
            except:
                pass
    except:
        pass

    # Click the Download data button - try multiple selectors
    download_clicked = False
    download_selectors = [
        "div.TUXButton-content:has(div.TUXButton-label:text('Download data'))",
        "div.TUXButton-label:text('Download data')",
        "button:has-text('Download data')",
        "*:has(svg):has-text('Download data')",
        "div:has-text('Download data'):has(svg)"
    ]
    
    for selector in download_selectors:
        try:
            if page.locator(selector).count() > 0:
                page.locator(selector).first.click()
                print(f"[INFO] Clicked 'Download data' button using: {selector}")
                download_clicked = True
                break
        except:
            pass
    
    if not download_clicked:
        print("[ERROR] Could not find 'Download data' button")
        # Try fallback method
        page.get_by_role("button", name="Download data").click()
    # Wait for download modal to appear
    time.sleep(2)
    
    # Select CSV radio button - try multiple selectors
    csv_selected = False
    csv_selectors = [
        'input[type="radio"][name="CSV"]',
        'input[type="radio"][value="CSV"]',
        'input.TUXRadioStandalone-input[name="CSV"]',
        'input[data-tt*="TUXRadio"][value="CSV"]',
        '//input[@type="radio" and @name="CSV"]'
    ]
    
    for selector in csv_selectors:
        try:
            if selector.startswith('//'):
                page.locator(f'xpath={selector}').check()
            else:
                page.locator(selector).check()
            print(f"[INFO] Selected CSV format using: {selector}")
            csv_selected = True
            break
        except:
            pass
    
    if not csv_selected:
        print("[WARN] Could not select CSV radio button, trying to proceed anyway")
    # Click the final Download button
    time.sleep(1)
    
    with page.expect_download(timeout=30000) as download_info:
        # Try multiple selectors for the Download button
        download_btn_selectors = [
            'div.TUXButton-label:text("Download")',
            'button:has(div.TUXButton-label:text("Download"))',
            'button:has-text("Download")',
            '*[class*="TUXButton"]:has-text("Download")',
            '//div[@class="TUXButton-label" and text()="Download"]/..',
        ]
        
        download_btn_clicked = False
        for selector in download_btn_selectors:
            try:
                if selector.startswith('//'):
                    elements = page.locator(f'xpath={selector}').all()
                else:
                    elements = page.locator(selector).all()
                
                # Click the last Download button (not the "Download data" one)
                if len(elements) > 0:
                    # If there are multiple, take the last one
                    elements[-1].click()
                    print(f"[INFO] Clicked final Download button using: {selector}")
                    download_btn_clicked = True
                    break
            except:
                pass
        
        if not download_btn_clicked:
            print("[ERROR] Could not find final Download button, trying fallback")
            page.locator('button:has-text("Download")').last.click()
    download = download_info.value
    save_path = output_dir / download.suggested_filename
    download.save_as(save_path)
    
    # Update extraction result
    extraction_result['csv_downloaded'] = True
    extraction_result['csv_path'] = str(save_path)

    if not page.is_closed():
        page.close()
    context.close()
    
    print("Extraction complete. Browser closed automatically after data capture.")
    print(f"[RESULT] CSV: {extraction_result['csv_downloaded']}, Followers: {extraction_result['follower_data'] is not None}")
    
    return extraction_result
