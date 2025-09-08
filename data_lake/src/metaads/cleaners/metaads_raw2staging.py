# %%
# ─── Cell 1: Imports & Environment Setup ────────────────────────────────────────
# Process Meta Ads NDJSON files from raw zone and create normalized CSV in staging
import os
import json
from pathlib import Path
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT"))
RAW = PROJECT_ROOT / os.getenv("RAW_ZONE", "2_raw")
STAGING = PROJECT_ROOT / os.getenv("STAGING_ZONE", "3_staging")

# %%
# ─── Cell 2: Load and Combine NDJSON Files ──────────────────────────────────────
raw_meta = RAW / "metaads"
staging_meta = STAGING / "metaads"
staging_meta.mkdir(parents=True, exist_ok=True)

# Find all NDJSON files
ndjson_files = list(raw_meta.glob("*.ndjson"))

if not ndjson_files:
    print(f"[WARNING] No NDJSON files found in {raw_meta}")
    exit(1)

print(f"[INFO] Found {len(ndjson_files)} NDJSON files to process")

# %%
# ─── Cell 3: Read and Combine Data ───────────────────────────────────────────────
all_data = []

for ndjson_file in sorted(ndjson_files):
    try:
        with open(ndjson_file, 'r', encoding='utf-8') as f:
            file_data = []
            for line in f:
                if line.strip():  # Skip empty lines
                    try:
                        record = json.loads(line)
                        file_data.append(record)
                    except json.JSONDecodeError as e:
                        print(f"[WARNING] Skipping invalid JSON line in {ndjson_file.name}: {e}")
                        continue
            
            if file_data:
                print(f"[LOADED] {ndjson_file.name} - {len(file_data)} records")
                all_data.extend(file_data)
                
    except Exception as e:
        print(f"[ERROR] Failed to read {ndjson_file.name}: {e}")
        continue

if not all_data:
    print("[ERROR] No data loaded from NDJSON files")
    exit(1)

print(f"\n[INFO] Total records loaded: {len(all_data)}")

# %%
# ─── Cell 4: Create DataFrame and Normalize ──────────────────────────────────────
df = pd.DataFrame(all_data)

# Remove duplicate columns (keep first occurrence)
df = df.loc[:, ~df.columns.duplicated()]

print(f"[INFO] DataFrame shape: {df.shape}")
print(f"[INFO] Columns: {df.columns.tolist()}")

# %%
# ─── Cell 5: Data Cleaning and Standardization ───────────────────────────────────
# Standardize column names
column_mapping = {
    'Amount spent (USD)': 'spend_usd',
    'Reporting starts': 'date_start',
    'Reporting ends': 'date_end',
    'Ad name': 'ad_name',
    'Ad Set Name': 'adset_name',
    'Ad delivery': 'ad_delivery_status',
    'Impressions': 'impressions',
    'Reach': 'reach',
    'Clicks': 'clicks',
    'Results': 'results',
    'Cost per results': 'cost_per_result',
    'Quality ranking': 'quality_ranking',
    'Engagement rate ranking': 'engagement_ranking',
    'Conversion rate ranking': 'conversion_ranking',
    'Attribution setting': 'attribution_setting',
    'Result indicator': 'result_indicator',
    'Bid': 'bid',
    'Bid type': 'bid_type',
    'Ad set budget': 'adset_budget',
    'Ad set budget type': 'budget_type',
    'Last significant edit': 'last_edit',
    'Ends': 'campaign_end_status'
}

# Apply column mapping
for old_col, new_col in column_mapping.items():
    if old_col in df.columns:
        df.rename(columns={old_col: new_col}, inplace=True)

# %%
# ─── Cell 6: Type Conversions and Calculations ──────────────────────────────────
# Convert numeric columns
numeric_columns = ['spend_usd', 'impressions', 'reach', 'clicks', 'results', 
                  'cost_per_result', 'bid', 'cpc', 'cpm', 'ctr', 'frequency']

for col in numeric_columns:
    if col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        except TypeError:
            # Skip columns that can't be converted
            continue

# Convert date columns
date_columns = ['date', 'date_start', 'date_end', 'last_edit']
for col in date_columns:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

# Calculate derived metrics if not present
try:
    if 'cpm' not in df.columns and 'spend_usd' in df.columns and 'impressions' in df.columns:
        df['cpm'] = (df['spend_usd'] / df['impressions'] * 1000).fillna(0).round(2)
        df.loc[df['impressions'] == 0, 'cpm'] = 0
except:
    pass

try:
    if 'cpc' not in df.columns and 'spend_usd' in df.columns and 'clicks' in df.columns:
        df['cpc'] = (df['spend_usd'] / df['clicks']).fillna(0).round(2)
        df.loc[df['clicks'] == 0, 'cpc'] = 0
