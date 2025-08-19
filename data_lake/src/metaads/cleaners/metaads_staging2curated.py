# %%
# ─── Cell 1: Imports & Environment Setup ────────────────────────────────────────
# Create business-ready datasets from staging Meta Ads data
import os
import json
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT"))
STAGING = PROJECT_ROOT / os.getenv("STAGING_ZONE", "3_staging")
CURATED = PROJECT_ROOT / os.getenv("CURATED_ZONE", "4_curated")

# %%
# ─── Cell 2: Load Staging Data ───────────────────────────────────────────────────
staging_meta = STAGING / "metaads"
curated_meta = CURATED / "metaads"
curated_meta.mkdir(parents=True, exist_ok=True)

# Load the latest staging file
latest_staging = staging_meta / "metaads_staging_latest.csv"

if not latest_staging.exists():
    # Try to find any staging file
    staging_files = list(staging_meta.glob("metaads_staging_*.csv"))
    if staging_files:
        latest_staging = sorted(staging_files)[-1]
    else:
        print(f"[ERROR] No staging files found in {staging_meta}")
        exit(1)

print(f"[INFO] Loading staging data from: {latest_staging}")
# Try to parse date columns but ignore if they don't exist
try:
    df = pd.read_csv(latest_staging, parse_dates=['date', 'date_start', 'date_end'], 
                     dayfirst=False)
except:
    # If date columns don't exist, just read normally
    df = pd.read_csv(latest_staging)

print(f"[INFO] Loaded {len(df)} records")

# %%
# ─── Cell 3: Create Campaign Performance Summary ─────────────────────────────────
# Aggregate by campaign
campaign_columns = ['campaign_id', 'campaign_name', 'campaign_objective', 'campaign_status']
available_campaign_cols = [col for col in campaign_columns if col in df.columns]

if 'campaign_name' in df.columns:
    groupby_col = 'campaign_name'
elif 'campaign_id' in df.columns:
    groupby_col = 'campaign_id'
else:
    groupby_col = None

campaign_summary = None
if groupby_col and 'spend_usd' in df.columns:
    # Aggregate metrics
    agg_dict = {}
    if 'spend_usd' in df.columns:
        agg_dict['spend_usd'] = 'sum'
    if 'impressions' in df.columns:
        agg_dict['impressions'] = 'sum'
    if 'clicks' in df.columns:
        agg_dict['clicks'] = 'sum'
    if 'reach' in df.columns:
        agg_dict['reach'] = 'sum'
    
    # Add first value for metadata columns
    for col in available_campaign_cols:
        if col != groupby_col and col in df.columns:
            agg_dict[col] = 'first'
    
    campaign_summary = df.groupby(groupby_col).agg(agg_dict).round(2)
    
    # Calculate performance metrics
    if 'spend_usd' in campaign_summary.columns and 'impressions' in campaign_summary.columns:
        campaign_summary['cpm'] = (campaign_summary['spend_usd'] / campaign_summary['impressions'] * 1000).round(2)
        campaign_summary.loc[campaign_summary['impressions'] == 0, 'cpm'] = 0
    
    if 'spend_usd' in campaign_summary.columns and 'clicks' in campaign_summary.columns:
        campaign_summary['cpc'] = (campaign_summary['spend_usd'] / campaign_summary['clicks']).round(2)
        campaign_summary.loc[campaign_summary['clicks'] == 0, 'cpc'] = 0
    
    if 'clicks' in campaign_summary.columns and 'impressions' in campaign_summary.columns:
        campaign_summary['ctr'] = (campaign_summary['clicks'] / campaign_summary['impressions'] * 100).round(4)
        campaign_summary.loc[campaign_summary['impressions'] == 0, 'ctr'] = 0
    
    # Sort by spend
    if 'spend_usd' in campaign_summary.columns:
        campaign_summary = campaign_summary.sort_values('spend_usd', ascending=False)
    
    # Save campaign summary
    campaign_file = curated_meta / f"campaign_summary_{datetime.now():%Y%m%d}.csv"
    campaign_summary.to_csv(campaign_file, encoding='utf-8')
    print(f"[SUCCESS] Campaign summary saved to: {campaign_file}")

