"""Revenue calculator service with distributor tracking."""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from backend.data.csv_loader import CSVDataLoader

logger = logging.getLogger(__name__)

class RevenueCalculator:
    """Calculate revenue metrics with distributor and delay tracking."""
    
    # Revenue per stream rates (discovered from analysis)
    RPS_RATES = {
        'spotify': 0.002274,
        'apple_music': 0.005771,
        'apple': 0.005771,  # Alias
        'youtube': 0.001000,  # Estimated
        'tidal': 0.012500,  # Industry average
        'amazon': 0.004000,  # Industry average
        'default': 0.002486  # Overall average
    }
    
    # Payment delay by distributor (in days)
    PAYMENT_DELAYS = {
        'distrokid': 60,  # 2 months average
        'toolost': 60,    # 2 months average
        'default': 60
    }
    
    def __init__(self):
        self.loader = CSVDataLoader()
        self._revenue_data = None
        self._streaming_data = None
        
    def _load_data(self, force_reload: bool = False):
        """Load revenue and streaming data."""
        if not force_reload and self._revenue_data and self._streaming_data:
            return
        
        # Load revenue data
        self._revenue_data = self.loader.load_csv('dk_bank_details.csv', force_reload)
        
        # Load streaming data
        self._streaming_data = self.loader.load_csv('tidy_daily_streams.csv', force_reload)
    
    def get_revenue_by_platform(self) -> Dict[str, Dict[str, float]]:
        """Calculate revenue breakdown by platform.
        
        Returns:
            Dictionary with platform statistics
        """
        self._load_data()
        
        platform_stats = defaultdict(lambda: {
            'total_revenue': 0.0,
            'total_streams': 0,
            'revenue_per_stream': 0.0,
            'transaction_count': 0
        })
        
        for row in self._revenue_data:
            platform = row.get('Store', 'Unknown')
            earnings = float(row.get('Earnings (USD)', 0))
            quantity = int(row.get('Quantity', 0))
            
            platform_stats[platform]['total_revenue'] += earnings
            platform_stats[platform]['total_streams'] += quantity
            platform_stats[platform]['transaction_count'] += 1
        
        # Calculate RPS for each platform
        for platform, stats in platform_stats.items():
            if stats['total_streams'] > 0:
                stats['revenue_per_stream'] = stats['total_revenue'] / stats['total_streams']
        
        return dict(platform_stats)
    
    def get_revenue_by_artist(self) -> Dict[str, Dict[str, float]]:
        """Calculate revenue breakdown by artist.
        
        Returns:
            Dictionary with artist statistics
        """
        self._load_data()
        
        artist_stats = defaultdict(lambda: {
            'total_revenue': 0.0,
            'total_streams': 0,
            'transaction_count': 0,
            'platforms': set()
        })
        
        for row in self._revenue_data:
            artist = row.get('Artist', 'Unknown')
            earnings = float(row.get('Earnings (USD)', 0))
            quantity = int(row.get('Quantity', 0))
            platform = row.get('Store', 'Unknown')
            
            artist_stats[artist]['total_revenue'] += earnings
            artist_stats[artist]['total_streams'] += quantity
            artist_stats[artist]['transaction_count'] += 1
            artist_stats[artist]['platforms'].add(platform)
        
        # Convert sets to lists for JSON serialization
        for artist, stats in artist_stats.items():
            stats['platforms'] = list(stats['platforms'])
            stats['platform_count'] = len(stats['platforms'])
        
        return dict(artist_stats)
    
    def get_revenue_by_distributor(self) -> Dict[str, Dict[str, Any]]:
        """Calculate revenue by distributor (DistroKid vs TooLost).
        
        Returns:
            Dictionary with distributor statistics
        """
        self._load_data()
        
        # Analyze streaming data for distributor breakdown
        distributor_stats = defaultdict(lambda: {
            'days_active': 0,
            'total_streams': 0,
            'spotify_streams': 0,
            'apple_streams': 0,
            'estimated_revenue': 0.0
        })
        
        for row in self._streaming_data:
            source = row.get('source', 'unknown')
            spotify = int(row.get('spotify_streams', 0))
            apple = int(row.get('apple_streams', 0))
            
            distributor_stats[source]['days_active'] += 1
            distributor_stats[source]['spotify_streams'] += spotify
            distributor_stats[source]['apple_streams'] += apple
            distributor_stats[source]['total_streams'] += spotify + apple
            
            # Calculate estimated revenue
            spotify_revenue = spotify * self.RPS_RATES['spotify']
            apple_revenue = apple * self.RPS_RATES['apple']
            distributor_stats[source]['estimated_revenue'] += spotify_revenue + apple_revenue
        
        return dict(distributor_stats)
    
    def get_monthly_revenue(self, include_expected: bool = True) -> List[Dict[str, Any]]:
        """Get monthly revenue with expected vs actual tracking.
        
        Args:
            include_expected: Include expected revenue calculations
            
        Returns:
            List of monthly revenue records
        """
        self._load_data()
        
        # Group actual revenue by month
        actual_by_month = defaultdict(lambda: {
            'actual_revenue': 0.0,
            'transaction_count': 0,
            'platforms': set()
        })
        
        for row in self._revenue_data:
            sale_month = row.get('Sale Month', '')
            if not sale_month:
                continue
                
            earnings = float(row.get('Earnings (USD)', 0))
            platform = row.get('Store', 'Unknown')
            
            actual_by_month[sale_month]['actual_revenue'] += earnings
            actual_by_month[sale_month]['transaction_count'] += 1
            actual_by_month[sale_month]['platforms'].add(platform)
        
        # Group streaming data by month for expected revenue
        expected_by_month = defaultdict(lambda: {
            'spotify_streams': 0,
            'apple_streams': 0,
            'total_streams': 0,
            'expected_revenue': 0.0
        })
        
        if include_expected:
            for row in self._streaming_data:
                date_str = row.get('date', '')
                if not date_str:
                    continue
                
                # Extract month from date
                try:
                    month = date_str[:7]  # YYYY-MM format
                except:
                    continue
                
                spotify = int(row.get('spotify_streams', 0))
                apple = int(row.get('apple_streams', 0))
                
                expected_by_month[month]['spotify_streams'] += spotify
                expected_by_month[month]['apple_streams'] += apple
                expected_by_month[month]['total_streams'] += spotify + apple
                
                # Calculate expected revenue
                spotify_revenue = spotify * self.RPS_RATES['spotify']
                apple_revenue = apple * self.RPS_RATES['apple']
                expected_by_month[month]['expected_revenue'] += spotify_revenue + apple_revenue
        
        # Combine actual and expected
        all_months = set(actual_by_month.keys()) | set(expected_by_month.keys())
        monthly_data = []
        
        for month in sorted(all_months):
            record = {
                'month': month,
                'actual_revenue': actual_by_month[month]['actual_revenue'],
                'transaction_count': actual_by_month[month]['transaction_count'],
                'platforms': list(actual_by_month[month]['platforms']),
                'expected_revenue': expected_by_month[month]['expected_revenue'],
                'spotify_streams': expected_by_month[month]['spotify_streams'],
                'apple_streams': expected_by_month[month]['apple_streams'],
                'total_streams': expected_by_month[month]['total_streams'],
                'variance': actual_by_month[month]['actual_revenue'] - expected_by_month[month]['expected_revenue']
            }
            
            # Calculate payment status based on delay
            try:
                month_date = datetime.strptime(month, '%Y-%m')
                payment_date = month_date + timedelta(days=self.PAYMENT_DELAYS['default'])
                record['payment_status'] = 'paid' if payment_date <= datetime.now() else 'pending'
                record['expected_payment_date'] = payment_date.strftime('%Y-%m-%d')
            except:
                record['payment_status'] = 'unknown'
                record['expected_payment_date'] = None
            
            monthly_data.append(record)
        
        return monthly_data
    
    def get_payment_delays(self) -> Dict[str, Any]:
        """Analyze payment delay patterns.
        
        Returns:
            Dictionary with delay statistics
        """
        self._load_data()
        
        delays = []
        delay_counts = defaultdict(int)
        
        for row in self._revenue_data:
            try:
                report_date = datetime.strptime(row['Reporting Date'], '%Y-%m-%d')
                sale_month = datetime.strptime(row['Sale Month'], '%Y-%m')
                
                delay_months = (report_date.year - sale_month.year) * 12 + (report_date.month - sale_month.month)
                delays.append(delay_months)
                delay_counts[delay_months] += 1
            except:
                continue
        
        if not delays:
            return {
                'average_delay_months': 0,
                'most_common_delay_months': 0,
                'delay_distribution': {}
            }
        
        # Calculate statistics
        total_transactions = len(delays)
        
        return {
            'average_delay_months': sum(delays) / len(delays),
            'most_common_delay_months': max(delay_counts, key=delay_counts.get),
            'delay_distribution': {
                str(delay): {
                    'count': count,
                    'percentage': (count / total_transactions) * 100
                }
                for delay, count in sorted(delay_counts.items())
            },
            'total_transactions_analyzed': total_transactions
        }
    
    def get_summary_kpis(self) -> Dict[str, Any]:
        """Get summary KPIs for dashboard.
        
        Returns:
            Dictionary with key performance indicators
        """
        self._load_data()
        
        # Calculate totals
        total_revenue = sum(float(row.get('Earnings (USD)', 0)) for row in self._revenue_data)
        total_streams = sum(int(row.get('Quantity', 0)) for row in self._revenue_data)
        
        # Get current month
        current_month = datetime.now().strftime('%Y-%m')
        
        # Calculate this month's metrics
        current_month_revenue = sum(
            float(row.get('Earnings (USD)', 0))
            for row in self._revenue_data
            if row.get('Sale Month', '').startswith(current_month)
        )
        
        # Get artist breakdown
        artist_stats = self.get_revenue_by_artist()
        
        # Get distributor breakdown
        distributor_stats = self.get_revenue_by_distributor()
        
        return {
            'total_revenue': total_revenue,
            'total_streams': total_streams,
            'average_revenue_per_stream': total_revenue / total_streams if total_streams > 0 else 0,
            'current_month_revenue': current_month_revenue,
            'artist_count': len(artist_stats),
            'top_artist': max(artist_stats.items(), key=lambda x: x[1]['total_revenue'])[0] if artist_stats else None,
            'distributor_breakdown': {
                'distrokid': distributor_stats.get('distrokid', {}).get('estimated_revenue', 0),
                'toolost': distributor_stats.get('toolost', {}).get('estimated_revenue', 0)
            },
            'last_updated': datetime.now().isoformat()
        }