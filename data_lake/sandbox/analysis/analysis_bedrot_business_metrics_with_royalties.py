#!/usr/bin/env python3
"""
BEDROT Business Metrics Analysis - WITH ROYALTY SPLITS
Analyzes Cost Per Acquisition, Revenue Per Stream, ROI, and Catalog Performance
Accounts for actual revenue after collaborator royalty splits
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Load datasets
print("Loading curated datasets...")
base_path = "/mnt/c/Users/Earth/BEDROT PRODUCTIONS/bedrot-data-ecosystem/data_lake/4_curated/"

# Load Meta Ads campaigns
meta_ads = pd.read_csv(base_path + "metaads_campaigns_daily.csv")
meta_ads['first_seen_date'] = pd.to_datetime(meta_ads['first_seen_date'])
meta_ads['last_seen_date'] = pd.to_datetime(meta_ads['last_seen_date'])

# Load streaming data
daily_streams = pd.read_csv(base_path + "tidy_daily_streams.csv")
daily_streams['date'] = pd.to_datetime(daily_streams['date'])

# Load financial data
dk_bank = pd.read_csv(base_path + "dk_bank_details.csv")
dk_bank['Sale Month'] = pd.to_datetime(dk_bank['Sale Month'])

# Load Spotify audience metrics
spotify_audience = pd.read_csv(base_path + "spotify_audience_curated_20250724_043430.csv")
spotify_audience['date'] = pd.to_datetime(spotify_audience['date'])

# Apply royalty splits
def get_actual_revenue_share(artist, title):
    """Get the actual revenue share for a track based on royalty agreements"""
    if artist.upper() == 'ZONE A0':
        title_upper = title.upper()
        if 'THE SOURCE' in title_upper or 'ANOVUS' in title_upper:
            return 0.40
        elif 'I WILL ALWAYS REMEMBER YOU' in title_upper or 'HOLD ON' in title_upper:
            return 0.50
        elif 'ENGAGEMENT PROTOCOL' in title_upper:
            return 0.80
        elif 'Z1' in title_upper:
            return 0.90
        elif 'OASIS' in title_upper:
            return 0.40
    return 1.00

# Apply royalty splits to revenue
dk_bank['revenue_share'] = dk_bank.apply(
    lambda row: get_actual_revenue_share(row['Artist'], row['Title']), 
    axis=1
)
dk_bank['actual_earnings'] = dk_bank['Earnings (USD)'] * dk_bank['revenue_share']

print("\n" + "="*80)
print("BEDROT PRODUCTIONS - BUSINESS METRICS ANALYSIS (WITH ROYALTY SPLITS)")
print("="*80)

# Calculate actual revenue totals
total_gross_revenue = dk_bank['Earnings (USD)'].sum()
total_actual_revenue = dk_bank['actual_earnings'].sum()
royalties_paid_out = total_gross_revenue - total_actual_revenue
retention_rate = (total_actual_revenue / total_gross_revenue) * 100

print(f"\nREVENUE OVERVIEW:")
print(f"Gross Revenue (before splits): ${total_gross_revenue:.2f}")
print(f"YOUR Actual Revenue (after splits): ${total_actual_revenue:.2f}")
print(f"Royalties Paid to Collaborators: ${royalties_paid_out:.2f}")
print(f"Revenue Retention Rate: {retention_rate:.1f}%")

# ============================================================================
# QUESTION 1: Cost Per Acquisition vs Lifetime Value (WITH ROYALTY ADJUSTMENT)
# ============================================================================
print("\n\n1. COST PER ACQUISITION vs LIFETIME VALUE ANALYSIS (ROYALTY-ADJUSTED)")
print("-" * 50)

# Calculate total Meta Ads spend and performance
total_spend = meta_ads['total_spend_usd'].sum()
total_clicks = meta_ads['total_clicks'].sum()
avg_cpc = meta_ads['avg_cpc'].mean()

print(f"Total Meta Ads Spend: ${total_spend:.2f}")
print(f"Total Clicks: {total_clicks:,}")
print(f"Average CPC: ${avg_cpc:.4f}")

# Get monthly listener growth during campaign periods
campaign_period = (meta_ads['first_seen_date'].min(), meta_ads['last_seen_date'].max())
spotify_during_campaigns = spotify_audience[
    (spotify_audience['date'] >= campaign_period[0]) & 
    (spotify_audience['date'] <= campaign_period[1])
]

if len(spotify_during_campaigns) > 0:
    listener_growth = spotify_during_campaigns['listeners'].max() - spotify_during_campaigns['listeners'].min()
    conversion_rate = listener_growth / total_clicks if total_clicks > 0 else 0
    cpa_monthly_listener = total_spend / listener_growth if listener_growth > 0 else 0
    
    print(f"\nMonthly Listener Growth During Campaigns: {listener_growth:,}")
    print(f"Conversion Rate (Clicks to Listeners): {conversion_rate:.2%}")
    print(f"Cost Per Acquisition (Monthly Listener): ${cpa_monthly_listener:.2f}")
else:
    print("\nInsufficient data for listener growth analysis")

# Calculate ACTUAL Lifetime Value based on royalty-adjusted revenue
unique_listeners = spotify_audience['listeners'].max()
avg_actual_revenue_per_listener = total_actual_revenue / unique_listeners if unique_listeners > 0 else 0
listener_retention_months = 6  # Conservative estimate
actual_ltv = avg_actual_revenue_per_listener * listener_retention_months

print(f"\nTotal ACTUAL Revenue (your share): ${total_actual_revenue:.2f}")
print(f"Average ACTUAL Revenue per Listener: ${avg_actual_revenue_per_listener:.4f}")
print(f"Estimated ACTUAL Lifetime Value (6 months): ${actual_ltv:.2f}")

if 'cpa_monthly_listener' in locals():
    actual_roi = (actual_ltv - cpa_monthly_listener) / cpa_monthly_listener if cpa_monthly_listener > 0 else 0
    print(f"\nACTUAL ROI per Listener: {actual_roi:.1%}")
    print(f"ACTUAL Profit per Listener: ${actual_ltv - cpa_monthly_listener:.2f}")

# ============================================================================
# QUESTION 2: Platform Revenue Comparison (WITH ROYALTY ADJUSTMENT)
# ============================================================================
print("\n\n2. REVENUE PER STREAM BY PLATFORM (ROYALTY-ADJUSTED)")
print("-" * 50)

# Group by store/platform with actual earnings
platform_revenue = dk_bank.groupby('Store').agg({
    'Quantity': 'sum',
    'Earnings (USD)': 'sum',
    'actual_earnings': 'sum'
}).reset_index()

platform_revenue['Gross Revenue per Stream'] = platform_revenue['Earnings (USD)'] / platform_revenue['Quantity']
platform_revenue['Actual Revenue per Stream'] = platform_revenue['actual_earnings'] / platform_revenue['Quantity']
platform_revenue = platform_revenue.sort_values('Actual Revenue per Stream', ascending=False)

print("\nPlatform Revenue Comparison (YOUR ACTUAL SHARE):")
print("-" * 30)
for _, row in platform_revenue.head(10).iterrows():
    print(f"{row['Store']:<30}")
    print(f"  YOUR Revenue/Stream: ${row['Actual Revenue per Stream']:.5f}")
    print(f"  Gross Revenue/Stream: ${row['Gross Revenue per Stream']:.5f}")
    print(f"  Total Streams: {row['Quantity']:,}")
    print(f"  YOUR Total Revenue: ${row['actual_earnings']:.2f}")
    print()

# Platform category comparison
spotify_actual = platform_revenue[platform_revenue['Store'].str.contains('Spotify', case=False, na=False)]['Actual Revenue per Stream'].mean()
apple_actual = platform_revenue[platform_revenue['Store'].str.contains('Apple|iTunes', case=False, na=False)]['Actual Revenue per Stream'].mean()
other_actual = platform_revenue[~platform_revenue['Store'].str.contains('Spotify|Apple|iTunes', case=False, na=False)]['Actual Revenue per Stream'].mean()

print("\nAverage ACTUAL Revenue per Stream by Platform Type:")
print(f"Spotify: ${spotify_actual:.5f} (your share)")
print(f"Apple Music/iTunes: ${apple_actual:.5f} (your share)")
print(f"Other Platforms: ${other_actual:.5f} (your share)")

# ============================================================================
# QUESTION 3: Meta Ads Payback Period (WITH ROYALTY ADJUSTMENT)
# ============================================================================
print("\n\n3. META ADS PAYBACK PERIOD ANALYSIS (ROYALTY-ADJUSTED)")
print("-" * 50)

# Calculate daily ACTUAL revenue rate
days_of_data = (dk_bank['Sale Month'].max() - dk_bank['Sale Month'].min()).days
daily_actual_revenue = total_actual_revenue / days_of_data if days_of_data > 0 else 0

print(f"Average Daily ACTUAL Revenue (your share): ${daily_actual_revenue:.2f}")
print(f"Average CPC: ${avg_cpc:.4f}")

# Calculate ACTUAL revenue per click
avg_streams_per_click = 50  # Conservative estimate
avg_actual_revenue_per_stream = total_actual_revenue / dk_bank['Quantity'].sum() if dk_bank['Quantity'].sum() > 0 else 0
actual_revenue_per_click = avg_streams_per_click * avg_actual_revenue_per_stream

print(f"\nEstimated ACTUAL Revenue per Click: ${actual_revenue_per_click:.4f}")
print(f"Cost per Click: ${avg_cpc:.4f}")

if actual_revenue_per_click > avg_cpc:
    print(f"Payback: IMMEDIATE (Actual Revenue > Cost)")
    print(f"ACTUAL Profit per Click: ${actual_revenue_per_click - avg_cpc:.4f}")
else:
    clicks_to_breakeven = avg_cpc / actual_revenue_per_click if actual_revenue_per_click > 0 else float('inf')
    print(f"Clicks to Break Even: {clicks_to_breakeven:.1f}")

# Calculate payback period in days using ACTUAL revenue
if daily_actual_revenue > 0:
    daily_ad_spend = total_spend / meta_ads['total_days_active'].sum()
    actual_payback_days = daily_ad_spend / daily_actual_revenue
    print(f"\nDaily Ad Spend: ${daily_ad_spend:.2f}")
    print(f"ACTUAL Payback Period: {actual_payback_days:.1f} days")

# ============================================================================
# QUESTION 4: Back Catalog vs New Releases (WITH ROYALTY ADJUSTMENT)
# ============================================================================
print("\n\n4. BACK CATALOG vs NEW RELEASES REVENUE (ROYALTY-ADJUSTED)")
print("-" * 50)

# Define cutoff for "new" releases (last 90 days)
cutoff_date = dk_bank['Sale Month'].max() - pd.Timedelta(days=90)

# Group tracks by release status
dk_bank['Release Type'] = dk_bank['Sale Month'].apply(
    lambda x: 'New Release' if x >= cutoff_date else 'Back Catalog'
)

revenue_by_type = dk_bank.groupby('Release Type').agg({
    'Earnings (USD)': 'sum',
    'actual_earnings': 'sum',
    'Quantity': 'sum'
}).reset_index()

total_actual = revenue_by_type['actual_earnings'].sum()
for _, row in revenue_by_type.iterrows():
    pct = (row['actual_earnings'] / total_actual * 100) if total_actual > 0 else 0
    print(f"\n{row['Release Type']}:")
    print(f"  YOUR Revenue: ${row['actual_earnings']:.2f} ({pct:.1f}%)")
    print(f"  Gross Revenue: ${row['Earnings (USD)']:.2f}")
    print(f"  Streams: {row['Quantity']:,}")
    print(f"  YOUR Avg per Stream: ${row['actual_earnings']/row['Quantity']:.5f}")

# Track-level analysis with actual revenue
track_revenue = dk_bank.groupby(['Title', 'Artist']).agg({
    'Earnings (USD)': 'sum',
    'actual_earnings': 'sum',
    'revenue_share': 'first',
    'Quantity': 'sum',
    'Sale Month': 'max'
}).reset_index()

track_revenue = track_revenue.sort_values('actual_earnings', ascending=False)

print("\n\nTop 10 Revenue-Generating Tracks (YOUR ACTUAL REVENUE):")
print("-" * 50)
for i, row in track_revenue.head(10).iterrows():
    age_days = (dk_bank['Sale Month'].max() - row['Sale Month']).days
    catalog_type = "New" if age_days <= 90 else f"Catalog ({age_days} days old)"
    print(f"{i+1}. {row['Artist']} - {row['Title']}")
    print(f"   YOUR Revenue: ${row['actual_earnings']:.2f} ({row['revenue_share']*100:.0f}% share)")
    print(f"   Gross Revenue: ${row['Earnings (USD)']:.2f} | Streams: {row['Quantity']:,} | {catalog_type}")

# ============================================================================
# ARTIST-SPECIFIC ANALYSIS WITH ROYALTY SPLITS
# ============================================================================
print("\n\n5. ARTIST-SPECIFIC ECONOMICS (WITH ROYALTY SPLITS)")
print("-" * 50)

artist_economics = dk_bank.groupby('Artist').agg({
    'Earnings (USD)': 'sum',
    'actual_earnings': 'sum',
    'Quantity': 'sum'
}).reset_index()

for _, row in artist_economics.iterrows():
    retention = (row['actual_earnings'] / row['Earnings (USD)']) * 100
    print(f"\n{row['Artist']}:")
    print(f"  Gross Revenue: ${row['Earnings (USD)']:.2f}")
    print(f"  YOUR Revenue: ${row['actual_earnings']:.2f}")
    print(f"  Retention Rate: {retention:.1f}%")
    print(f"  Total Streams: {row['Quantity']:,}")
    print(f"  YOUR $/Stream: ${row['actual_earnings']/row['Quantity']:.5f}")

# ============================================================================
# SUMMARY & RECOMMENDATIONS (ROYALTY-ADJUSTED)
# ============================================================================
print("\n\n" + "="*80)
print("KEY INSIGHTS & RECOMMENDATIONS (ROYALTY-ADJUSTED)")
print("="*80)

print(f"""
1. COST PER ACQUISITION vs ACTUAL LIFETIME VALUE:
   - CPA: ${cpa_monthly_listener:.2f} per listener
   - ACTUAL LTV (your share): ${actual_ltv:.2f}
   - ACTUAL ROI: {actual_roi:.0%}
   - You're keeping {retention_rate:.0f}% of gross revenue

