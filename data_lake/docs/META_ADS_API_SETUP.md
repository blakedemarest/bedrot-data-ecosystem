# Meta Ads API Setup Guide

## Current Status

✅ **Access Token is Valid** - Your token has the necessary permissions
✅ **Permissions Present** - ads_management, ads_read, business_management
❌ **Account Access Blocked** - The ad account owner needs to grant permission

## Issue

Error: `(#200) Ad account owner has NOT grant ads_management or ads_read permission`

This means your access token is valid but the ad account (`act_3952554308360744`) hasn't authorized your app/user to access it.

## Solution Steps

### Option 1: Grant Access via Business Manager (Recommended)

1. **Log into Meta Business Suite**: https://business.facebook.com
2. **Go to Business Settings** → **People**
3. **Find your user** (bedrotprod@gmail.com)
4. **Click on the user** → **Ad Accounts**
5. **Select your ad account** (BEDROT-ADS)
6. **Grant these permissions**:
   - Campaign Management
   - Ad Management
   - View Performance

### Option 2: System User (For Automation)

1. **Create System User**:
   - Business Settings → System Users → Add
   - Name: "BEDROT API User"
   - Role: Admin

2. **Assign Ad Account**:
   - Select System User → Add Assets
   - Choose Ad Accounts → Select your account
   - Grant "Manage campaigns" permission

3. **Generate Token**:
   - Select System User → Generate Token
   - Select permissions: ads_management, ads_read
   - Copy the new token

### Option 3: Re-authenticate with Graph API Explorer

1. **Visit**: https://developers.facebook.com/tools/explorer/
2. **Select your app** (or use default)
3. **Get User Access Token**
4. **Select Permissions**:
   - ads_management
   - ads_read
   - business_management
5. **Important**: Make sure you're logged in as the ad account owner
6. **Generate Access Token**
7. **Exchange for Long-Lived Token**:
```bash
curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token?  
  grant_type=fb_exchange_token&  
  client_id={your-app-id}&  
  client_secret={your-app-secret}&  
  fb_exchange_token={short-lived-token}"
```

## After Fixing

Once permissions are granted, test again:
```bash
cd data_lake
.venv/Scripts/python.exe test_meta_api.py
```

You should see:
- Account Name
- Currency
- Spend data
- Recent campaign metrics

## Important Notes

- The token you have IS valid with correct permissions
- The issue is at the ad account level, not the token level
- System User tokens are best for automation (they don't expire)
- Regular user tokens expire after 60 days

## Your Current Credentials

```
META_ACCESS_TOKEN=EAAOCVoMBVXcBPELgfVPyZCbqdCZCHvX8xgwRzIHLeQrrG4D53ZCQde0uM4VY440r6XsyqP9wGAwZA4dOK7zMQzfAmcxppoZB2rUjfRWZAdYaEw1lZC7qpxGBnX5hCeaJlR6V1QahawRadimlRDopiCpVDySZBBt9b0TlbrYsL9ZAfnaHg4rhQMlsOQbGO5Xc56gZDZD
META_AD_ACCOUNT_ID=act_3952554308360744
```

## CSV Data Analysis Works!

While waiting for API access, you can still:
1. Analyze the exported CSV data (which is working)
2. Total spend found: $3,105.42
3. ROI calculated: -46.5% (needs optimization)

## Next Steps

1. Grant permissions in Business Manager
2. Re-run `test_meta_api.py` to verify
3. Once working, create automated extractors
4. Set up daily/weekly reporting