# %%
# ─── Cell 4: Create Daily Performance Time Series ────────────────────────────────
if 'date' in df.columns and 'spend_usd' in df.columns:
    # Aggregate by date
    agg_dict = {}
    if 'spend_usd' in df.columns:
        agg_dict['spend_usd'] = 'sum'
    if 'impressions' in df.columns:
        agg_dict['impressions'] = 'sum'
    if 'clicks' in df.columns:
        agg_dict['clicks'] = 'sum'
    if 'reach' in df.columns:
        agg_dict['reach'] = 'sum'
    
    daily_performance = df.groupby('date').agg(agg_dict).round(2)
    
    # Calculate daily metrics
    if 'spend_usd' in daily_performance.columns and 'impressions' in daily_performance.columns:
        daily_performance['cpm'] = (daily_performance['spend_usd'] / daily_performance['impressions'] * 1000).round(2)
        daily_performance.loc[daily_performance['impressions'] == 0, 'cpm'] = 0
    
    if 'spend_usd' in daily_performance.columns and 'clicks' in daily_performance.columns:
        daily_performance['cpc'] = (daily_performance['spend_usd'] / daily_performance['clicks']).round(2)
        daily_performance.loc[daily_performance['clicks'] == 0, 'cpc'] = 0
    
    if 'clicks' in daily_performance.columns and 'impressions' in daily_performance.columns:
        daily_performance['ctr'] = (daily_performance['clicks'] / daily_performance['impressions'] * 100).round(4)
        daily_performance.loc[daily_performance['impressions'] == 0, 'ctr'] = 0
    
    # Reset index to make date a column
    daily_performance = daily_performance.reset_index()
    
    # Save daily performance
    daily_file = curated_meta / f"daily_performance_{datetime.now():%Y%m%d}.csv"
    daily_performance.to_csv(daily_file, index=False, encoding='utf-8')
    print(f"[SUCCESS] Daily performance saved to: {daily_file}")

# %%
# ─── Cell 5: Create Ad Performance Detail ────────────────────────────────────────
if 'ad_name' in df.columns or 'campaign_name' in df.columns:
    # Detailed ad-level performance
    ad_performance = df.copy()
    
    # Select relevant columns
    keep_columns = ['date', 'campaign_name', 'campaign_id', 'adset_name', 'adset_id',
                   'ad_name', 'spend_usd', 'impressions', 'clicks', 'reach',
                   'cpm', 'cpc', 'ctr', 'quality_ranking', 'engagement_ranking',
                   'conversion_ranking', 'pixel_view_content', 'pixel_purchase',
                   'pixel_add_to_cart', 'pixel_link_click']
    
    available_columns = [col for col in keep_columns if col in ad_performance.columns]
    if available_columns:
        ad_performance = ad_performance[available_columns]
        
        # Sort by date and spend
        sort_cols = []
        if 'date' in ad_performance.columns:
            sort_cols.append('date')
        if 'spend_usd' in ad_performance.columns:
            sort_cols.append('spend_usd')
        
        if sort_cols:
            ad_performance = ad_performance.sort_values(sort_cols, ascending=[False, False] if len(sort_cols) == 2 else [False])
        
        # Save ad performance
        ad_file = curated_meta / f"ad_performance_{datetime.now():%Y%m%d}.csv"
        ad_performance.to_csv(ad_file, index=False, encoding='utf-8')
        print(f"[SUCCESS] Ad performance saved to: {ad_file}")

# %%
# ─── Cell 6: Create KPI Dashboard Dataset ────────────────────────────────────────
# Create a summary dataset for dashboard/reporting
kpi_data = {
    'metric': [],
    'value': [],
    'period': []
}

# Overall KPIs
if 'spend_usd' in df.columns:
    kpi_data['metric'].append('Total Spend')
    kpi_data['value'].append(f"${df['spend_usd'].sum():,.2f}")
    kpi_data['period'].append('All Time')

if 'impressions' in df.columns:
    kpi_data['metric'].append('Total Impressions')
    kpi_data['value'].append(f"{df['impressions'].sum():,}")
    kpi_data['period'].append('All Time')

if 'clicks' in df.columns:
    kpi_data['metric'].append('Total Clicks')
    kpi_data['value'].append(f"{df['clicks'].sum():,}")
    kpi_data['period'].append('All Time')

if 'reach' in df.columns and df['reach'].notna().any():
    kpi_data['metric'].append('Total Reach')
    kpi_data['value'].append(f"{df['reach'].sum():,}")
    kpi_data['period'].append('All Time')

