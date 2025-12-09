import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

print("BEDROT MARKETING ATTRIBUTION: Multi-Channel Regression Analysis")
print("="*80)

# Load all marketing data sources
print("\n1. LOADING ALL MARKETING CHANNELS...")

# Streaming data (dependent variable)
streaming_df = pd.read_csv('data_lake/4_curated/tidy_daily_streams.csv')
spotify_detailed = pd.read_csv('data_lake/4_curated/spotify_audience_curated_20250907_141945.csv')

# TikTok data (suspected independent variable)
tiktok_df = pd.read_csv('data_lake/4_curated/tiktok_analytics_curated_20250908_055938.csv')

# Meta Ads data (control variable)
try:
    meta_campaigns = pd.read_csv('data_lake/4_curated/metaads_campaigns_daily.csv')
    print(f"Meta campaigns loaded: {len(meta_campaigns)} campaigns")
except:
    meta_campaigns = None
    print("Meta campaigns not available")

try:
    meta_summary = pd.read_csv('data_lake/4_curated/meta_ads_summary_20250812_030945.csv')
    print(f"Meta summary loaded: {meta_summary.shape}")
except:
    meta_summary = None

print(f"Streaming data: {len(streaming_df)} records")
print(f"Spotify detailed: {len(spotify_detailed)} records") 
print(f"TikTok data: {len(tiktok_df)} records")

# Convert dates
streaming_df['date'] = pd.to_datetime(streaming_df['date'])
spotify_detailed['date'] = pd.to_datetime(spotify_detailed['date'])
tiktok_df['date'] = pd.to_datetime(tiktok_df['date'])

print("\n2. BUILDING COMPREHENSIVE DATASET...")

# Create daily aggregated dataset
date_range = pd.date_range(
    start='2024-07-01',  # Start when TikTok activity begins
    end='2025-09-07',    # Latest data available
    freq='D'
)

# Initialize master dataset
master_df = pd.DataFrame({'date': date_range})

# Add streaming metrics (dependent variables)
streaming_daily = streaming_df.groupby('date').agg({
    'combined_streams': 'sum',
    'spotify_streams': 'sum',
    'apple_streams': 'sum'
}).reset_index()
master_df = master_df.merge(streaming_daily, on='date', how='left').fillna(0)

# Add ZONE A0 specific streams
zonea0_spotify = spotify_detailed[spotify_detailed['artist_name'] == 'zone_a0']
zonea0_daily = zonea0_spotify.groupby('date').agg({
    'streams': 'sum',
    'listeners': 'sum',
    'followers': 'max'
}).reset_index()
zonea0_daily.columns = ['date', 'zonea0_streams', 'zonea0_listeners', 'zonea0_followers']
master_df = master_df.merge(zonea0_daily, on='date', how='left').fillna(0)

# Add TikTok metrics (independent variables)
tiktok_zonea0 = tiktok_df[tiktok_df['artist'] == 'zone.a0']
tiktok_daily = tiktok_zonea0.groupby('date').agg({
    'Video Views': 'sum',
    'Likes': 'sum', 
    'Comments': 'sum',
    'Shares': 'sum',
    'engagement_rate': 'mean'
}).reset_index()
tiktok_daily.columns = ['date', 'tiktok_views', 'tiktok_likes', 'tiktok_comments', 'tiktok_shares', 'tiktok_engagement']
master_df = master_df.merge(tiktok_daily, on='date', how='left').fillna(0)

# Add Meta Ads spend (if available)
if meta_campaigns is not None:
    # This requires processing meta campaigns by date - let's create a proxy
    # Since we don't have daily spend, we'll create campaign activity indicator
    master_df['meta_campaigns_active'] = 0  # Placeholder for now
    
    # Based on campaign dates from the data we saw
    campaign_periods = [
        ('2025-05-25', '2025-06-06'),  # Major PIG1987 campaign period
        ('2025-05-30', '2025-06-14'),  # IWARY campaign period
    ]
    
    for start, end in campaign_periods:
        mask = (master_df['date'] >= start) & (master_df['date'] <= end)
        master_df.loc[mask, 'meta_campaigns_active'] = 1

