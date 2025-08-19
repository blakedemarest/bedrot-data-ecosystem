#!/usr/bin/env python3
"""
Test Meta Ads API Connection
Validates that the API credentials work and can fetch basic account info
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

def test_meta_api():
    """Test Meta Ads API connection and fetch basic account info"""
    
    print("=" * 80)
    print("META ADS API CONNECTION TEST")
    print("=" * 80)
    
    # Get credentials
    access_token = os.getenv('META_ACCESS_TOKEN')
    ad_account_id = os.getenv('META_AD_ACCOUNT_ID')
    
    if not access_token or not ad_account_id:
        print("[ERROR] Missing credentials in .env file")
        return False
    
    print(f"[INFO] Access Token Length: {len(access_token)} chars")
    print(f"[INFO] Ad Account ID: {ad_account_id}")
    
    # Test 1: Verify token validity
    print("\n[TEST 1] Verifying access token...")
    debug_url = f"https://graph.facebook.com/debug_token?input_token={access_token}&access_token={access_token}"
    
    try:
        response = requests.get(debug_url)
        data = response.json()
        
        if 'data' in data:
            token_data = data['data']
            is_valid = token_data.get('is_valid', False)
            
            if is_valid:
                print("[SUCCESS] Token is valid!")
                expires_at = token_data.get('expires_at', 0)
                if expires_at:
                    expiry_date = datetime.fromtimestamp(expires_at)
                    print(f"[INFO] Token expires: {expiry_date}")
                
                scopes = token_data.get('scopes', [])
                print(f"[INFO] All Permissions: {', '.join(scopes)}")
                
                # Check for required permissions
                required_perms = ['ads_management', 'ads_read']
                has_required = all(perm in scopes for perm in required_perms)
                
                if not has_required:
                    print("[WARNING] Missing required permissions!")
                    print(f"[WARNING] Need: {', '.join(required_perms)}")
                    print("[INFO] Please re-authenticate with proper permissions")
            else:
                print("[ERROR] Token is invalid")
                error = token_data.get('error', {})
                print(f"[ERROR] {error.get('message', 'Unknown error')}")
                return False
        else:
            print(f"[ERROR] {data.get('error', {}).get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to verify token: {e}")
        return False
    
    # Test 2: Fetch account info
    print("\n[TEST 2] Fetching ad account information...")
    account_url = f"https://graph.facebook.com/v18.0/{ad_account_id}"
    params = {
        'access_token': access_token,
        'fields': 'name,account_status,currency,timezone_name,spend_cap,amount_spent'
    }
    
    try:
        response = requests.get(account_url, params=params)
        data = response.json()
        
        if 'error' not in data:
            print("[SUCCESS] Account accessed successfully!")
            print(f"[INFO] Account Name: {data.get('name', 'N/A')}")
            print(f"[INFO] Currency: {data.get('currency', 'N/A')}")
            print(f"[INFO] Timezone: {data.get('timezone_name', 'N/A')}")
            print(f"[INFO] Account Status: {data.get('account_status', 'N/A')}")
            
            spend_cap = data.get('spend_cap')
            if spend_cap:
                print(f"[INFO] Spend Cap: {spend_cap}")
                
            amount_spent = data.get('amount_spent')
            if amount_spent:
                print(f"[INFO] Lifetime Spend: {amount_spent}")
        else:
            error = data['error']
            print(f"[ERROR] {error.get('message', 'Unknown error')}")
            print(f"[ERROR] Code: {error.get('code', 'N/A')}")
            print(f"[ERROR] Type: {error.get('type', 'N/A')}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to fetch account info: {e}")
        return False
    
    # Test 3: Fetch recent campaign data
    print("\n[TEST 3] Fetching recent campaign insights...")
    
    # Calculate date range (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    insights_url = f"https://graph.facebook.com/v18.0/{ad_account_id}/insights"
    
    # Format time_range as JSON string
    import json
    time_range = json.dumps({
        'since': start_date.strftime('%Y-%m-%d'),
        'until': end_date.strftime('%Y-%m-%d')
    })
    
    params = {
        'access_token': access_token,
        'fields': 'spend,impressions,reach,clicks,cpm,cpc',
        'level': 'account',
        'time_range': time_range
    }
    
    try:
        response = requests.get(insights_url, params=params)
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            insights = data['data'][0]
            print("[SUCCESS] Insights retrieved!")
            print(f"\n[LAST 30 DAYS METRICS]")
            print(f"  Spend: ${float(insights.get('spend', 0)):.2f}")
            print(f"  Impressions: {insights.get('impressions', 0)}")
            print(f"  Reach: {insights.get('reach', 0)}")
            print(f"  Clicks: {insights.get('clicks', 0)}")
            
            cpm = insights.get('cpm')
            if cpm:
                print(f"  CPM: ${float(cpm):.2f}")
                
            cpc = insights.get('cpc')
            if cpc:
                print(f"  CPC: ${float(cpc):.2f}")
        elif 'error' in data:
            error = data['error']
            print(f"[WARNING] Could not fetch insights: {error.get('message', 'Unknown error')}")
        else:
            print("[INFO] No data available for the last 30 days")
            
    except Exception as e:
        print(f"[WARNING] Failed to fetch insights: {e}")
    
    print("\n" + "=" * 80)
    print("API TEST COMPLETE")
    print("=" * 80)
    print("[SUCCESS] Meta Ads API is configured and working correctly!")
    print("\nYou can now:")
    print("1. Run extractors to fetch campaign data")
    print("2. Use the API to get real-time insights")
    print("3. Automate campaign reporting")
    
    return True

if __name__ == "__main__":
    success = test_meta_api()
    exit(0 if success else 1)