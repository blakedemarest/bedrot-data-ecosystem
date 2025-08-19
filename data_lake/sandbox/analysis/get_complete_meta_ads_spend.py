#!/usr/bin/env python3
"""
Get Complete Meta Ads Spend Data
Retrieves all-time advertising spend from Meta Ads API
"""

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from datetime import datetime, timedelta
import pandas as pd
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def initialize_meta_api():
    """Initialize Meta API with credentials from environment"""
    # These should be in your .env file
    app_id = os.getenv('META_APP_ID')
    app_secret = os.getenv('META_APP_SECRET')
    access_token = os.getenv('META_ACCESS_TOKEN')
    ad_account_id = os.getenv('META_AD_ACCOUNT_ID')  # Format: act_123456789
    
    if not all([app_id, app_secret, access_token, ad_account_id]):
        print("\n⚠️ Missing Meta API credentials in .env file!")
        print("\nYou need to add these to your .env file:")
        print("META_APP_ID=your_app_id")
        print("META_APP_SECRET=your_app_secret")
        print("META_ACCESS_TOKEN=your_access_token")
        print("META_AD_ACCOUNT_ID=act_your_account_id")
        print("\nTo get these credentials:")
        print("1. Go to https://developers.facebook.com/apps/")
        print("2. Select your app (or create one)")
        print("3. Go to Settings > Basic for App ID and Secret")
        print("4. Go to Tools > Access Token Debugger for a token")
        print("5. Find your Ad Account ID in Meta Ads Manager")
        return None, None
    
    # Initialize the API
    FacebookAdsApi.init(app_id, app_secret, access_token)
    
    return AdAccount(ad_account_id), access_token

def get_all_time_spend(ad_account):
    """Get all-time advertising spend data"""
    print("\n📊 Fetching all-time Meta Ads spend data...")
    
    # Define parameters for the insights request
    params = {
        'level': 'account',
        'fields': [
            AdsInsights.Field.spend,
            AdsInsights.Field.impressions,
            AdsInsights.Field.clicks,
            AdsInsights.Field.cpc,
            AdsInsights.Field.cpm,
            AdsInsights.Field.ctr,
            AdsInsights.Field.account_currency,
            AdsInsights.Field.account_name,
        ],
        'time_range': {
            'since': '2024-01-01',  # Adjust based on when you started advertising
            'until': datetime.now().strftime('%Y-%m-%d')
        },
        'time_increment': 1,  # Daily breakdown
    }
    
    # Get insights
    insights = ad_account.get_insights(params=params)
    
    # Convert to DataFrame
    data = []
    for insight in insights:
        data.append({
            'date': insight.get('date_start'),
            'spend': float(insight.get('spend', 0)),
            'impressions': int(insight.get('impressions', 0)),
            'clicks': int(insight.get('clicks', 0)),
            'cpc': float(insight.get('cpc', 0)),
            'cpm': float(insight.get('cpm', 0)),
            'ctr': float(insight.get('ctr', 0)),
            'currency': insight.get('account_currency', 'USD'),
        })
    
    df = pd.DataFrame(data)
    return df

def get_campaign_level_spend(ad_account):
    """Get campaign-level spend breakdown"""
    print("\n📊 Fetching campaign-level breakdown...")
    
    params = {
        'level': 'campaign',
        'fields': [
            AdsInsights.Field.campaign_name,
            AdsInsights.Field.campaign_id,
            AdsInsights.Field.spend,
            AdsInsights.Field.impressions,
            AdsInsights.Field.clicks,
            AdsInsights.Field.cpc,
            AdsInsights.Field.objective,
        ],
        'time_range': {
            'since': '2024-01-01',
            'until': datetime.now().strftime('%Y-%m-%d')
        },
        'filtering': [{'field': 'spend', 'operator': 'GREATER_THAN', 'value': 0}],
    }
    
    insights = ad_account.get_insights(params=params)
    
    campaigns = []
    for insight in insights:
        campaigns.append({
            'campaign_name': insight.get('campaign_name'),
            'campaign_id': insight.get('campaign_id'),
            'objective': insight.get('objective'),
            'total_spend': float(insight.get('spend', 0)),
            'total_impressions': int(insight.get('impressions', 0)),
            'total_clicks': int(insight.get('clicks', 0)),
            'avg_cpc': float(insight.get('cpc', 0)),
        })
    
    return pd.DataFrame(campaigns)