# Add time-based features (control variables)
master_df['day_of_week'] = master_df['date'].dt.dayofweek
master_df['month'] = master_df['date'].dt.month
master_df['week_of_year'] = master_df['date'].dt.isocalendar().week

# Add lagged features for different channels
print("\n3. CREATING LAGGED FEATURES...")

def create_lagged_features(df, column, lags):
    """Create lagged features for a given column"""
    for lag in lags:
        df[f'{column}_lag_{lag}d'] = df[column].shift(lag)
    return df

# Test multiple lag periods for each channel
tiktok_lags = [1, 3, 7, 14, 30, 60, 84]  # 1 day to 12 weeks
meta_lags = [0, 1, 3, 7, 14]  # Shorter lags for paid ads

for lag in tiktok_lags:
    master_df[f'tiktok_views_lag_{lag}d'] = master_df['tiktok_views'].shift(lag)
    master_df[f'tiktok_engagement_lag_{lag}d'] = master_df['tiktok_engagement'].shift(lag)

for lag in meta_lags:
    master_df[f'meta_active_lag_{lag}d'] = master_df['meta_campaigns_active'].shift(lag)

# Create rolling window features (cumulative impact)
for window in [7, 14, 30]:
    master_df[f'tiktok_views_rolling_{window}d'] = master_df['tiktok_views'].rolling(window).sum()
    master_df[f'meta_active_rolling_{window}d'] = master_df['meta_campaigns_active'].rolling(window).sum()

# Remove early rows with NaN due to lags
analysis_df = master_df[master_df['date'] >= '2024-09-01'].copy().dropna()

print(f"Analysis dataset: {len(analysis_df)} days with complete data")
print(f"Date range: {analysis_df['date'].min()} to {analysis_df['date'].max()}")

print("\n4. CORRELATION MATRIX - ALL CHANNELS...")
correlation_cols = ['zonea0_streams', 'tiktok_views', 'meta_campaigns_active'] + \
                  [col for col in analysis_df.columns if 'lag' in col and ('tiktok' in col or 'meta' in col)]

corr_data = analysis_df[correlation_cols].corr()
print("Top correlations with ZONE A0 streams:")
stream_corrs = corr_data['zonea0_streams'].abs().sort_values(ascending=False)
print(stream_corrs.head(15))

print("\n5. MULTIVARIATE REGRESSION ANALYSIS...")

# Define features and target
target = 'zonea0_streams'
feature_cols = [col for col in analysis_df.columns if 'lag' in col or 'rolling' in col or 'meta' in col]
feature_cols += ['day_of_week', 'month']

X = analysis_df[feature_cols].fillna(0)
y = analysis_df[target]

