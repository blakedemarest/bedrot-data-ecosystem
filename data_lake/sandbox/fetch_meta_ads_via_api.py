#!/usr/bin/env python3
"""
Fetch Meta Ads Data via API and Recreate CSV
Replaces manual export from Facebook website
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Try to import Facebook Business SDK
try:
    from facebook_business.api import FacebookAdsApi
    from facebook_business.adobjects.adaccount import AdAccount
    from facebook_business.adobjects.adsinsights import AdsInsights
    from facebook_business.adobjects.campaign import Campaign
    from facebook_business.adobjects.adset import AdSet
    from facebook_business.adobjects.ad import Ad
    print("✅ Facebook Business SDK imported successfully")
except ImportError:
    print("❌ Facebook Business SDK not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "facebook-business"])
    from facebook_business.api import FacebookAdsApi
    from facebook_business.adobjects.adaccount import AdAccount
    from facebook_business.adobjects.adsinsights import AdsInsights
    from facebook_business.adobjects.campaign import Campaign
    from facebook_business.adobjects.adset import AdSet
    from facebook_business.adobjects.ad import Ad
    print("✅ Facebook Business SDK installed and imported")

def load_credentials():
    """Load Meta API credentials from .env file"""
    env_path = Path(__file__).parent.parent / '.env'
    credentials = {}
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if 'META_ACCESS_TOKEN' in line and '=' in line:
                    credentials['access_token'] = line.split('=', 1)[1].strip()
                elif 'META_AD_ACCOUNT_ID' in line and '=' in line:
                    credentials['ad_account_id'] = line.split('=', 1)[1].strip()
    
    # Hardcoded fallback (from your .env)
    if not credentials.get('access_token'):
        credentials['access_token'] = 'EAAXvnIxyuoUBO1RocMZAJ9T7O62FVD47QcUxHvxskEFc0YMTYW2NKE4SMmsWBd2cEZAqZCZBhpl8UdZCin05RW6HSx5amqepFIaDvdGcyNZBXpzjzBR2gipR4PBYTPv1mIHb8tZATDNFr6Sg9ZCptxaF95qZAfMf9ANXsNaBVRCIZBPlB2hoVCg29Q8IuqbgSfcFCZCCGF5gsx8'
    if not credentials.get('ad_account_id'):
        credentials['ad_account_id'] = 'act_3952554308360744'
    
    # We don't need app_id and app_secret for read-only operations with user access token
    credentials['app_id'] = 'placeholder'
    credentials['app_secret'] = 'placeholder'
    
    return credentials

def initialize_api(credentials):
    """Initialize Facebook Ads API"""
    try:
        FacebookAdsApi.init(
            credentials.get('app_id'),
            credentials.get('app_secret'),
            credentials['access_token']
        )
        account = AdAccount(credentials['ad_account_id'])
        
        # Test the connection
        account_info = account.api_get(fields=['name', 'account_id', 'currency'])
        print(f"✅ Connected to account: {account_info.get('name')} ({account_info.get('account_id')})")
        print(f"   Currency: {account_info.get('currency')}")
        
        return account
    except Exception as e:
        print(f"❌ Error initializing API: {str(e)}")
        return None

def fetch_ads_data(account, start_date='2022-07-12', end_date=None):
    """Fetch all ads data to recreate the CSV"""
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n📊 Fetching ads data from {start_date} to {end_date}...")
    
    all_ads_data = []
    
    try:
        # Define the fields we need to match the CSV structure
        fields = [
            AdsInsights.Field.ad_name,
            AdsInsights.Field.adset_name,
            AdsInsights.Field.campaign_name,
            AdsInsights.Field.spend,
            AdsInsights.Field.impressions,
            AdsInsights.Field.reach,
            AdsInsights.Field.clicks,
            AdsInsights.Field.cpc,
            AdsInsights.Field.cpm,
            AdsInsights.Field.cpp,
            AdsInsights.Field.ctr,
            AdsInsights.Field.frequency,
            AdsInsights.Field.conversions,
            AdsInsights.Field.cost_per_conversion,
            AdsInsights.Field.actions,
            AdsInsights.Field.action_values,
            AdsInsights.Field.cost_per_action_type,
            AdsInsights.Field.quality_ranking,
            AdsInsights.Field.engagement_rate_ranking,
            AdsInsights.Field.conversion_rate_ranking,
        ]
        
        # Parameters for the insights request
        params = {
            'level': 'ad',
            'time_range': {
                'since': start_date,
                'until': end_date
            },
            'fields': fields,
            'filtering': [{'field': 'spend', 'operator': 'GREATER_THAN', 'value': 0}],
            'limit': 500
        }
        
        # Fetch insights
        insights = account.get_insights(params=params)
        
        print(f"Processing ads data...")
        
        for insight in insights:
            # Extract actions to get specific conversion types
            actions = insight.get('actions', [])
            conversions = 0
            for action in actions:
                if action['action_type'] == 'offsite_conversion.fb_pixel_view_content':
                    conversions = int(action['value'])
            
            # Extract cost per action
            cost_per_actions = insight.get('cost_per_action_type', [])
            cost_per_conversion = 0
            for cpa in cost_per_actions:
                if cpa['action_type'] == 'offsite_conversion.fb_pixel_view_content':
                    cost_per_conversion = float(cpa['value'])
            
            ad_data = {
                'Reporting starts': start_date,
                'Reporting ends': end_date,
                'Ad name': insight.get('ad_name', ''),
                'Ad delivery': 'active' if float(insight.get('spend', 0)) > 0 else 'not_delivering',
                'Ad Set Name': insight.get('adset_name', ''),
                'Campaign Name': insight.get('campaign_name', ''),
                'Amount spent (USD)': float(insight.get('spend', 0)),
                'Impressions': int(insight.get('impressions', 0)),
                'Reach': int(insight.get('reach', 0)),
                'Clicks': int(insight.get('clicks', 0)),
                'CPC': float(insight.get('cpc', 0)),
                'CPM': float(insight.get('cpm', 0)),
                'CTR': float(insight.get('ctr', 0)),
                'Frequency': float(insight.get('frequency', 0)),
                'Results': conversions,
                'Cost per results': cost_per_conversion,
                'Quality ranking': insight.get('quality_ranking', '-'),
                'Engagement rate ranking': insight.get('engagement_rate_ranking', '-'),
                'Conversion rate ranking': insight.get('conversion_rate_ranking', '-'),
            }
            
            all_ads_data.append(ad_data)
        
        print(f"✅ Fetched {len(all_ads_data)} ads with spend > 0")
        
    except Exception as e:
        print(f"❌ Error fetching ads data: {str(e)}")
        print("Attempting alternative approach...")
        
        # Alternative: Get ads first, then insights
        try:
            all_ads_data = fetch_ads_alternative(account, start_date, end_date)
        except Exception as e2:
            print(f"❌ Alternative approach also failed: {str(e2)}")
    
    return all_ads_data

def fetch_ads_alternative(account, start_date, end_date):
    """Alternative method: fetch ads list first, then get insights"""
    all_ads_data = []
    
    # Get all campaigns
    campaigns = account.get_campaigns(fields=['name'])
    
    for campaign in campaigns:
        print(f"  Processing campaign: {campaign.get('name')}")
        
        # Get adsets for this campaign
        adsets = campaign.get_ad_sets(fields=['name'])
        
        for adset in adsets:
            # Get ads for this adset
            ads = adset.get_ads(fields=['name'])
            
            for ad in ads:
                # Get insights for this specific ad
                try:
                    params = {
                        'time_range': {
                            'since': start_date,
                            'until': end_date
                        }
                    }
                    
                    insights = ad.get_insights(params=params, fields=[
                        AdsInsights.Field.spend,
                        AdsInsights.Field.impressions,
                        AdsInsights.Field.reach,
                        AdsInsights.Field.clicks,
                        AdsInsights.Field.actions,
                    ])
                    
                    for insight in insights:
                        if float(insight.get('spend', 0)) > 0:
                            ad_data = {
                                'Reporting starts': start_date,
                                'Reporting ends': end_date,
                                'Ad name': ad.get('name', ''),
                                'Ad delivery': 'active',
                                'Ad Set Name': adset.get('name', ''),
                                'Campaign Name': campaign.get('name', ''),
                                'Amount spent (USD)': float(insight.get('spend', 0)),
                                'Impressions': int(insight.get('impressions', 0)),
                                'Reach': int(insight.get('reach', 0)),
                                'Clicks': int(insight.get('clicks', 0)),
                            }
                            all_ads_data.append(ad_data)
                
                except Exception as e:
                    continue
    
    return all_ads_data

def create_csv_from_api_data(ads_data):
    """Create CSV file matching the original format"""
    if not ads_data:
        print("❌ No data to save")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(ads_data)
    
    # Fill missing columns with default values
    required_columns = [
        'Reporting starts', 'Reporting ends', 'Ad name', 'Ad delivery',
        'Ad Set Name', 'Bid', 'Bid type', 'Ad set budget', 'Ad set budget type',
        'Last significant edit', 'Attribution setting', 'Results',
        'Result indicator', 'Reach', 'Impressions', 'Cost per results',
        'Quality ranking', 'Engagement rate ranking', 'Conversion rate ranking',
        'Amount spent (USD)', 'Ends'
    ]
    
    for col in required_columns:
        if col not in df.columns:
            if col == 'Bid':
                df[col] = 0
            elif col == 'Bid type':
                df[col] = 'ABSOLUTE_OCPM'
            elif col == 'Ad set budget':
                df[col] = 5
            elif col == 'Ad set budget type':
                df[col] = 'Daily'
            elif col == 'Attribution setting':
                df[col] = '7-day click, 1-day view, or 1-day engaged-view'
            elif col == 'Result indicator':
                df[col] = 'actions:offsite_conversion.fb_pixel_view_content'
            elif col == 'Ends':
                df[col] = 'Ongoing'
            elif col == 'Last significant edit':
                df[col] = 0
            else:
                df[col] = '-'
    
    # Reorder columns to match original
    df = df[required_columns]
    
    # Save to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = Path(__file__).parent.parent / '4_curated'
    output_file = output_path / f'meta_ads_api_export_{timestamp}.csv'
    
    df.to_csv(output_file, index=False)
    print(f"\n✅ CSV file created: {output_file}")
    print(f"   Rows: {len(df)}")
    print(f"   Total Spend: ${df['Amount spent (USD)'].sum():,.2f}")
    
    return df

def main():
    """Main execution"""
    print("="*80)
    print("META ADS API DATA FETCHER")
    print("="*80)
    
    # Load credentials
    print("\n1. Loading credentials...")
    credentials = load_credentials()
    
    # Initialize API
    print("\n2. Initializing API...")
    account = initialize_api(credentials)
    
    if not account:
        print("\n❌ Failed to initialize API. Trying with a fresh token...")
        print("\nTo get a fresh token:")
        print("1. Go to: https://developers.facebook.com/tools/explorer/")
        print("2. Select your app")
        print("3. Add permissions: ads_read, ads_management")
        print("4. Generate token")
        print("5. Update META_ACCESS_TOKEN in .env file")
        return
    
    # Fetch data
    print("\n3. Fetching ads data...")
    ads_data = fetch_ads_data(account, start_date='2022-07-12')
    
    if ads_data:
        # Create CSV
        print("\n4. Creating CSV file...")
        df = create_csv_from_api_data(ads_data)
        
        # Summary
        if df is not None:
            print("\n" + "="*80)
            print("SUMMARY")
            print("="*80)
            print(f"Total Ads: {len(df)}")
            print(f"Total Spend: ${df['Amount spent (USD)'].sum():,.2f}")
            print(f"Date Range: {df['Reporting starts'].min()} to {df['Reporting ends'].max()}")
            
            # Group by campaign
            if 'Campaign Name' in df.columns:
                campaign_spend = df.groupby('Campaign Name')['Amount spent (USD)'].sum().sort_values(ascending=False)
                print(f"\nTop Campaigns:")
                for campaign, spend in campaign_spend.head(5).items():
                    print(f"  • {campaign}: ${spend:,.2f}")
    else:
        print("\n❌ No data retrieved. Please check your access token and permissions.")

if __name__ == "__main__":
    main()