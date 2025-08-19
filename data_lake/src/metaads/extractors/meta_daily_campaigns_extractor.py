# Enhanced Meta Ads Daily Campaign Performance Extractor
# Collects daily-level performance data for all ad campaigns with Meta Pixel events
# Uses direct Graph API requests (proven to work with our System User token)

# %%
import json
import os
import sqlite3
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

# %%
load_dotenv()
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID")
PROJECT_ROOT = os.getenv("PROJECT_ROOT")
assert ACCESS_TOKEN and AD_ACCOUNT_ID and PROJECT_ROOT, "Missing required .env variables: META_ACCESS_TOKEN, META_AD_ACCOUNT_ID, PROJECT_ROOT"

# API Configuration
API_VERSION = "v18.0"  # Using v18.0 which we tested successfully
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

PROJECT_ROOT = Path(PROJECT_ROOT)
LANDING_DIR = PROJECT_ROOT / "1_landing" / "metaads"
LANDING_DIR.mkdir(parents=True, exist_ok=True)

CACHE_DIR = PROJECT_ROOT / "src" / "metaads" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DB = CACHE_DIR / "campaign_activity.db"

# Field definitions for API requests
CAMPAIGN_FIELDS = "id,name,status,objective,effective_status,created_time,updated_time,daily_budget,lifetime_budget"

INSIGHT_FIELDS = "campaign_id,campaign_name,adset_id,adset_name,spend,impressions,clicks,cpc,cpm,ctr,reach,frequency,actions,date_start,date_stop"

