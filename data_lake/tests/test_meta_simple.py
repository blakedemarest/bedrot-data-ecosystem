#!/usr/bin/env python3
"""
Simple Meta API Test - Tests basic connectivity
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

def test_simple():
    """Test basic Meta API connectivity"""
    
    print("=" * 80)
    print("SIMPLE META API TEST")
    print("=" * 80)
    
    access_token = os.getenv('META_ACCESS_TOKEN')
    ad_account_id = os.getenv('META_AD_ACCOUNT_ID')
    
    print(f"[INFO] Token length: {len(access_token)} chars")
    print(f"[INFO] Ad Account: {ad_account_id}")
    
    # Test 1: Get user info
    print("\n[TEST 1] Getting user info...")
    url = "https://graph.facebook.com/v18.0/me"
    params = {
        'access_token': access_token,
        'fields': 'id,name,email'
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if 'error' not in data:
        print(f"[SUCCESS] User: {data.get('name', 'Unknown')}")
        print(f"[SUCCESS] ID: {data.get('id', 'Unknown')}")
        user_id = data.get('id')
    else:
        print(f"[ERROR] {data['error']['message']}")
        return
    
    # Test 2: Get ad accounts the user has access to
    print("\n[TEST 2] Getting accessible ad accounts...")
    url = f"https://graph.facebook.com/v18.0/{user_id}/adaccounts"
    params = {
        'access_token': access_token,
        'fields': 'id,name,account_status,currency,amount_spent'
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if 'data' in data:
        accounts = data['data']
        print(f"[SUCCESS] Found {len(accounts)} ad account(s)")
        
        for acc in accounts:
            print(f"\nAccount: {acc.get('id')}")
            print(f"  Name: {acc.get('name', 'N/A')}")
            print(f"  Status: {acc.get('account_status', 'N/A')}")
            print(f"  Currency: {acc.get('currency', 'N/A')}")
            
            # Check if this is our target account
            if acc.get('id') == ad_account_id:
                print("  [MATCH] This is the configured account!")
    else:
        print(f"[ERROR] {data.get('error', {}).get('message', 'Unknown error')}")
    
    # Test 3: Try different API version
    print("\n[TEST 3] Testing with API v20.0...")
    url = f"https://graph.facebook.com/v20.0/{ad_account_id}"
    params = {
        'access_token': access_token,
        'fields': 'id,name'
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if 'error' not in data:
        print(f"[SUCCESS] Account accessible with v20.0!")
        print(f"  ID: {data.get('id')}")
        print(f"  Name: {data.get('name', 'N/A')}")
    else:
        print(f"[INFO] v20.0 also requires permission grant")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print("\nBased on the test results:")
    print("1. Your token is valid and working")
    print("2. You can see which ad accounts you have access to")
    print("3. Check if the configured account ID matches your accessible accounts")
    print("4. If not listed, you need to request access from the account owner")

if __name__ == "__main__":
    test_simple()