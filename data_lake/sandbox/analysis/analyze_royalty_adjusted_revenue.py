#!/usr/bin/env python3
"""
Analyze BEDROT revenue with royalty splits applied
Shows actual take-home revenue after collaborator splits
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Load datasets
print("Loading data...")
base_path = "4_curated/"

# Load financial data
dk_bank = pd.read_csv(base_path + "dk_bank_details.csv")
dk_bank['Sale Month'] = pd.to_datetime(dk_bank['Sale Month'])

# Load track catalog with royalty splits
track_catalog = pd.read_csv(base_path + "track_catalog_royalty_splits.csv")

# Create a mapping of royalty splits
royalty_map = {}
for _, row in track_catalog.iterrows():
    # Create key from artist and title (normalized)
    key = f"{row['artist'].upper()}_{row['title'].upper()}"
    royalty_map[key] = row['your_revenue_share'] / 100  # Convert percentage to decimal

# Apply royalty splits to actual revenue
def get_actual_revenue_share(artist, title):
    """Get the actual revenue share for a track"""
    # Normalize the key
    key = f"{artist.upper()}_{title.upper()}"
    
    # Special handling for specific ZONE A0 tracks
    if artist.upper() == 'ZONE A0':
        if 'THE SOURCE' in title.upper() or 'ANOVUS' in title.upper():
            return 0.40
        elif 'I WILL ALWAYS REMEMBER YOU' in title.upper() or 'HOLD ON' in title.upper():
            return 0.50
        elif 'ENGAGEMENT PROTOCOL' in title.upper():
            return 0.80
        elif 'Z1' in title.upper():
            return 0.90
        elif 'OASIS' in title.upper():
            return 0.40
    
    # Default: 100% for all other tracks
    return 1.00

# Apply royalty splits
dk_bank['revenue_share'] = dk_bank.apply(
    lambda row: get_actual_revenue_share(row['Artist'], row['Title']), 
    axis=1
)
dk_bank['actual_earnings'] = dk_bank['Earnings (USD)'] * dk_bank['revenue_share']

print("\n" + "="*80)
print("ROYALTY-ADJUSTED REVENUE ANALYSIS")
print("="*80)

# Summary statistics
total_gross_revenue = dk_bank['Earnings (USD)'].sum()
total_actual_revenue = dk_bank['actual_earnings'].sum()
total_royalties_paid = total_gross_revenue - total_actual_revenue

print(f"\nGross Revenue (before splits): ${total_gross_revenue:.2f}")
print(f"Actual Revenue (after splits): ${total_actual_revenue:.2f}")
print(f"Royalties Paid to Collaborators: ${total_royalties_paid:.2f}")
print(f"Your Revenue Retention: {(total_actual_revenue/total_gross_revenue)*100:.1f}%")

# Artist breakdown
print("\n" + "-"*50)
print("REVENUE BY ARTIST (After Royalty Splits):")
print("-"*50)

artist_revenue = dk_bank.groupby('Artist').agg({
    'Earnings (USD)': 'sum',
    'actual_earnings': 'sum',
    'Quantity': 'sum'
}).round(2)

for artist in artist_revenue.index:
    gross = artist_revenue.loc[artist, 'Earnings (USD)']
    actual = artist_revenue.loc[artist, 'actual_earnings']
    streams = artist_revenue.loc[artist, 'Quantity']
    retention = (actual/gross)*100 if gross > 0 else 100
    
    print(f"\n{artist}:")
    print(f"  Gross Revenue: ${gross:.2f}")
    print(f"  Your Revenue: ${actual:.2f}")
    print(f"  Retention Rate: {retention:.1f}%")
    print(f"  Total Streams: {streams:,}")

# Track-level analysis with royalty splits
print("\n" + "-"*50)
print("TOP TRACKS BY ACTUAL REVENUE (Your Share):")
print("-"*50)

track_revenue = dk_bank.groupby(['Artist', 'Title']).agg({
    'Earnings (USD)': 'sum',
    'actual_earnings': 'sum',
    'revenue_share': 'first',
    'Quantity': 'sum'
}).reset_index()

track_revenue = track_revenue.sort_values('actual_earnings', ascending=False)

print("\nTop 15 Tracks (Your Actual Revenue):")
for i, row in track_revenue.head(15).iterrows():
    print(f"\n{i+1}. {row['Artist']} - {row['Title'][:40]}")
    print(f"   Gross: ${row['Earnings (USD)']:.2f} | Your Share: ${row['actual_earnings']:.2f} ({row['revenue_share']*100:.0f}%)")
    print(f"   Streams: {row['Quantity']:,}")

# Identify tracks with splits
tracks_with_splits = track_revenue[track_revenue['revenue_share'] < 1.0]
if len(tracks_with_splits) > 0:
    print("\n" + "-"*50)
    print("TRACKS WITH ROYALTY SPLITS:")
    print("-"*50)
    for _, row in tracks_with_splits.iterrows():
        print(f"\n{row['Artist']} - {row['Title']}")
        print(f"  Your Share: {row['revenue_share']*100:.0f}%")
        print(f"  Gross Revenue: ${row['Earnings (USD)']:.2f}")
        print(f"  Your Revenue: ${row['actual_earnings']:.2f}")
        print(f"  Paid to Collaborators: ${row['Earnings (USD)'] - row['actual_earnings']:.2f}")

# Monthly trend with actual revenue
print("\n" + "-"*50)
print("MONTHLY REVENUE TREND (Actual vs Gross):")
print("-"*50)

monthly_revenue = dk_bank.groupby(pd.Grouper(key='Sale Month', freq='M')).agg({
    'Earnings (USD)': 'sum',
    'actual_earnings': 'sum'
}).reset_index()

for _, row in monthly_revenue.iterrows():
    if row['Earnings (USD)'] > 0:
        retention = (row['actual_earnings']/row['Earnings (USD)'])*100
        print(f"{row['Sale Month'].strftime('%Y-%m')}: Gross ${row['Earnings (USD)']:6.2f} | Actual ${row['actual_earnings']:6.2f} ({retention:.0f}%)")

# Platform analysis with actual revenue
print("\n" + "-"*50)
print("PLATFORM REVENUE (After Royalty Splits):")
print("-"*50)

platform_revenue = dk_bank.groupby('Store').agg({
    'Earnings (USD)': 'sum',
    'actual_earnings': 'sum',
    'Quantity': 'sum'
}).reset_index()

platform_revenue['actual_per_stream'] = platform_revenue['actual_earnings'] / platform_revenue['Quantity']
platform_revenue = platform_revenue.sort_values('actual_earnings', ascending=False)

for _, row in platform_revenue.head(10).iterrows():
    print(f"\n{row['Store'][:30]}:")
    print(f"  Your Revenue: ${row['actual_earnings']:.2f}")
    print(f"  Your $/Stream: ${row['actual_per_stream']:.5f}")
    print(f"  Streams: {row['Quantity']:,}")

# Future releases impact
print("\n" + "="*80)
print("FUTURE RELEASE REVENUE IMPACT")
print("="*80)

future_releases = [
    ("ZONE A0", "THE SOURCE", 40, "2025-05-02"),
    ("ZONE A0", "ANOVUS", 40, "2025-05-02"),
    ("ZONE A0", "I WILL ALWAYS REMEMBER YOU", 50, "2025-05-30"),
    ("ZONE A0", "ENGAGEMENT PROTOCOL", 80, "2025-07-11"),
    ("ZONE A0", "Z1", 90, "2025-08-08"),
    ("ZONE A0", "OASIS", 40, "2025-09-05"),
    ("ZONE A0", "BLACK BOX (Album)", 100, "2025-10-24"),
]

print("\nUpcoming releases with royalty considerations:")
for artist, title, share, date in future_releases:
    print(f"\n{date}: {artist} - {title}")
    print(f"  Your Revenue Share: {share}%")
    if share < 100:
        print(f"  ⚠️ Note: {100-share}% goes to collaborators")

# Key insights
print("\n" + "="*80)
print("KEY INSIGHTS - ROYALTY IMPACT")
print("="*80)

retention_rate = (total_actual_revenue/total_gross_revenue)*100

print(f"""
1. OVERALL REVENUE RETENTION: {retention_rate:.1f}%
   - You keep ${total_actual_revenue:.2f} of ${total_gross_revenue:.2f} gross revenue
   - This is {'excellent' if retention_rate > 90 else 'good' if retention_rate > 75 else 'concerning'}

2. ARTIST COMPARISON:
   - PIG1987: {(artist_revenue.loc['PIG1987', 'actual_earnings']/artist_revenue.loc['PIG1987', 'Earnings (USD)'])*100:.0f}% retention
   - ZONE A0: {(artist_revenue.loc['ZONE A0', 'actual_earnings']/artist_revenue.loc['ZONE A0', 'Earnings (USD)'])*100:.0f}% retention

3. FUTURE RELEASE STRATEGY:
   - Several ZONE A0 releases have lower revenue shares (40-50%)
   - Consider this in marketing budget allocation
   - Focus promotion on high-retention tracks (80-100% share)

4. COLLABORATION ECONOMICS:
   - Collaborations can expand reach but reduce per-stream revenue
   - Balance between audience growth and revenue retention
""")

print("\nAnalysis complete! Royalty splits have been applied to all revenue calculations.")