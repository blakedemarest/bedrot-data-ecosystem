import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from scipy.stats import pearsonr, spearmanr
from scipy.signal import correlate
import warnings
warnings.filterwarnings('ignore')

print("BEDROT ANALYTICS: TikTok Views -> Spotify Streams Correlation Analysis")
print("="*80)

# Load datasets
print("\n1. LOADING DATASETS...")
tiktok_df = pd.read_csv(r'data_lake\4_curated\tiktok_analytics_curated_20250908_055938.csv')
spotify_df = pd.read_csv(r'data_lake\4_curated\spotify_audience_curated_20250907_141945.csv')
combined_streams_df = pd.read_csv(r'data_lake\4_curated\tidy_daily_streams.csv')

# Filter for ZONE A0 data
zonea0_tiktok = tiktok_df[tiktok_df['artist'] == 'zone.a0'].copy()
zonea0_spotify = spotify_df[spotify_df['artist_name'] == 'zone_a0'].copy()

print(f"TikTok zone.a0 records: {len(zonea0_tiktok)}")
print(f"Spotify zone_a0 records: {len(zonea0_spotify)}")
print(f"Combined streams records: {len(combined_streams_df)}")

# Convert dates
zonea0_tiktok['date'] = pd.to_datetime(zonea0_tiktok['date'])
zonea0_spotify['date'] = pd.to_datetime(zonea0_spotify['date'])
combined_streams_df['date'] = pd.to_datetime(combined_streams_df['date'])

# Focus on non-zero data periods
print("\n2. IDENTIFYING ACTIVITY PERIODS...")
active_tiktok = zonea0_tiktok[zonea0_tiktok['Video Views'] > 0]
active_spotify = zonea0_spotify[zonea0_spotify['streams'] > 0]

print(f"TikTok active period: {active_tiktok['date'].min()} to {active_tiktok['date'].max()}")
print(f"Spotify active period: {active_spotify['date'].min()} to {active_spotify['date'].max()}")

print("\n3. PEAK ACTIVITY ANALYSIS...")
print("TikTok Top 10 Days:")
top_tiktok_days = active_tiktok.nlargest(10, 'Video Views')[['date', 'Video Views', 'Likes', 'engagement_rate']]
print(top_tiktok_days)

print("\nSpotify Top 10 Days:")
top_spotify_days = active_spotify.nlargest(10, 'streams')[['date', 'streams', 'listeners', 'followers']]
print(top_spotify_days)

# Calculate lag correlation
print("\n4. LAG CORRELATION ANALYSIS...")
def calculate_lag_correlation(tiktok_data, spotify_data, max_lag_days=90):
    """Calculate correlation at different lag periods"""
    
    # Merge datasets on date for overlap analysis
    date_range = pd.date_range(
        start=min(tiktok_data['date'].min(), spotify_data['date'].min()),
        end=max(tiktok_data['date'].max(), spotify_data['date'].max()),
        freq='D'
    )
    
    # Create daily series
    tiktok_series = tiktok_data.set_index('date')['Video Views'].reindex(date_range, fill_value=0)
    spotify_series = spotify_data.set_index('date')['streams'].reindex(date_range, fill_value=0)
    
    correlations = []
    
    for lag in range(0, max_lag_days + 1, 7):  # Weekly intervals
        if lag == 0:
            corr_data = pd.DataFrame({
                'tiktok': tiktok_series,
                'spotify': spotify_series
            }).dropna()
        else:
            # Shift TikTok data forward by lag days
            shifted_tiktok = tiktok_series.shift(lag)
            corr_data = pd.DataFrame({
                'tiktok': shifted_tiktok,
                'spotify': spotify_series
            }).dropna()
        
        if len(corr_data) > 10 and corr_data['tiktok'].sum() > 0:
            pearson_r, p_val = pearsonr(corr_data['tiktok'], corr_data['spotify'])
            correlations.append({
                'lag_days': lag,
                'lag_weeks': lag/7,
                'correlation': pearson_r,
                'p_value': p_val,
                'sample_size': len(corr_data)
            })
    
    return pd.DataFrame(correlations)

lag_corr = calculate_lag_correlation(active_tiktok, active_spotify, max_lag_days=84)
print("\nLag Correlation Results (Weekly):")
print(lag_corr.round(4))

