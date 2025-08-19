# Sandbox Zone

## Purpose
The sandbox zone serves as a secure, isolated environment for data exploration, experimentation, and prototyping within the BEDROT Data Lake. This zone enables data scientists, analysts, and developers to freely explore data, test hypotheses, and develop new analytics approaches without impacting production systems or datasets.

## What Goes Here
- **Experimental data processing**: Ad-hoc analysis and transformation scripts
- **Proof of concept work**: Early-stage feature development and testing
- **Temporary datasets**: Short-lived data for exploration and validation
- **User-specific workspaces**: Individual project folders for team members
- **Algorithm testing**: Machine learning model experiments and validation
- **Data quality investigations**: Exploratory analysis of data issues
- **Research projects**: Academic or business research initiatives
- **Training materials**: Learning datasets and educational content

## Directory Structure
```
sandbox/
├── analysis/               # Business metrics and revenue analysis scripts
│   ├── analysis_bedrot_business_metrics.py          # Core business KPIs and ROI
│   ├── analysis_bedrot_business_metrics_with_royalties.py  # Revenue with royalty splits
│   ├── analyze_royalty_adjusted_revenue.py          # Royalty impact analysis
│   ├── run_meta_ads_analysis.py                     # Meta Ads campaign performance
│   └── get_complete_meta_ads_spend.py               # Total ad spend calculations
├── verified/               # Production-tested Jupyter notebooks
│   ├── distrokid_landing2raw.ipynb
│   ├── distrokid_raw2staging.ipynb
│   ├── distrokid_staging2curated.ipynb
│   ├── meta_ads_exploratory_analysis_4_cleaning.ipynb
│   ├── metaads_landing2raw.ipynb
│   ├── metaads_raw2staging.ipynb
│   ├── metaads_staging2curated.ipynb
│   ├── streaming_data_tidy.ipynb
│   ├── tiktok_raw2staging.ipynb
│   ├── toolost_landing2raw.ipynb
│   ├── toolost_raw2staging.ipynb
│   └── toolost_staging2curated.ipynb
├── experiments/            # Active research and development
│   ├── fetch_meta_ads_via_api.py
│   ├── meta_ads_api_fetcher.py
│   └── analyze_meta_ads_complete.py
└── notebooks/              # Exploration and data analysis
    ├── financial_analysis.ipynb
    ├── linktree_landing2raw.ipynb
    ├── linktree_raw2staging.ipynb
    ├── linktree_staging2curated.ipynb
    └── meta_ads_complete_analysis.ipynb
```

## Analysis Scripts

The `analysis/` subdirectory contains production-ready business analysis scripts that generate key insights for BEDROT PRODUCTIONS:

### Core Business Metrics (`analysis_bedrot_business_metrics.py`)
- Calculates Cost Per Acquisition (CPA) from Meta Ads spend
- Computes Revenue Per Stream across all platforms
- Generates ROI metrics for marketing campaigns
- Analyzes catalog performance by artist and track

### Royalty Analysis (`analysis_bedrot_business_metrics_with_royalties.py`, `analyze_royalty_adjusted_revenue.py`)
- Applies royalty splits to revenue calculations
- Tracks collaborator earnings and splits
- Provides net revenue after royalty distributions
- Analyzes impact of different royalty structures

### Meta Ads Analysis (`run_meta_ads_analysis.py`, `get_complete_meta_ads_spend.py`)
- Deep dive into Meta Ads campaign performance
- Calculate total ad spend across all campaigns
- Track conversion metrics and ROAS (Return on Ad Spend)
- Identify best-performing campaigns and creatives

### Usage
All analysis scripts read from the curated zone (`4_curated/`) and expect the standard data lake structure:
```bash
cd sandbox/analysis
python analysis_bedrot_business_metrics.py
```

## Sandbox Rules & Guidelines

### Resource Management
- **Compute limits**: Respect CPU, memory, and storage quotas
- **Time limits**: Clean up temporary files and processes regularly
- **Storage quotas**: Monitor disk usage and archive or delete unused data
- **Concurrent access**: Coordinate with team members on shared resources

### Data Security & Privacy
- **No production secrets**: Never store production credentials or API keys
- **Data anonymization**: Use anonymized or synthetic data when possible
- **Access controls**: Respect data classification and access restrictions
- **Sensitive data handling**: Follow GDPR and privacy guidelines for personal data

### Documentation Standards
- **Experiment logs**: Document purpose, methodology, and findings
- **Code documentation**: Comment experimental code for future reference  
- **Results tracking**: Maintain records of successful and failed experiments
- **Knowledge sharing**: Document learnings for team benefit