except:
    pass

try:
    if 'ctr' not in df.columns and 'clicks' in df.columns and 'impressions' in df.columns:
        df['ctr'] = (df['clicks'] / df['impressions'] * 100).fillna(0).round(4)
        df.loc[df['impressions'] == 0, 'ctr'] = 0
except:
    pass

# %%
# ─── Cell 7: Parse Meta Pixel Events ─────────────────────────────────────────────
def parse_pixel_events(events_str):
    """Parse Meta Pixel events from JSON string"""
    if pd.isna(events_str) or events_str == '{}' or not events_str:
        return {}
    
    try:
        if isinstance(events_str, str):
            return json.loads(events_str)
        else:
            return events_str
    except:
        return {}

if 'meta_pixel_events' in df.columns:
    # Parse events and create summary columns
    df['pixel_events_parsed'] = df['meta_pixel_events'].apply(parse_pixel_events)
    
    # Extract common events as separate columns
    df['pixel_view_content'] = df['pixel_events_parsed'].apply(
        lambda x: x.get('ViewContent', 0) if x else 0
    )
    df['pixel_purchase'] = df['pixel_events_parsed'].apply(
        lambda x: x.get('Purchase', 0) if x else 0
    )
    df['pixel_add_to_cart'] = df['pixel_events_parsed'].apply(
        lambda x: x.get('AddToCart', 0) if x else 0
    )
    df['pixel_link_click'] = df['pixel_events_parsed'].apply(
        lambda x: x.get('LinkClick', 0) if x else 0
    )
    
    # Drop the parsed column (keep original JSON string)
    df.drop('pixel_events_parsed', axis=1, inplace=True)

# %%
# ─── Cell 8: Data Quality and Deduplication ──────────────────────────────────────
# Remove duplicates based on key columns
key_columns = []
if 'date' in df.columns:
    key_columns.append('date')
if 'campaign_id' in df.columns:
    key_columns.append('campaign_id')
if 'adset_id' in df.columns:
    key_columns.append('adset_id')
if 'ad_name' in df.columns and 'campaign_id' not in df.columns:
    key_columns.append('ad_name')

if key_columns:
    before_dedup = len(df)
    df = df.drop_duplicates(subset=key_columns, keep='last')
    after_dedup = len(df)
    print(f"[INFO] Deduplication: {before_dedup} -> {after_dedup} records (removed {before_dedup - after_dedup})")

# Sort by date if available
if 'date' in df.columns:
    df = df.sort_values('date', ascending=False)
elif 'date_start' in df.columns:
    df = df.sort_values('date_start', ascending=False)

# %%
# ─── Cell 9: Save to Staging Zone ────────────────────────────────────────────────
# Save main dataset
output_file = staging_meta / f"metaads_staging_{datetime.now():%Y%m%d_%H%M%S}.csv"
df.to_csv(output_file, index=False, encoding='utf-8')

print(f"\n[SUCCESS] Saved {len(df)} records to {output_file}")

# Also save a 'latest' version for easy access
latest_file = staging_meta / "metaads_staging_latest.csv"
df.to_csv(latest_file, index=False, encoding='utf-8')
print(f"[SUCCESS] Also saved as latest: {latest_file}")

# %%
# ─── Cell 10: Data Summary ───────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("DATA SUMMARY")
print("=" * 80)

# Basic statistics
if 'spend_usd' in df.columns:
    try:
        total_spend = df['spend_usd'].sum()
        avg_spend = df['spend_usd'].mean()
        print(f"Total Spend: ${total_spend:,.2f}")
        print(f"Average Daily Spend: ${avg_spend:,.2f}")
    except:
        pass

if 'impressions' in df.columns:
    try:
        total_impressions = df['impressions'].sum()
        print(f"Total Impressions: {total_impressions:,}")
    except:
        pass

if 'clicks' in df.columns:
    try:
        total_clicks = df['clicks'].sum()
        print(f"Total Clicks: {total_clicks:,}")
    except:
        pass

if 'date' in df.columns:
    print(f"Date Range: {df['date'].min()} to {df['date'].max()}")
elif 'date_start' in df.columns:
    print(f"Date Range: {df['date_start'].min()} to {df['date_start'].max()}")

# Campaign summary if available
if 'campaign_name' in df.columns:
    print(f"\nUnique Campaigns: {df['campaign_name'].nunique()}")
    top_campaigns = df.groupby('campaign_name')['spend_usd'].sum().nlargest(5).reset_index()
    print("\nTop 5 Campaigns by Spend:")
    for _, row in top_campaigns.iterrows():
        campaign = row['campaign_name']
        spend = row['spend_usd']
        print(f"  - {campaign}: ${spend:,.2f}")

print("\n" + "=" * 80)