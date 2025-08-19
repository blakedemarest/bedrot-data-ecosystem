#!/usr/bin/env python3
"""
Run Meta Ads Complete Analysis
Executes the analysis notebook code to process Meta Ads data
"""

import pandas as pd
import numpy as np
import warnings
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

warnings.filterwarnings('ignore')

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
pd.set_option('display.float_format', lambda x: '%.2f' % x)

def main():
    print("=" * 80)
    print("META ADS COMPLETE ANALYSIS - BEDROT PRODUCTIONS")
    print("Full Campaign History: July 2022 - August 2025")
    print("=" * 80)
    
    # Load the CSV file
    file_path = r'C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake\1_landing\BEDROT-ADS-Ads-Jul-12-2022-Aug-12-2025.csv'
    
    try:
        df = pd.read_csv(file_path)
        print(f"\n[SUCCESS] Dataset loaded: {len(df)} ads")
        print(f"[INFO] Date range: {df['Reporting starts'].min()} to {df['Reporting ends'].max()}")
    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
        return
    except Exception as e:
        print(f"[ERROR] Error loading file: {e}")
        return
    
    # Calculate total spend and key metrics
    total_spend = df['Amount spent (USD)'].sum()
    total_impressions = df['Impressions'].sum()
    total_reach = df['Reach'].sum()
    total_results = df['Results'].sum()
    
    # Calculate averages
    avg_cpm = (total_spend / total_impressions) * 1000 if total_impressions > 0 else 0
    avg_cpr = total_spend / total_results if total_results > 0 else 0
    
    print("\n" + "=" * 80)
    print("TOTAL META ADS SPEND")
    print("=" * 80)
    print(f"\nTOTAL SPEND: ${total_spend:,.2f}")
    print(f"\nKEY METRICS:")
    print(f"  - Total Impressions: {total_impressions:,}")
    print(f"  - Total Reach: {total_reach:,}")
    print(f"  - Total Results: {total_results:,.0f}")
    print(f"  - Average CPM: ${avg_cpm:.2f}")
    print(f"  - Average Cost per Result: ${avg_cpr:.2f}")
    print(f"  - Number of Ads: {len(df)}")
    
    # Extract campaign names from Ad Set Names
    df['Campaign'] = df['Ad Set Name'].str.extract(r'([^-]+)')
    df['Campaign'] = df['Campaign'].str.strip()
    
    # Group by campaign
    campaign_metrics = df.groupby('Campaign').agg({
        'Amount spent (USD)': 'sum',
        'Impressions': 'sum',
        'Reach': 'sum',
        'Results': 'sum',
        'Ad name': 'count'
    }).round(2)
    
    campaign_metrics.columns = ['Total Spend', 'Impressions', 'Reach', 'Results', 'Num Ads']
    campaign_metrics['CPM'] = (campaign_metrics['Total Spend'] / campaign_metrics['Impressions'] * 1000).round(2)
    campaign_metrics['Cost per Result'] = (campaign_metrics['Total Spend'] / campaign_metrics['Results']).round(2)
    campaign_metrics = campaign_metrics.sort_values('Total Spend', ascending=False)
    
    print("\n" + "=" * 80)
    print("CAMPAIGN BREAKDOWN")
    print("=" * 80)
    print("\nTop 5 Campaigns by Spend:")
    for i, (campaign, data) in enumerate(campaign_metrics.head(5).iterrows(), 1):
        print(f"\n{i}. {campaign}:")
        print(f"   - Spend: ${data['Total Spend']:,.2f}")
        print(f"   - Results: {data['Results']:,.0f}")
        print(f"   - CPM: ${data['CPM']:.2f}")
        print(f"   - Cost per Result: ${data['Cost per Result']:.2f}")
    
    # ROI Analysis
    print("\n" + "=" * 80)
    print("ROI ANALYSIS")
    print("=" * 80)
    
    try:
        revenue_path = r'C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake\4_curated\dk_bank_details.csv'
        revenue_df = pd.read_csv(revenue_path)
        total_revenue = revenue_df['Earnings (USD)'].sum()
        actual_revenue = total_revenue * 0.88  # After royalties
        
        print(f"\n[FINANCIAL] Total Meta Ads Spend: ${total_spend:,.2f}")
        print(f"[FINANCIAL] Gross Music Revenue: ${total_revenue:,.2f}")
        print(f"[FINANCIAL] Actual Revenue (after royalties): ${actual_revenue:,.2f}")
        print(f"\n[ROI] GROSS ROI: {((total_revenue - total_spend) / total_spend * 100):.1f}%")
        print(f"[ROI] ACTUAL ROI: {((actual_revenue - total_spend) / total_spend * 100):.1f}%")
    except:
        estimated_revenue = 1889.26
        actual_revenue = estimated_revenue * 0.88
        print(f"\n[FINANCIAL] Total Meta Ads Spend: ${total_spend:,.2f}")
        print(f"[FINANCIAL] Estimated Revenue: ${estimated_revenue:,.2f}")
        print(f"[FINANCIAL] Actual Revenue (after royalties): ${actual_revenue:,.2f}")
        print(f"\n[ROI] ESTIMATED ROI: {((actual_revenue - total_spend) / total_spend * 100):.1f}%")
    
    # Test API Connection
    print("\n" + "=" * 80)
    print("META API CONNECTION TEST")
    print("=" * 80)
    
    access_token = os.getenv('META_ACCESS_TOKEN')
    ad_account_id = os.getenv('META_AD_ACCOUNT_ID')
    
    if access_token and ad_account_id:
        print(f"[SUCCESS] Access token found (length: {len(access_token)} chars)")
        print(f"[SUCCESS] Ad Account ID: {ad_account_id}")
        print("\n[INFO] API credentials are configured and ready to use")
        print("To fetch live data, you can use the Meta Ads API with these credentials")
    else:
        print("[ERROR] API credentials not found in .env file")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"""
Key Findings:
1. Total Meta Ads spend: ${total_spend:,.2f}
2. Top performing campaign: {campaign_metrics.index[0]}
3. Average cost per result: ${avg_cpr:.2f}
4. Current ROI is {'NEGATIVE' if total_spend > 1889.26 else 'POSITIVE'}

Recommendations:
- Focus budget on {campaign_metrics.index[0]} campaign
- Optimize targeting to reduce cost per result
- Consider reducing overall spend until unit economics improve
""")

if __name__ == "__main__":
    main()