# %%
class CampaignActivityTracker:
    """Track campaign activity status using SQLite cache"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for campaign activity tracking"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS campaign_activity (
                    campaign_id TEXT PRIMARY KEY,
                    last_active_date TEXT,
                    is_active INTEGER,
                    consecutive_inactive_days INTEGER DEFAULT 0,
                    updated_at TEXT
                )
            """)
            conn.commit()
    
    def get_active_campaigns(self) -> Set[str]:
        """Get list of campaigns that should be queried (not inactive for 7+ days)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT campaign_id FROM campaign_activity 
                WHERE is_active = 1 OR consecutive_inactive_days < 7
            """)
            return {row[0] for row in cursor.fetchall()}
    
    def update_campaign_activity(self, campaign_id: str, has_data: bool, date: str):
        """Update campaign activity status"""
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT consecutive_inactive_days FROM campaign_activity WHERE campaign_id = ?",
                (campaign_id,)
            ).fetchone()
            
            if has_data:
                # Campaign has data - reset inactive counter
                conn.execute("""
                    INSERT OR REPLACE INTO campaign_activity 
                    (campaign_id, last_active_date, is_active, consecutive_inactive_days, updated_at)
                    VALUES (?, ?, 1, 0, ?)
                """, (campaign_id, date, datetime.now().isoformat()))
            else:
                # Campaign has no data - increment inactive counter
                inactive_days = (existing[0] if existing else 0) + 1
                is_active = 1 if inactive_days < 7 else 0
                
                conn.execute("""
                    INSERT OR REPLACE INTO campaign_activity 
                    (campaign_id, last_active_date, is_active, consecutive_inactive_days, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (campaign_id, date, is_active, inactive_days, datetime.now().isoformat()))
            
            conn.commit()

# %%
def make_api_request(url: str, params: Dict = None) -> Dict:
    """
    Make a GET request to the Meta Graph API with error handling.
    Returns the JSON response or raises an exception.
    """
    if params is None:
        params = {}
    
    # Always include access token
    params['access_token'] = ACCESS_TOKEN
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API request failed: {e}")
        if response.text:
            print(f"[ERROR] Response: {response.text}")
        raise

def fetch_all_pages(url: str, params: Dict = None) -> List[Dict]:
    """
    Fetch all pages of results from a paginated API endpoint.
    Handles pagination automatically.
    """
    if params is None:
        params = {}
    
    all_results = []
    
    while url:
        data = make_api_request(url, params)
        
        # Add results from this page
        if 'data' in data:
            all_results.extend(data['data'])
        
        # Check for next page
        if 'paging' in data and 'next' in data['paging']:
            url = data['paging']['next']
            params = {}  # Next URL already has parameters
        else:
            url = None
    
    return all_results

# %%
def retry_api_call(func, max_retries: int = 3, delay: float = 2.0):
    """Retry API calls with exponential backoff for rate limits"""
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.RequestException as e:
            # Check if it's a rate limit error (code 17 or 80004)
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    error_code = error_data.get('error', {}).get('code')
                    if error_code in [17, 80004]:  # Rate limit errors
                        wait_time = delay * (2 ** attempt)
                        print(f"[INFO] Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        if attempt == max_retries - 1:
                            raise
                        continue
                except:
                    pass
            
            print(f"[ERROR] API error: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(delay)
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(delay)

# %%
def extract_pixel_events(actions: List[Dict]) -> Dict[str, int]:
    """Extract and aggregate Meta Pixel events from actions data"""
    pixel_events = {}
    
    if not actions:
        return pixel_events
    
    for action in actions:
        action_type = action.get('action_type', '')
        value = int(float(action.get('value', 0)))
        
        # Map common action types to standardized event names
        event_mapping = {
            'offsite_conversion.fb_pixel_view_content': 'ViewContent',
            'offsite_conversion.fb_pixel_add_to_cart': 'AddToCart', 
            'offsite_conversion.fb_pixel_purchase': 'Purchase',
            'offsite_conversion.fb_pixel_initiate_checkout': 'InitiateCheckout',
            'offsite_conversion.fb_pixel_add_payment_info': 'AddPaymentInfo',
            'offsite_conversion.fb_pixel_lead': 'Lead',
            'offsite_conversion.fb_pixel_complete_registration': 'CompleteRegistration',
            'link_click': 'LinkClick',
            'post_engagement': 'PostEngagement',
            'onsite_conversion.messaging_conversation_started_7d': 'MessagingStarted'
        }
        
        # Use mapped name or original action_type
        event_name = event_mapping.get(action_type, action_type)
        
        # Aggregate events by type
        if event_name in pixel_events:
            pixel_events[event_name] += value
        else:
            pixel_events[event_name] = value
    
    return pixel_events

# %%
def fetch_campaign_daily_insights(campaign_id: str, date_start: str, date_end: str) -> List[Dict]:
    """Fetch daily insights for a specific campaign using direct API calls"""
    
    def _fetch():
        url = f"{BASE_URL}/{campaign_id}/insights"
        
        # Format time_range as JSON string (required by API)
        time_range = json.dumps({
            'since': date_start,
            'until': date_end
        })
        
        params = {
            'fields': INSIGHT_FIELDS,
            'time_range': time_range,
            'time_increment': 1,  # Daily breakdown
            'level': 'campaign',
            'limit': 500
        }
        
        return fetch_all_pages(url, params)
    
    return retry_api_call(_fetch)

# %%
def get_all_campaigns() -> List[Dict]:
    """Get all campaigns from the ad account using direct API calls"""
    
    def _fetch():
        url = f"{BASE_URL}/{AD_ACCOUNT_ID}/campaigns"
        params = {
            'fields': CAMPAIGN_FIELDS,
            'limit': 1000
        }
        return fetch_all_pages(url, params)
    
    return retry_api_call(_fetch)

# %%
def validate_api_connection() -> bool:
    """Validate API token and account access before running extraction"""
    print("[INFO] Validating API connection...")
    
    try:
        # Test token validity
        url = f"{BASE_URL}/debug_token"
        params = {
            'input_token': ACCESS_TOKEN,
            'access_token': ACCESS_TOKEN
        }
        response = make_api_request(url, params)
        
        if 'data' in response and response['data'].get('is_valid'):
            print("[SUCCESS] Token is valid")
        else:
            print("[ERROR] Token is invalid or expired")
            return False
        
        # Test account access
        url = f"{BASE_URL}/{AD_ACCOUNT_ID}"
        params = {'fields': 'name,currency,account_status'}
        response = make_api_request(url, params)
        
        if 'name' in response:
            print(f"[SUCCESS] Account accessed: {response['name']}")
            return True
        else:
            print("[ERROR] Cannot access ad account")
            return False
            
    except Exception as e:
        print(f"[ERROR] Validation failed: {e}")
        return False

# %%
def main():
    """Main extraction logic"""
    print("=" * 80)
    print("META ADS DAILY CAMPAIGN EXTRACTOR")
    print("=" * 80)
    
    # Validate API connection first
    if not validate_api_connection():
        print("[ERROR] API validation failed. Please check your credentials.")
        return
    
    print(f"\n[INFO] Starting Meta Ads daily campaign extraction...")
    
    # Initialize activity tracker
    tracker = CampaignActivityTracker(CACHE_DB)
    
    # Date range for extraction (last 30 days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    date_start = start_date.strftime('%Y-%m-%d')
    date_end = end_date.strftime('%Y-%m-%d')
    
    print(f"[INFO] Extracting data from {date_start} to {date_end}")
    
    # Get all campaigns
    print("[INFO] Fetching campaigns...")
    campaigns = get_all_campaigns()
    print(f"[INFO] Found {len(campaigns)} campaigns")
    
    # Get active campaigns from cache
    active_campaign_ids = tracker.get_active_campaigns()
    
    # If cache is empty, include all campaigns for first run
    if not active_campaign_ids:
        active_campaign_ids = {c['id'] for c in campaigns}
        print(f"[INFO] First run - including all {len(active_campaign_ids)} campaigns")
    else:
        print(f"[INFO] Including {len(active_campaign_ids)} active campaigns from cache")
    
    # Collect daily insights
    all_daily_data = []
    campaigns_with_data = set()
    
    for campaign in tqdm(campaigns, desc="Processing campaigns"):
        campaign_id = campaign['id']
        campaign_name = campaign['name']
        
        # Skip if campaign is marked as inactive (7+ days no data)
        if campaign_id not in active_campaign_ids:
            print(f"[SKIP] Campaign {campaign_name} inactive for 7+ days")
            continue
        
        try:
            # Fetch daily insights
            daily_insights = fetch_campaign_daily_insights(campaign_id, date_start, date_end)
            
            if daily_insights:
                campaigns_with_data.add(campaign_id)
                
                for insight in daily_insights:
                    # Extract pixel events
                    actions = insight.get('actions', [])
                    pixel_events = extract_pixel_events(actions)
                    
                    # Determine if campaign is currently active
                    campaign_status = campaign.get('status', 'UNKNOWN')
                    effective_status = campaign.get('effective_status', 'UNKNOWN')
                    is_active = campaign_status == 'ACTIVE' and effective_status in ['ACTIVE', 'CAMPAIGN_PAUSED']
                    
                    # Build daily record with additional metrics
                    daily_record = {
                        'date': insight.get('date_start'),
                        'campaign_id': campaign_id,
                        'campaign_name': campaign_name,
                        'campaign_objective': campaign.get('objective', ''),
                        'campaign_status': campaign_status,
                        'adset_id': insight.get('adset_id', ''),
                        'adset_name': insight.get('adset_name', ''),
                        'spend_usd': float(insight.get('spend', 0)) if insight.get('spend') else 0.0,
                        'impressions': int(insight.get('impressions', 0)) if insight.get('impressions') else 0,
                        'clicks': int(insight.get('clicks', 0)) if insight.get('clicks') else 0,
                        'reach': float(insight.get('reach', 0)) if insight.get('reach') else 0.0,
                        'frequency': float(insight.get('frequency', 0)) if insight.get('frequency') else 0.0,
                        'cpc': float(insight.get('cpc', 0)) if insight.get('cpc') else 0.0,
                        'cpm': float(insight.get('cpm', 0)) if insight.get('cpm') else 0.0,
                        'ctr': float(insight.get('ctr', 0)) if insight.get('ctr') else 0.0,
                        'meta_pixel_events': json.dumps(pixel_events) if pixel_events else "{}",
                        'is_active': is_active
                    }
                    
                    all_daily_data.append(daily_record)
            
            # Update activity tracker
            tracker.update_campaign_activity(
                campaign_id, 
                bool(daily_insights), 
                date_end
            )
            
        except Exception as e:
            print(f"[ERROR] Failed to process campaign {campaign_name}: {e}")
            continue
    
    # Save results
    if all_daily_data:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = LANDING_DIR / f"metaads_campaign_daily_{timestamp}.csv"
        
        df = pd.DataFrame(all_daily_data)
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        print(f"[SUCCESS] Saved {len(all_daily_data)} daily records to {output_file}")
        print(f"[INFO] Campaigns with data: {len(campaigns_with_data)}")
        print(f"[INFO] Date range: {df['date'].min()} to {df['date'].max()}")
        
        # Show sample of pixel events
        sample_events = df[df['meta_pixel_events'] != '{}']['meta_pixel_events'].head(3)
        if not sample_events.empty:
            print("[INFO] Sample pixel events:")
            for events in sample_events:
                print(f"  {events}")
    else:
        print("[WARNING] No data collected - all campaigns may be inactive")

# %%
if __name__ == "__main__":
    main()