print(f"Features: {len(feature_cols)}")
print(f"Sample size: {len(X)}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Multiple regression models
models = {
    'Linear Regression': LinearRegression(),
    'Ridge Regression': Ridge(alpha=1.0),
    'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42)
}

results = {}
for name, model in models.items():
    if 'Forest' in name:
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        feature_importance = model.feature_importances_
    else:
        model.fit(X_train_scaled, y_train)
        pred = model.predict(X_test_scaled)
        feature_importance = abs(model.coef_)
    
    r2 = r2_score(y_test, pred)
    mae = mean_absolute_error(y_test, pred)
    
    results[name] = {
        'r2_score': r2,
        'mae': mae,
        'feature_importance': feature_importance
    }
    
    print(f"\n{name}:")
    print(f"  R² Score: {r2:.4f}")
    print(f"  Mean Absolute Error: {mae:.1f} streams")

print("\n6. FEATURE IMPORTANCE ANALYSIS...")
best_model_name = max(results.keys(), key=lambda k: results[k]['r2_score'])
best_model = models[best_model_name]
print(f"\nBest performing model: {best_model_name}")

# Get feature importance from best model
importance = results[best_model_name]['feature_importance']
feature_importance_df = pd.DataFrame({
    'feature': feature_cols,
    'importance': importance
}).sort_values('importance', ascending=False)

print("\nTop 15 Most Important Features:")
print(feature_importance_df.head(15))

# Specifically analyze TikTok vs Meta contribution
print("\n7. CHANNEL ATTRIBUTION ANALYSIS...")

tiktok_features = [f for f in feature_cols if 'tiktok' in f]
meta_features = [f for f in feature_cols if 'meta' in f]

tiktok_importance = feature_importance_df[feature_importance_df['feature'].isin(tiktok_features)]['importance'].sum()
meta_importance = feature_importance_df[feature_importance_df['feature'].isin(meta_features)]['importance'].sum()

print(f"TikTok total importance: {tiktok_importance:.4f}")
print(f"Meta Ads total importance: {meta_importance:.4f}")
print(f"TikTok vs Meta ratio: {tiktok_importance/meta_importance:.2f}:1")

# Test incremental lift
print("\n8. INCREMENTAL LIFT TESTING...")

# Model without TikTok features
X_no_tiktok = X_train[[f for f in feature_cols if 'tiktok' not in f]]
X_test_no_tiktok = X_test[[f for f in feature_cols if 'tiktok' not in f]]

if len(X_no_tiktok.columns) > 0:
    model_no_tiktok = RandomForestRegressor(n_estimators=100, random_state=42)
    model_no_tiktok.fit(X_no_tiktok, y_train)
    pred_no_tiktok = model_no_tiktok.predict(X_test_no_tiktok)
    r2_no_tiktok = r2_score(y_test, pred_no_tiktok)
    
    tiktok_lift = results['Random Forest']['r2_score'] - r2_no_tiktok
    print(f"Model R² without TikTok: {r2_no_tiktok:.4f}")
    print(f"TikTok incremental lift: {tiktok_lift:.4f}")

# Model without Meta features  
X_no_meta = X_train[[f for f in feature_cols if 'meta' not in f]]
X_test_no_meta = X_test[[f for f in feature_cols if 'meta' not in f]]

if len(X_no_meta.columns) > 0:
    model_no_meta = RandomForestRegressor(n_estimators=100, random_state=42)
    model_no_meta.fit(X_no_meta, y_train)
    pred_no_meta = model_no_meta.predict(X_test_no_meta)
    r2_no_meta = r2_score(y_test, pred_no_meta)
    
    meta_lift = results['Random Forest']['r2_score'] - r2_no_meta
    print(f"Model R² without Meta: {r2_no_meta:.4f}")
    print(f"Meta Ads incremental lift: {meta_lift:.4f}")

print("\n" + "="*80)
print("KEY FINDINGS:")
print("="*80)
print("1. Best model explains {:.1f}% of stream variance".format(results[best_model_name]['r2_score']*100))
print("2. TikTok features account for {:.1f}% of total importance".format(tiktok_importance*100))
print("3. Meta Ads features account for {:.1f}% of total importance".format(meta_importance*100))

optimal_tiktok_lag = feature_importance_df[feature_importance_df['feature'].str.contains('tiktok_views_lag')].iloc[0]
print(f"4. Optimal TikTok lag: {optimal_tiktok_lag['feature']} (importance: {optimal_tiktok_lag['importance']:.4f})")

print(f"\n📊 ATTRIBUTION VERDICT:")
if tiktok_importance > meta_importance:
    print(f"✅ TikTok is the PRIMARY driver ({tiktok_importance/meta_importance:.1f}x stronger than Meta)")
elif meta_importance > tiktok_importance * 1.5:
    print(f"⚠️  Meta Ads are the PRIMARY driver ({meta_importance/tiktok_importance:.1f}x stronger than TikTok)")
else:
    print(f"🤝 Both channels contribute meaningfully (similar importance)")