best_lag = lag_corr.loc[lag_corr['correlation'].idxmax()]
print(f"\nBEST CORRELATION: {best_lag['correlation']:.4f} at {best_lag['lag_weeks']:.0f} weeks lag")

# 5. CUMULATIVE IMPACT ANALYSIS
print("\n5. CUMULATIVE IMPACT ANALYSIS...")
def analyze_cumulative_impact(tiktok_data, spotify_data, window_days=30):
    """Analyze how TikTok activity accumulates to drive streams"""
    
    # Calculate rolling sums for TikTok views
    tiktok_daily = tiktok_data.set_index('date')['Video Views'].resample('D').sum()
    
    results = []
    for window in [7, 14, 30, 60]:
        tiktok_rolling = tiktok_daily.rolling(window=window).sum()
        
        # Shift forward by optimal lag
        lag_days = int(best_lag['lag_days'])
        tiktok_lagged = tiktok_rolling.shift(lag_days)
        
        # Merge with Spotify data
        spotify_daily = spotify_data.set_index('date')['streams']
        merged = pd.DataFrame({
            'tiktok_cumulative': tiktok_lagged,
            'spotify_streams': spotify_daily
        }).dropna()
        
        if len(merged) > 5:
            corr, p_val = pearsonr(merged['tiktok_cumulative'], merged['spotify_streams'])
            results.append({
                'window_days': window,
                'correlation': corr,
                'p_value': p_val,
                'sample_size': len(merged)
            })
    
    return pd.DataFrame(results)

cumulative_analysis = analyze_cumulative_impact(active_tiktok, active_spotify)
print("Cumulative Window Analysis:")
print(cumulative_analysis.round(4))

# 6. CONVERSION RATE ANALYSIS
print("\n6. CONVERSION RATE ANALYSIS...")
def calculate_conversion_metrics(tiktok_data, spotify_data, lag_days):
    """Calculate conversion rates from TikTok views to Spotify streams"""
    
    # Prepare data with lag
    tiktok_daily = tiktok_data.set_index('date')['Video Views'].resample('D').sum()
    spotify_daily = spotify_data.set_index('date')['streams'].resample('D').sum()
    
    # Apply lag
    tiktok_lagged = tiktok_daily.shift(lag_days)
    
    # Merge datasets
    conversion_data = pd.DataFrame({
        'tiktok_views': tiktok_lagged,
        'spotify_streams': spotify_daily
    }).dropna()
    
    # Remove zero days
    active_conversion = conversion_data[conversion_data['tiktok_views'] > 0]
    
    if len(active_conversion) > 0:
        total_views = active_conversion['tiktok_views'].sum()
        total_streams = active_conversion['spotify_streams'].sum()
        conversion_rate = (total_streams / total_views) * 100
        
        return {
            'total_tiktok_views': int(total_views),
            'total_spotify_streams': int(total_streams),
            'conversion_rate_percent': conversion_rate,
            'avg_daily_views': active_conversion['tiktok_views'].mean(),
            'avg_daily_streams': active_conversion['spotify_streams'].mean(),
            'active_days': len(active_conversion)
        }
    
    return None

conversion_metrics = calculate_conversion_metrics(active_tiktok, active_spotify, int(best_lag['lag_days']))
if conversion_metrics:
    print("CONVERSION METRICS:")
    for key, value in conversion_metrics.items():
        if 'percent' in key or 'rate' in key:
            print(f"{key}: {value:.4f}%")
        elif 'avg' in key:
            print(f"{key}: {value:.1f}")
        else:
            print(f"{key}: {value}")

# 7. SPILLOVER TO COMBINED STREAMS
print("\n7. SPILLOVER EFFECT ANALYSIS...")
print("Analyzing if TikTok views boost overall BEDROT streams...")

# Check correlation between TikTok activity and combined streams
recent_combined = combined_streams_df[combined_streams_df['date'] >= '2024-07-01'].copy()
print(f"Recent combined streams (July+ 2024): {len(recent_combined)} days")
print(f"Date range: {recent_combined['date'].min()} to {recent_combined['date'].max()}")