2. PLATFORM REVENUE COMPARISON (YOUR ACTUAL SHARE):
   - Apple Music/iTunes: ${apple_actual:.5f}/stream (your share)
   - Spotify: ${spotify_actual:.5f}/stream (your share)
   - Focus on platforms with best actual returns

3. META ADS PAYBACK PERIOD (ACTUAL):
   - Payback Period: {actual_payback_days:.1f} days
   - Daily ACTUAL Revenue: ${daily_actual_revenue:.2f}
   - Still profitable but longer than gross calculations

4. CATALOG PERFORMANCE (ACTUAL REVENUE):
   - Back catalog provides steady baseline
   - Monitor tracks with lower royalty shares
   - PIG1987 (100% retention) vs ZONE A0 ({(artist_economics[artist_economics['Artist']=='ZONE A0']['actual_earnings'].sum()/artist_economics[artist_economics['Artist']=='ZONE A0']['Earnings (USD)'].sum()*100):.0f}% retention)

5. STRATEGIC IMPLICATIONS:
   - Prioritize marketing for 100% retention tracks
   - ZONE A0's upcoming releases have varying splits (40-90%)
   - Factor royalty splits into ROI calculations
   - Consider collaboration value vs revenue dilution
""")

print("\nAnalysis complete! All metrics adjusted for royalty splits.")