### Clean-up Policies
- **Regular cleanup**: Remove temporary files and completed experiments
- **Archival process**: Move successful prototypes to appropriate zones
- **Resource monitoring**: Track storage usage and optimize regularly
- **Collaboration hygiene**: Clean shared spaces after use

## Common Use Cases

### Data Exploration
```python
# Example: Exploring streaming data patterns
import pandas as pd
import matplotlib.pyplot as plt

# Load sample data for exploration
streaming_data = pd.read_csv('curated/streaming/daily_streams.csv')

# Perform exploratory data analysis
monthly_trends = streaming_data.groupby('month').sum()
plt.plot(monthly_trends.index, monthly_trends['streams'])
plt.title('Monthly Streaming Trends')
plt.savefig('sandbox/experiments/streaming_trends.png')
```

### Algorithm Development
```python
# Example: Testing clustering algorithms
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Load artist performance data
artist_data = pd.read_parquet('curated/artists/performance_metrics.parquet')

# Feature engineering and model testing
features = artist_data[['monthly_streams', 'engagement_rate', 'social_followers']]
scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)

# Test different clustering approaches
for n_clusters in range(2, 10):
    kmeans = KMeans(n_clusters=n_clusters)
    labels = kmeans.fit_predict(scaled_features)
    # Evaluate and save results
```

### Data Quality Investigation
```python
# Example: Investigating data anomalies
import pandas as pd
from datetime import datetime, timedelta

# Load recent data for quality checks
recent_data = pd.read_csv('staging/social_media/tiktok_metrics.csv')

# Identify potential data quality issues
outliers = recent_data[recent_data['engagement_rate'] > 0.5]  # Unusually high engagement
missing_data = recent_data.isnull().sum()
duplicate_records = recent_data.duplicated().sum()

# Document findings
with open('sandbox/data_quality/tiktok_investigation.md', 'w') as f:
    f.write(f"Data Quality Report - {datetime.now()}\n")
    f.write(f"Outliers found: {len(outliers)}\n")
    f.write(f"Missing values: {missing_data.sum()}\n")
    f.write(f"Duplicates: {duplicate_records}\n")
```

## Integration with Production Pipeline

### Promotion Path
Successful sandbox experiments can be promoted through:
1. **Staging zone**: For production testing and validation
2. **Curated zone**: For business-ready datasets and models
3. **Production ETL**: Integration into automated pipelines
4. **Dashboard integration**: Real-time analytics and reporting

### Code Migration
- **Script standardization**: Convert notebooks to production-ready Python scripts
- **Error handling**: Add robust error handling and logging
- **Configuration management**: Use environment variables and config files
- **Testing**: Implement unit tests and data validation
- **Documentation**: Create comprehensive documentation for production use

## Development Tools & Resources

### Recommended Tools
- **Jupyter Notebooks**: Interactive data exploration and prototyping
- **Python libraries**: pandas, numpy, scikit-learn, matplotlib, seaborn
- **SQL tools**: SQLite browser, DBeaver for database exploration
- **Version control**: Git for tracking experimental code changes
- **Visualization**: Plotly, Bokeh for interactive charts

### Sample Datasets
The sandbox includes sample datasets for learning and experimentation:
- `sandbox/sample_data/streaming_sample.csv`: Anonymized streaming metrics
- `sandbox/sample_data/social_media_sample.json`: Sample social media data
- `sandbox/sample_data/financial_sample.parquet`: Synthetic financial data

## Performance Monitoring

### Resource Usage Tracking
- Monitor CPU and memory usage during experiments
- Track storage consumption by user and project
- Set alerts for resource limit violations
- Generate usage reports for capacity planning

### Optimization Guidelines
- Use efficient data formats (Parquet, HDF5) for large datasets
- Implement sampling for large-scale experiments
- Leverage pandas/Polars optimization techniques
- Cache intermediate results to avoid recomputation

## Next Steps

### Successful Experiments
When sandbox work proves valuable:
1. **Document findings**: Create comprehensive experiment reports
2. **Code review**: Peer review experimental code for production readiness
3. **Testing**: Develop test cases and validation procedures
4. **Production planning**: Plan integration with existing pipelines
5. **Knowledge transfer**: Share learnings with the broader team

### Failed Experiments
Even unsuccessful experiments provide value:
1. **Document lessons learned**: Record what didn't work and why
2. **Archive code**: Store failed experiments for future reference
3. **Update documentation**: Improve guidance based on common pitfalls
4. **Team sharing**: Discuss failures to prevent repeated mistakes

## Related Resources
- See `data_lake/docs/sandbox_guidelines.md` for detailed usage policies
- Check `data_lake/scripts/sandbox_cleanup.py` for automated maintenance
- Reference `data_lake/docs/promotion_process.md` for moving work to production
- Visit `data_lake/sandbox/examples/` for sample experiments and templates