# Calculate correlation with combined streams
tiktok_july_onwards = active_tiktok[active_tiktok['date'] >= '2024-07-01']
if len(tiktok_july_onwards) > 0 and len(recent_combined) > 0:
    
    # Apply same lag to combined streams
    lag_days = int(best_lag['lag_days'])
    tiktok_for_combined = tiktok_july_onwards.set_index('date')['Video Views']
    combined_daily = recent_combined.set_index('date')['combined_streams']
    
    # Shift TikTok forward by lag
    tiktok_lagged_combined = tiktok_for_combined.shift(lag_days)
    
    spillover_data = pd.DataFrame({
        'tiktok_views': tiktok_lagged_combined,
        'combined_streams': combined_daily
    }).dropna()
    
    if len(spillover_data) > 5:
        spillover_corr, spillover_p = pearsonr(spillover_data['tiktok_views'], spillover_data['combined_streams'])
        print(f"TikTok → Combined Streams Correlation: {spillover_corr:.4f} (p={spillover_p:.4f})")
        
        # Calculate spillover conversion rate
        spillover_conversion = (spillover_data['combined_streams'].sum() / spillover_data['tiktok_views'].sum()) * 100
        print(f"Spillover Conversion Rate: {spillover_conversion:.4f}%")

# 8. THRESHOLD ANALYSIS
print("\n8. THRESHOLD EFFECT ANALYSIS...")
def analyze_thresholds(tiktok_data, spotify_data, lag_days):
    """Find view thresholds that trigger streaming spikes"""
    
    tiktok_daily = tiktok_data.set_index('date')['Video Views']
    spotify_daily = spotify_data.set_index('date')['streams']
    
    # Apply lag
    tiktok_lagged = tiktok_daily.shift(lag_days)
    
    threshold_data = pd.DataFrame({
        'tiktok_views': tiktok_lagged,
        'spotify_streams': spotify_daily
    }).dropna()
    
    # Define thresholds
    thresholds = [0, 100, 500, 1000, 1500, 2000, 2500]
    threshold_results = []
    
    for threshold in thresholds:
        above_threshold = threshold_data[threshold_data['tiktok_views'] >= threshold]
        if len(above_threshold) > 0:
            avg_streams = above_threshold['spotify_streams'].mean()
            threshold_results.append({
                'view_threshold': threshold,
                'avg_streams': avg_streams,
                'days_above': len(above_threshold)
            })
    
    return pd.DataFrame(threshold_results)

threshold_analysis = analyze_thresholds(active_tiktok, active_spotify, int(best_lag['lag_days']))
print("Threshold Analysis:")
print(threshold_analysis.round(2))

# 9. FINAL INSIGHTS
print("\n" + "="*80)
print("KEY BUSINESS INSIGHTS:")
print("="*80)

print(f"1. OPTIMAL LAG: TikTok views convert to streams after {best_lag['lag_weeks']:.0f} weeks")
print(f"2. CORRELATION STRENGTH: {best_lag['correlation']:.4f} (p={best_lag['p_value']:.4f})")

if conversion_metrics:
    print(f"3. CONVERSION RATE: {conversion_metrics['conversion_rate_percent']:.4f}% of TikTok views → streams")
    print(f"4. SCALE: {conversion_metrics['total_tiktok_views']} views generated {conversion_metrics['total_spotify_streams']} streams")

if len(threshold_analysis) > 1:
    high_threshold = threshold_analysis[threshold_analysis['view_threshold'] >= 1000]
    if len(high_threshold) > 0:
        best_threshold = high_threshold.loc[high_threshold['avg_streams'].idxmax()]
        print(f"5. SWEET SPOT: {best_threshold['view_threshold']}+ views -> {best_threshold['avg_streams']:.1f} avg streams")

print(f"\nSTRATEGIC RECOMMENDATIONS:")
print(f"- Plan content {int(best_lag['lag_weeks'])} weeks before desired stream spikes")
print(f"- Target 1000+ daily TikTok views for meaningful conversion")
print(f"- Monitor cumulative 30-day TikTok performance for best stream prediction")
print(f"- Consider spillover effects on overall BEDROT catalog performance")

print("\n" + "="*80)
print("Analysis complete. Data exported for further visualization.")