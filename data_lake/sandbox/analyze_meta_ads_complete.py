#!/usr/bin/env python3
"""
Complete Meta Ads Analysis Script
Analyzes the exported CSV and provides option to fetch fresh data via API
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
pd.set_option('display.float_format', lambda x: '%.2f' % x)

def load_csv_data():
    """Load the exported Meta Ads CSV"""
    csv_path = Path(r'C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake\1_landing\BEDROT-ADS-Ads-Jul-12-2022-Aug-12-2025.csv')
    
    if not csv_path.exists():
        # Try Unix path
        csv_path = Path('/mnt/c/Users/Earth/BEDROT PRODUCTIONS/bedrot-data-ecosystem/data_lake/1_landing/BEDROT-ADS-Ads-Jul-12-2022-Aug-12-2025.csv')
    
    print(f"Loading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Clean and process data
    df['Amount spent (USD)'] = pd.to_numeric(df['Amount spent (USD)'], errors='coerce').fillna(0)
    df['Impressions'] = pd.to_numeric(df['Impressions'], errors='coerce').fillna(0)
    df['Reach'] = pd.to_numeric(df['Reach'], errors='coerce').fillna(0)
    df['Results'] = pd.to_numeric(df['Results'], errors='coerce').fillna(0)
    df['Cost per results'] = pd.to_numeric(df['Cost per results'], errors='coerce').fillna(0)
    
    return df

def analyze_total_spend(df):
    """Analyze total spending metrics"""
    print("\n" + "="*80)
    print("💰 TOTAL META ADS SPEND ANALYSIS")
    print("="*80)
    
    total_spend = df['Amount spent (USD)'].sum()
    total_impressions = df['Impressions'].sum()
    total_reach = df['Reach'].sum()
    total_results = df['Results'].sum()
    num_ads = len(df)
    
    # Calculate averages
    avg_cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
    avg_cpr = (total_spend / total_results) if total_results > 0 else 0
    
    print(f"\n🎯 TOTAL LIFETIME SPEND: ${total_spend:,.2f}")
    print(f"\n📊 KEY METRICS:")
    print(f"  • Total Ads Run: {num_ads}")
    print(f"  • Total Impressions: {total_impressions:,.0f}")
    print(f"  • Total Reach: {total_reach:,.0f}")
    print(f"  • Total Results/Conversions: {total_results:,.0f}")
    print(f"  • Average CPM: ${avg_cpm:.2f}")
    print(f"  • Average Cost per Result: ${avg_cpr:.2f}")
    
    return {
        'total_spend': total_spend,
        'total_impressions': total_impressions,
        'total_reach': total_reach,
        'total_results': total_results,
        'num_ads': num_ads,
        'avg_cpm': avg_cpm,
        'avg_cpr': avg_cpr
    }

def analyze_campaigns(df):
    """Analyze by campaign"""
    print("\n" + "="*80)
    print("📈 CAMPAIGN ANALYSIS")
    print("="*80)
    
    # Extract campaign names
    df['Campaign'] = df['Ad Set Name'].str.extract(r'([^-]+)')[0].str.strip()
    
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
    
    print("\nCampaign Performance:")
    for campaign, data in campaign_metrics.iterrows():
        spend_pct = (data['Total Spend'] / df['Amount spent (USD)'].sum() * 100)
        print(f"\n  {campaign}:")
        print(f"    • Spend: ${data['Total Spend']:,.2f} ({spend_pct:.1f}% of total)")
        print(f"    • Results: {data['Results']:,.0f}")
        print(f"    • Cost per Result: ${data['Cost per Result']:.2f}")
        print(f"    • CPM: ${data['CPM']:.2f}")
        print(f"    • Ads: {data['Num Ads']:.0f}")
    
    return campaign_metrics

def analyze_creatives(df):
    """Analyze by creative type"""
    print("\n" + "="*80)
    print("🎨 CREATIVE ANALYSIS")
    print("="*80)
    
    # Extract creative numbers
    df['Creative'] = df['Ad name'].str.extract(r'(AD\d+)')
    
    # Group by creative
    creative_performance = df.groupby('Creative').agg({
        'Amount spent (USD)': 'sum',
        'Results': 'sum',
        'Impressions': 'sum',
        'Cost per results': 'mean'
    }).round(2)
    
    creative_performance.columns = ['Total Spend', 'Total Results', 'Total Impressions', 'Avg Cost per Result']
    creative_performance['Effectiveness'] = (creative_performance['Total Results'] / creative_performance['Total Spend']).round(3)
    creative_performance = creative_performance.sort_values('Total Spend', ascending=False)
    
    print("\nTop Creatives by Spend:")
    for creative, data in creative_performance.head(5).iterrows():
        print(f"\n  {creative}:")
        print(f"    • Spend: ${data['Total Spend']:,.2f}")
        print(f"    • Results: {data['Total Results']:,.0f}")
        print(f"    • Effectiveness: {data['Effectiveness']:.3f} results per dollar")
        print(f"    • Avg Cost per Result: ${data['Avg Cost per Result']:.2f}")
    
    return creative_performance

def calculate_roi(total_spend):
    """Calculate ROI based on music revenue"""
    print("\n" + "="*80)
    print("💸 ROI ANALYSIS")
    print("="*80)
    
    # Try to load actual revenue data
    try:
        revenue_path = Path('/mnt/c/Users/Earth/BEDROT PRODUCTIONS/bedrot-data-ecosystem/data_lake/4_curated/dk_bank_details.csv')
        revenue_df = pd.read_csv(revenue_path)
        total_revenue = revenue_df['Earnings (USD)'].sum()
        actual_revenue = total_revenue * 0.88  # 88% retention after royalties
        
        roi = ((actual_revenue - total_spend) / total_spend * 100)
        
        print(f"\n  💰 Total Ad Spend: ${total_spend:,.2f}")
        print(f"  💵 Gross Music Revenue: ${total_revenue:,.2f}")
        print(f"  💸 Actual Revenue (88% after royalties): ${actual_revenue:,.2f}")
        print(f"\n  📈 ROI: {roi:.1f}%")
        
        if roi > 0:
            print(f"  ✅ POSITIVE ROI: You made ${actual_revenue - total_spend:,.2f} profit")
        else:
            print(f"  ❌ NEGATIVE ROI: You lost ${total_spend - actual_revenue:,.2f}")
        
        print(f"\n  For every $1 spent on ads:")
        print(f"    • Gross return: ${(total_revenue / total_spend):.2f}")
        print(f"    • Actual return: ${(actual_revenue / total_spend):.2f}")
        
    except Exception as e:
        print(f"\n  ⚠️ Could not load revenue data: {e}")
        print(f"  Using estimated revenue of $1,889.26")
        
        estimated_revenue = 1889.26
        actual_revenue = estimated_revenue * 0.88
        roi = ((actual_revenue - total_spend) / total_spend * 100)
        
        print(f"\n  💰 Total Ad Spend: ${total_spend:,.2f}")
        print(f"  💵 Estimated Revenue: ${estimated_revenue:,.2f}")
        print(f"  💸 Actual Revenue (after royalties): ${actual_revenue:,.2f}")
        print(f"\n  📈 ESTIMATED ROI: {roi:.1f}%")
        
        if roi > 0:
            print(f"  ✅ POSITIVE ROI: Estimated profit of ${actual_revenue - total_spend:,.2f}")
        else:
            print(f"  ❌ NEGATIVE ROI: Estimated loss of ${total_spend - actual_revenue:,.2f}")

def export_to_curated(df, campaign_metrics, creative_performance, summary_metrics):
    """Export processed data to curated folder"""
    print("\n" + "="*80)
    print("💾 EXPORTING DATA")
    print("="*80)
    
    output_path = Path('/mnt/c/Users/Earth/BEDROT PRODUCTIONS/bedrot-data-ecosystem/data_lake/4_curated')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save complete processed data
    complete_file = output_path / f'meta_ads_complete_{timestamp}.csv'
    df.to_csv(complete_file, index=False)
    print(f"\n✅ Complete data saved: {complete_file.name}")
    
    # Save campaign summary
    campaign_file = output_path / f'meta_ads_campaigns_{timestamp}.csv'
    campaign_metrics.to_csv(campaign_file)
    print(f"✅ Campaign summary saved: {campaign_file.name}")
    
    # Save creative performance
    creative_file = output_path / f'meta_ads_creatives_{timestamp}.csv'
    creative_performance.to_csv(creative_file)
    print(f"✅ Creative analysis saved: {creative_file.name}")
    
    # Save summary metrics
    summary_df = pd.DataFrame([summary_metrics])
    summary_file = output_path / f'meta_ads_summary_{timestamp}.csv'
    summary_df.to_csv(summary_file, index=False)
    print(f"✅ Summary metrics saved: {summary_file.name}")

def get_fresh_token_instructions():
    """Instructions for getting a fresh Meta API token"""
    print("\n" + "="*80)
    print("🔑 HOW TO GET A FRESH META ADS API TOKEN")
    print("="*80)
    print("""
    1. Go to: https://developers.facebook.com/tools/explorer/
    
    2. In the dropdown, select your app (or use 'Graph API Explorer')
    
    3. Click 'Generate Access Token'
    
    4. Add these permissions:
       ✓ ads_read
       ✓ ads_management
       ✓ business_management
       
    5. Click 'Generate Access Token' again
    
    6. Copy the token and update it in:
       /data_lake/.env file
       
       META_ACCESS_TOKEN=your_new_token_here
    
    7. The token will be valid for about 60 days
    
    Alternative: Use Business Manager Token (longer lasting):
    1. Go to: https://business.facebook.com/settings/system-users
    2. Create a system user
    3. Generate token with ads permissions
    4. This token can last up to 60 days without expiration
    """)

def main():
    """Main execution"""
    print("="*80)
    print("META ADS COMPLETE ANALYSIS")
    print("Date Range: July 2022 - August 2025")
    print("="*80)
    
    # Load CSV data
    print("\n📂 Loading CSV data...")
    df = load_csv_data()
    print(f"✅ Loaded {len(df)} ads")
    
    # Analyze total spend
    summary_metrics = analyze_total_spend(df)
    
    # Analyze campaigns
    campaign_metrics = analyze_campaigns(df)
    
    # Analyze creatives
    creative_performance = analyze_creatives(df)
    
    # Calculate ROI
    calculate_roi(summary_metrics['total_spend'])
    
    # Export to curated
    export_to_curated(df, campaign_metrics, creative_performance, summary_metrics)
    
    # Show API instructions
    print("\n" + "="*80)
    print("📡 WANT FRESH DATA FROM API?")
    print("="*80)
    print("\nYour API token has expired. To fetch fresh data directly from Meta:")
    get_fresh_token_instructions()
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE!")
    print("="*80)
    print(f"\n🎯 Key Finding: Your total Meta Ads spend is ${summary_metrics['total_spend']:,.2f}")
    print(f"   (Not $456 as shown in the partial May-June data)")

if __name__ == "__main__":
    main()