def get_monthly_spend(ad_account):
    """Get monthly spend summary"""
    print("\n📊 Calculating monthly spend summary...")
    
    params = {
        'level': 'account',
        'fields': [
            AdsInsights.Field.spend,
            AdsInsights.Field.impressions,
            AdsInsights.Field.clicks,
        ],
        'time_range': {
            'since': '2024-01-01',
            'until': datetime.now().strftime('%Y-%m-%d')
        },
        'time_increment': 'monthly',
    }
    
    insights = ad_account.get_insights(params=params)
    
    monthly = []
    for insight in insights:
        monthly.append({
            'month': insight.get('date_start')[:7],  # YYYY-MM format
            'spend': float(insight.get('spend', 0)),
            'impressions': int(insight.get('impressions', 0)),
            'clicks': int(insight.get('clicks', 0)),
        })
    
    return pd.DataFrame(monthly)

def save_to_curated(df_daily, df_campaigns, df_monthly):
    """Save data to curated zone"""
    curated_path = "/mnt/c/Users/Earth/BEDROT PRODUCTIONS/bedrot-data-ecosystem/data_lake/4_curated/"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save daily data
    daily_file = f"{curated_path}metaads_complete_daily_{timestamp}.csv"
    df_daily.to_csv(daily_file, index=False)
    print(f"\n✅ Saved daily data to: {daily_file}")
    
    # Save campaign data
    campaign_file = f"{curated_path}metaads_campaigns_complete_{timestamp}.csv"
    df_campaigns.to_csv(campaign_file, index=False)
    print(f"✅ Saved campaign data to: {campaign_file}")
    
    # Save monthly summary
    monthly_file = f"{curated_path}metaads_monthly_summary_{timestamp}.csv"
    df_monthly.to_csv(monthly_file, index=False)
    print(f"✅ Saved monthly summary to: {monthly_file}")
    
    return daily_file, campaign_file, monthly_file

def main():
    """Main execution"""
    print("="*80)
    print("META ADS COMPLETE SPEND RETRIEVAL")
    print("="*80)
    
    # Initialize API
    ad_account, access_token = initialize_meta_api()
    
    if not ad_account:
        print("\n❌ Cannot proceed without API credentials.")
        print("\nAlternative: Manual Export from Meta Ads Manager")
        print("-" * 50)
        print("1. Go to https://business.facebook.com/adsmanager")
        print("2. Click 'Reports' in the top menu")
        print("3. Select date range: 'Lifetime' or custom range")
        print("4. Click 'Export' > 'Export Table Data (.csv)'")
        print("5. Save the file to the curated folder")
        return
    
    try:
        # Get all data
        df_daily = get_all_time_spend(ad_account)
        df_campaigns = get_campaign_level_spend(ad_account)
        df_monthly = get_monthly_spend(ad_account)
        
        # Calculate totals
        total_spend = df_daily['spend'].sum()
        total_clicks = df_daily['clicks'].sum()
        total_impressions = df_daily['impressions'].sum()
        avg_cpc = total_spend / total_clicks if total_clicks > 0 else 0
        
        print("\n" + "="*80)
        print("ALL-TIME META ADS METRICS")
        print("="*80)
        print(f"\n💰 TOTAL SPEND: ${total_spend:,.2f}")
        print(f"🖱️ TOTAL CLICKS: {total_clicks:,}")
        print(f"👁️ TOTAL IMPRESSIONS: {total_impressions:,}")
        print(f"💵 AVERAGE CPC: ${avg_cpc:.3f}")
        
        # Show by campaign
        print("\n" + "-"*50)
        print("SPEND BY CAMPAIGN:")
        print("-"*50)
        for _, row in df_campaigns.sort_values('total_spend', ascending=False).iterrows():
            print(f"\n{row['campaign_name']}:")
            print(f"  Spend: ${row['total_spend']:,.2f}")
            print(f"  Clicks: {row['total_clicks']:,}")
            print(f"  CPC: ${row['avg_cpc']:.3f}")
        
        # Show monthly trend
        print("\n" + "-"*50)
        print("MONTHLY SPEND TREND:")
        print("-"*50)
        for _, row in df_monthly.iterrows():
            print(f"{row['month']}: ${row['spend']:,.2f} ({row['clicks']:,} clicks)")
        
        # Save to curated
        save_to_curated(df_daily, df_campaigns, df_monthly)
        
        print("\n✅ Complete! All data has been retrieved and saved.")
        
    except Exception as e:
        print(f"\n❌ Error retrieving data: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check if your access token is still valid")
        print("2. Ensure you have the right permissions (ads_read)")
        print("3. Verify your ad account ID is correct")
        print("\nTo refresh your token:")
        print("https://developers.facebook.com/tools/explorer/")

if __name__ == "__main__":
    main()