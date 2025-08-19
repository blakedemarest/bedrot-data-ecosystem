# Meta Ads Complete Spend Export Guide

## Quick Manual Export (Recommended)

Since your automated data only shows $456.15 from May-June 2025, here's how to get your complete spending history:

### Step 1: Access Meta Ads Manager
1. Go to: https://business.facebook.com/adsmanager
2. Log in with your account

### Step 2: Navigate to Reporting
1. Click **"Reports"** in the top menu
2. Or use direct link: https://business.facebook.com/adsmanager/reporting

### Step 3: Set Date Range for All-Time Data
1. Click the date range selector (usually shows "Last 30 days")
2. Select **"Lifetime"** or
3. Choose **"Custom"** and set:
   - Start: January 1, 2024 (or when you started)
   - End: Today

### Step 4: Configure Columns
Click **"Columns"** dropdown and select **"Performance and Clicks"** to include:
- Campaign name
- Delivery
- Results
- Reach
- Impressions
- Amount Spent
- Cost per Result
- Clicks (All)
- CPC (All)

### Step 5: Export the Data
1. Click **"Export"** button (top right)
2. Choose **"Export Table Data (.csv)"**
3. Save as: `metaads_complete_export_YYYYMMDD.csv`
4. Move to: `/data_lake/4_curated/`

## Account Spending Limit Check

To see your total historical spend:

1. Go to: https://business.facebook.com/settings/ad-accounts
2. Click on your ad account
3. Go to **"Payment Settings"**
4. Look for **"Total Spent"** or **"Lifetime Spent"**

## API Alternative Setup

If you want to automate this:

### Get Your Credentials

1. **App ID & Secret**:
   - Go to: https://developers.facebook.com/apps/
   - Select your app (or create one)
   - Settings > Basic

2. **Access Token**:
   - Go to: https://developers.facebook.com/tools/explorer/
   - Select your app
   - Add permissions: `ads_read`, `ads_management`
   - Generate token

3. **Ad Account ID**:
   - In Ads Manager, look at the URL
   - Format: `act_123456789`
   - Or go to Business Settings > Ad Accounts

### Add to .env file:
```
META_APP_ID=your_app_id_here
META_APP_SECRET=your_app_secret_here
META_ACCESS_TOKEN=your_access_token_here
META_AD_ACCOUNT_ID=act_your_account_id_here
```

### Run the Script:
```bash
cd /mnt/c/Users/Earth/BEDROT\ PRODUCTIONS/bedrot-data-ecosystem/data_lake
python get_complete_meta_ads_spend.py
```

## Quick Insights Export

For a quick spending summary:

1. Go to: https://business.facebook.com/adsmanager/manage
2. Look at the account overview (top of page)
3. It shows: **"Amount Spent: $X,XXX.XX"** for selected period
4. Change date range to "Lifetime" to see total

## Expected Data

Based on your campaigns, you should see:
- Multiple months of data (not just May-June)
- Various artist campaigns (ZONE A0, PIG1987, IWARY)
- Total spend likely in the $1,000-5,000 range

## Troubleshooting

If the exported amount seems wrong:
1. Check if you have multiple ad accounts
2. Verify the date range includes all campaigns
3. Check if some campaigns are in a different currency
4. Look for archived or deleted campaigns

## Next Steps

Once you have the complete data:
1. Compare with your bank statements
2. Update your ROI calculations
3. Re-run the business metrics analysis
4. Plan future campaign budgets based on actual CPA