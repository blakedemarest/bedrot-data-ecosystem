# Fix Meta Ads API Access - Action Required

## Current Situation

✅ **Token is Valid** - "Conversions API System User" token is working
❌ **No Ad Accounts** - The System User has 0 ad accounts assigned
❌ **Account ID Mismatch** - Trying to access `act_3952554308360744` but user has no access

## IMMEDIATE FIX NEEDED

You need to assign the ad account to your System User in Business Manager.

### Step-by-Step Fix (5 minutes)

1. **Go to Meta Business Manager**
   - https://business.facebook.com
   - Log in with the account that owns the ad account

2. **Navigate to System Users**
   - Business Settings (gear icon) → Users → System Users
   - Find "Conversions API System User" (ID: 122137214192731342)

3. **Add Ad Account to System User**
   - Click on "Conversions API System User"
   - Click "Add Assets" button
   - Select "Ad Accounts"
   - Find and check: `act_3952554308360744` (BEDROT-ADS)
   - Select permissions:
     - ✅ Manage campaigns
     - ✅ View performance
     - ✅ Manage ads
   - Click "Save Changes"

4. **Verify Access**
   - After saving, the ad account should appear under the System User's assets
   - The permissions should show as active

5. **Test Again**
   ```bash
   cd data_lake
   .venv/Scripts/python.exe test_meta_simple.py
   ```
   
   You should now see:
   - Found 1 ad account(s)
   - Account: act_3952554308360744
   - Name: BEDROT-ADS

## Alternative: Generate New Token

If the above doesn't work, generate a new token:

1. **In System Users**
   - Select "Conversions API System User"
   - Click "Generate New Token"
   - Select these permissions:
     - ads_management
     - ads_read
     - business_management
   - Click "Generate Token"
   - Copy the new token

2. **Update .env**
   ```
   META_ACCESS_TOKEN=<new_token_here>
   ```

## Why This Happened

Your System User was created but never assigned to the ad account. This is a common setup step that's easy to miss. System Users need explicit permission to access ad accounts, even if they're in the same Business Manager.

## Quick Check Command

Run this to verify which accounts you have access to:
```bash
.venv/Scripts/python.exe test_meta_simple.py
```

Currently shows: **0 ad accounts**
Should show: **1 ad account (act_3952554308360744)**

## Once Fixed

After granting access, you'll be able to:
- Fetch real-time campaign data
- Get detailed insights via API
- Automate reporting
- Track ROI in real-time

---
**Need Help?** The issue is specifically that the System User needs the ad account assigned in Business Manager. This is a one-time setup that takes 2-3 minutes.