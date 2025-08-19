#!/usr/bin/env python3
"""
Meta Ads API Data Fetcher - Production Ready
Fetches complete ads data and recreates the CSV structure
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import Facebook Business SDK
try:
    from facebook_business.api import FacebookAdsApi
    from facebook_business.adobjects.adaccount import AdAccount
    from facebook_business.adobjects.adsinsights import AdsInsights
    from facebook_business.adobjects.ad import Ad
except ImportError:
    print("Installing Facebook Business SDK...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "facebook-business"])
    from facebook_business.api import FacebookAdsApi
    from facebook_business.adobjects.adaccount import AdAccount
    from facebook_business.adobjects.adsinsights import AdsInsights
    from facebook_business.adobjects.ad import Ad

class MetaAdsAPIFetcher:
    def __init__(self):
        self.access_token = None
        self.ad_account_id = None
        self.account = None
        
    def load_credentials(self):
        """Load credentials from .env file"""
        env_path = Path(__file__).parent.parent / '.env'
        
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    if 'META_ACCESS_TOKEN' in line and '=' in line:
                        self.access_token = line.split('=', 1)[1].strip()
                    elif 'META_AD_ACCOUNT_ID' in line and '=' in line:
                        self.ad_account_id = line.split('=', 1)[1].strip()
        
        return self.access_token and self.ad_account_id
    
    def initialize_api(self):
        """Initialize Facebook Ads API"""
        try:
            # Initialize with minimal parameters for user access token
            FacebookAdsApi.init(access_token=self.access_token)
            
            # Test connection
            self.account = AdAccount(self.ad_account_id)
            account_info = self.account.api_get(fields=['name', 'currency', 'account_status'])
            
            print(f"✅ Connected to: {account_info.get('name')}")
            print(f"   Account ID: {self.ad_account_id}")
            print(f"   Currency: {account_info.get('currency')}")
            print(f"   Status: {account_info.get('account_status')}")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            
            if 'OAuthException' in error_msg:
                print("❌ Token expired or invalid")
                self.print_token_instructions()
            elif 'Invalid parameter' in error_msg:
                print("❌ Invalid account ID or permissions")
            else:
                print(f"❌ API Error: {error_msg}")
            
            return False
    
    def fetch_all_ads_insights(self, start_date='2022-01-01', end_date=None):
        """Fetch all ads insights matching the CSV structure"""
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n📊 Fetching ads data from {start_date} to {end_date}...")
        
        all_ads = []
        
        # Define fields to fetch
        fields = [
            'ad_id',
            'ad_name',
            'adset_id',
            'adset_name',
            'campaign_id', 
            'campaign_name',
            'spend',
            'impressions',
            'reach',
            'clicks',
            'actions',
            'cost_per_action_type',
            'quality_ranking',
            'engagement_rate_ranking',
            'conversion_rate_ranking',
            'frequency',
            'cpm',
            'cpc',
            'ctr',
        ]
        
        # Parameters
        params = {
            'level': 'ad',
            'time_range': {
                'since': start_date,
                'until': end_date
            },
            'time_increment': 'all_days',  # Get total for period
            'fields': fields,
            'limit': 1000,
            'filtering': [
                {
                    'field': 'spend',
                    'operator': 'GREATER_THAN',
                    'value': 0
                }
            ]
        }
        
        try:
            # Fetch insights
            insights_cursor = self.account.get_insights(params=params)
            
            # Process each ad
            for insight in insights_cursor:
                ad_data = self.process_insight(insight, start_date, end_date)
                all_ads.append(ad_data)
                
                # Show progress
                if len(all_ads) % 10 == 0:
                    print(f"  Processed {len(all_ads)} ads...")
            
            print(f"✅ Fetched {len(all_ads)} ads with spend > 0")
            
        except Exception as e:
            print(f"❌ Error fetching insights: {str(e)}")
        
        return all_ads
    
    def process_insight(self, insight, start_date, end_date):
        """Process a single insight to match CSV structure"""
        
        # Extract conversions from actions
        results = 0
        cost_per_result = 0
        
        actions = insight.get('actions', [])
        for action in actions:
            if 'offsite_conversion' in action.get('action_type', ''):
                results += float(action.get('value', 0))
        
        cost_per_actions = insight.get('cost_per_action_type', [])
        for cpa in cost_per_actions:
            if 'offsite_conversion' in cpa.get('action_type', ''):
                cost_per_result = float(cpa.get('value', 0))
        
        # Build row matching CSV structure
        return {
            'Reporting starts': start_date,
            'Reporting ends': end_date,
            'Ad name': insight.get('ad_name', ''),
            'Ad delivery': 'active',  # All fetched ads have spend
            'Ad Set Name': insight.get('adset_name', ''),
            'Bid': 0,
            'Bid type': 'ABSOLUTE_OCPM',
            'Ad set budget': 5,
            'Ad set budget type': 'Daily',
            'Last significant edit': 0,
            'Attribution setting': '7-day click, 1-day view, or 1-day engaged-view',
            'Results': int(results),
            'Result indicator': 'actions:offsite_conversion.fb_pixel_view_content',
            'Reach': int(insight.get('reach', 0)),
            'Impressions': int(insight.get('impressions', 0)),
            'Cost per results': cost_per_result,
            'Quality ranking': insight.get('quality_ranking', '-'),
            'Engagement rate ranking': insight.get('engagement_rate_ranking', '-'),
            'Conversion rate ranking': insight.get('conversion_rate_ranking', '-'),
            'Amount spent (USD)': float(insight.get('spend', 0)),
            'Ends': 'Ongoing'
        }
    
    def save_to_csv(self, ads_data):
        """Save ads data to CSV matching original format"""
        if not ads_data:
            print("❌ No data to save")
            return None
        
        # Create DataFrame
        df = pd.DataFrame(ads_data)
        
        # Save to landing and curated folders
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Landing folder (raw data)
        landing_path = Path(__file__).parent.parent / '1_landing'
        landing_file = landing_path / f'meta_ads_api_{timestamp}.csv'
        df.to_csv(landing_file, index=False)
        print(f"\n✅ Raw data saved to landing: {landing_file.name}")
        
        # Curated folder (processed data)
        curated_path = Path(__file__).parent.parent / '4_curated'
        curated_file = curated_path / f'meta_ads_complete_{timestamp}.csv'
        df.to_csv(curated_file, index=False)
        print(f"✅ Processed data saved to curated: {curated_file.name}")
        
        # Summary
        total_spend = df['Amount spent (USD)'].sum()
        total_impressions = df['Impressions'].sum()
        total_results = df['Results'].sum()
        
        print(f"\n📊 Summary:")
        print(f"  • Total Ads: {len(df)}")
        print(f"  • Total Spend: ${total_spend:,.2f}")
        print(f"  • Total Impressions: {total_impressions:,}")
        print(f"  • Total Results: {total_results:,}")
        
        return df
    
    def print_token_instructions(self):
        """Print instructions for getting a new token"""
        print("\n" + "="*80)
        print("🔑 GET A NEW META ADS API TOKEN")
        print("="*80)
        print("""
        Quick Method:
        1. Go to: https://developers.facebook.com/tools/explorer/
        2. Click "Generate Access Token"
        3. Add permissions: ads_read, ads_management
        4. Click "Generate Access Token" again
        5. Copy the token
        
        Update .env file:
        META_ACCESS_TOKEN=paste_your_new_token_here
        
        The token will last 60-90 days.
        """)

def main():
    """Main execution"""
    print("="*80)
    print("META ADS API DATA FETCHER")
    print("="*80)
    
    fetcher = MetaAdsAPIFetcher()
    
    # Load credentials
    if not fetcher.load_credentials():
        print("\n❌ No credentials found in .env file")
        print("\nAdd these to your .env file:")
        print("META_ACCESS_TOKEN=your_token_here")
        print("META_AD_ACCOUNT_ID=act_your_account_id")
        fetcher.print_token_instructions()
        return
    
    # Initialize API
    if not fetcher.initialize_api():
        return
    
    # Ask for date range
    print("\n📅 Date Range Options:")
    print("1. All time (2022-01-01 to today)")
    print("2. Last 3 months")
    print("3. Custom range")
    
    choice = input("\nSelect option (1-3) [default: 1]: ").strip() or "1"
    
    if choice == "1":
        start_date = "2022-01-01"
        end_date = None
    elif choice == "2":
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        end_date = None
    else:
        start_date = input("Enter start date (YYYY-MM-DD): ")
        end_date = input("Enter end date (YYYY-MM-DD) [leave blank for today]: ").strip() or None
    
    # Fetch data
    ads_data = fetcher.fetch_all_ads_insights(start_date, end_date)
    
    if ads_data:
        # Save to CSV
        df = fetcher.save_to_csv(ads_data)
        
        print("\n✅ SUCCESS! Data fetched and saved.")
        print("\nNext steps:")
        print("1. Run analyze_meta_ads_complete.py to analyze the data")
        print("2. Open the Jupyter notebook for visualizations")
    else:
        print("\n❌ No data fetched. Please check your token and try again.")

if __name__ == "__main__":
    main()