# Average metrics
if 'spend_usd' in df.columns and 'impressions' in df.columns and df['impressions'].sum() > 0:
    avg_cpm = (df['spend_usd'].sum() / df['impressions'].sum() * 1000)
    kpi_data['metric'].append('Average CPM')
    kpi_data['value'].append(f"${avg_cpm:.2f}")
    kpi_data['period'].append('All Time')

if 'spend_usd' in df.columns and 'clicks' in df.columns and df['clicks'].sum() > 0:
    avg_cpc = df['spend_usd'].sum() / df['clicks'].sum()
    kpi_data['metric'].append('Average CPC')
    kpi_data['value'].append(f"${avg_cpc:.2f}")
    kpi_data['period'].append('All Time')

if 'clicks' in df.columns and 'impressions' in df.columns and df['impressions'].sum() > 0:
    avg_ctr = (df['clicks'].sum() / df['impressions'].sum() * 100)
    kpi_data['metric'].append('Average CTR')
    kpi_data['value'].append(f"{avg_ctr:.2f}%")
    kpi_data['period'].append('All Time')

# Last 30 days metrics if date column exists
if 'date' in df.columns and not df['date'].isna().all():
    last_30_days = df[df['date'] >= (df['date'].max() - timedelta(days=30))]
    
    if not last_30_days.empty:
        if 'spend_usd' in last_30_days.columns:
            kpi_data['metric'].append('Last 30 Days Spend')
            kpi_data['value'].append(f"${last_30_days['spend_usd'].sum():,.2f}")
            kpi_data['period'].append('Last 30 Days')
        
        if 'impressions' in last_30_days.columns:
            kpi_data['metric'].append('Last 30 Days Impressions')
            kpi_data['value'].append(f"{last_30_days['impressions'].sum():,}")
            kpi_data['period'].append('Last 30 Days')
        
        if 'clicks' in last_30_days.columns:
            kpi_data['metric'].append('Last 30 Days Clicks')
            kpi_data['value'].append(f"{last_30_days['clicks'].sum():,}")
            kpi_data['period'].append('Last 30 Days')

# Create KPI dataframe
kpi_df = pd.DataFrame(kpi_data)

# Save KPI dataset
kpi_file = curated_meta / f"kpi_summary_{datetime.now():%Y%m%d}.csv"
kpi_df.to_csv(kpi_file, index=False, encoding='utf-8')
print(f"[SUCCESS] KPI summary saved to: {kpi_file}")

# %%
# ─── Cell 7: Create Latest Versions ──────────────────────────────────────────────
# Create "latest" versions for easy access
if campaign_summary is not None:
    campaign_summary.to_csv(curated_meta / "campaign_summary_latest.csv", encoding='utf-8')

if 'daily_performance' in locals():
    daily_performance.to_csv(curated_meta / "daily_performance_latest.csv", index=False, encoding='utf-8')

if 'ad_performance' in locals():
    ad_performance.to_csv(curated_meta / "ad_performance_latest.csv", index=False, encoding='utf-8')

kpi_df.to_csv(curated_meta / "kpi_summary_latest.csv", index=False, encoding='utf-8')

print(f"\n[SUCCESS] All 'latest' versions saved for easy access")

# %%
# ─── Cell 8: Final Summary ───────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("META ADS PIPELINE COMPLETE")
print("=" * 80)
print(f"\nCurated datasets created in: {curated_meta}")
print("\nAvailable datasets:")
print("  1. campaign_summary_latest.csv - Campaign-level aggregated metrics")
if 'daily_performance' in locals():
    print("  2. daily_performance_latest.csv - Daily time series data")
if 'ad_performance' in locals():
    print("  3. ad_performance_latest.csv - Detailed ad-level performance")
print("  4. kpi_summary_latest.csv - Key performance indicators")

# Print key metrics
print("\nKey Metrics:")
if 'spend_usd' in df.columns:
    print(f"  Total Spend: ${df['spend_usd'].sum():,.2f}")
if 'impressions' in df.columns:
    print(f"  Total Impressions: {df['impressions'].sum():,}")
if 'clicks' in df.columns:
    print(f"  Total Clicks: {df['clicks'].sum():,}")

if 'date' in df.columns and not df['date'].isna().all():
    print(f"\nDate Range: {df['date'].min().date()} to {df['date'].max().date()}")

print("\n" + "=" * 80)