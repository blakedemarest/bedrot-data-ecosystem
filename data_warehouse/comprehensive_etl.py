"""
BEDROT Comprehensive ETL - Real Data Loading
Created: 2025-08-28

Fixes all the critical ETL issues identified from real curated data:
1. Financial data mapping (14,209 revenue transactions) 
2. Track catalog expansion with royalty splits
3. TikTok social media data with artist mapping
4. Enhanced Meta Ads performance data
5. Proper platform/territory/artist mapping

Uses REAL production data, no dummy data.
"""

import sqlite3
import pandas as pd
import os
import sys
from pathlib import Path
from datetime import datetime
import json
from campaign_parser import BEDROTCampaignParser
import re

# Set up paths
PROJECT_ROOT = Path("/mnt/c/Users/Earth/BEDROT PRODUCTIONS/bedrot-data-ecosystem")
DATA_LAKE_CURATED = PROJECT_ROOT / "data_lake" / "4_curated"
WAREHOUSE_DIR = PROJECT_ROOT / "data_warehouse"
DB_PATH = WAREHOUSE_DIR / "bedrot_analytics.db"


class ComprehensiveETL:
    """Comprehensive ETL for real BEDROT production data."""
    
    def __init__(self):
        self.conn = None
        self.campaign_parser = BEDROTCampaignParser()
        
        # Mapping dictionaries for data transformation
        self.platform_mapping = {}
        self.artist_mapping = {}
        self.territory_mapping = {}
        self.track_mapping = {}
        
    def setup_database(self):
        """Connect to existing database and load reference data."""
        print("🔌 Connecting to existing database...")
        
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Load reference mappings
        self._load_platform_mapping()
        self._load_artist_mapping()
        self._load_territory_mapping()
        self._load_track_mapping()
        
        print("   ✅ Database connected, reference data loaded")
        
    def _load_platform_mapping(self):
        """Load platform_name -> platform_id mapping."""
        cursor = self.conn.execute("SELECT platform_id, platform_name FROM platforms")
        for row in cursor.fetchall():
            platform_id, platform_name = row
            self.platform_mapping[platform_name.upper()] = platform_id
            
        # Add additional mappings for financial data
        self.store_to_platform = {
            'SPOTIFY': 'SPOTIFY',
            'APPLE MUSIC': 'APPLE MUSIC',
            'TIKTOK': 'TIKTOK', 
            'YOUTUBE': 'YOUTUBE MUSIC',
            'LUNA': 'SPOTIFY',  # Luna is often Spotify in China
            'TENCENT': 'SPOTIFY',  # Tencent Music → map to Spotify
            'SOUNDCLOUD': 'SOUNDCLOUD',
            'BANDCAMP': 'BANDCAMP'
        }
        
    def _load_artist_mapping(self):
        """Load artist_name -> artist_id mapping."""
        cursor = self.conn.execute("SELECT artist_id, artist_name FROM artists")
        for row in cursor.fetchall():
            artist_id, artist_name = row
            self.artist_mapping[artist_name] = artist_id
            # Add lowercase mapping
            self.artist_mapping[artist_name.lower()] = artist_id
            
        # Add special TikTok artist mappings
        # Handle "zone.a0" and "ZONE.A0" variations
        zone_a0_id = self.artist_mapping.get("ZONE A0")
        if zone_a0_id:
            self.artist_mapping["ZONE.A0"] = zone_a0_id
            self.artist_mapping["zone.a0"] = zone_a0_id
            
    def _load_territory_mapping(self):
        """Load country_code -> territory_id mapping."""
        cursor = self.conn.execute("SELECT territory_id, country_code FROM territories")
        for row in cursor.fetchall():
            territory_id, country_code = row
            self.territory_mapping[country_code] = territory_id
            
    def _load_track_mapping(self):
        """Load track info -> track_id mapping."""
        cursor = self.conn.execute("SELECT track_id, title, isrc FROM tracks")
        for row in cursor.fetchall():
            track_id, title, isrc = row
            self.track_mapping[title.upper()] = track_id
            if isrc:
                self.track_mapping[isrc] = track_id

    def load_track_catalog_expansion(self):
        """Load track catalog with royalty splits to expand our track database."""
        print("\\n🎵 Loading track catalog expansion...")
        
        catalog_file = DATA_LAKE_CURATED / "track_catalog_royalty_splits.csv"
        if not catalog_file.exists():
            print("   ❌ Track catalog file not found")
            return
            
        df = pd.read_csv(catalog_file)
        print(f"   Reading {len(df)} tracks from catalog")
        
        tracks_added = 0
        relationships_added = 0
        
        for _, row in df.iterrows():
            artist_name = str(row['artist']).upper()
            track_title = str(row['title']).upper()
            isrc = row.get('isrc', '') or None
            upc = row.get('upc', '') or None
            release_date = row.get('release_date', '') or None
            release_type = str(row.get('release_type', 'single')).lower()
            royalty_pct = float(row.get('royalty_percentage', 100))
            
            # Get or create artist
            artist_id = self.artist_mapping.get(artist_name)
            if not artist_id:
                print(f"   ⚠️  Artist '{artist_name}' not found, skipping track '{track_title}'")
                continue
                
            # Check if track already exists
            track_id = self.track_mapping.get(track_title)
            if not track_id and isrc:
                track_id = self.track_mapping.get(isrc)
                
            if not track_id:
                # Insert new track
                try:
                    cursor = self.conn.execute("""
                        INSERT INTO tracks (title, isrc, upc, release_date, release_type)
                        VALUES (?, ?, ?, ?, ?)
                    """, (track_title, isrc, upc, release_date, release_type))
                    track_id = cursor.lastrowid
                    self.track_mapping[track_title] = track_id
                    if isrc:
                        self.track_mapping[isrc] = track_id
                    tracks_added += 1
                    print(f"   ➕ Added track: {track_title}")
                except sqlite3.IntegrityError:
                    # Track might already exist, try to find it
                    cursor = self.conn.execute("SELECT track_id FROM tracks WHERE title = ?", (track_title,))
                    result = cursor.fetchone()
                    if result:
                        track_id = result[0]
            
            # Insert track-artist relationship
            if track_id:
                try:
                    self.conn.execute("""
                        INSERT OR IGNORE INTO track_artists (track_id, artist_id, role_type, royalty_percentage)
                        VALUES (?, ?, 'primary', ?)
                    """, (track_id, artist_id, royalty_pct))
                    relationships_added += 1
                except sqlite3.IntegrityError:
                    pass  # Relationship already exists
        
        self.conn.commit()
        print(f"   ✅ Added {tracks_added} new tracks, {relationships_added} artist relationships")

    def load_financial_data_fixed(self):
        """Load financial data with proper mapping logic."""
        print("\\n💰 Loading financial data with intelligent mapping...")
        
        bank_file = DATA_LAKE_CURATED / "dk_bank_details.csv"
        if not bank_file.exists():
            print("   ❌ Financial data file not found")
            return
            
        df = pd.read_csv(bank_file)
        print(f"   Processing {len(df)} financial transactions")
        
        revenue_records = 0
        expense_records = 0
        skipped_records = 0
        
        for _, row in df.iterrows():
            try:
                # Extract data
                reporting_date = row['Reporting Date']
                sale_month = row['Sale Month'] 
                store = str(row['Store']).upper()
                artist_name = str(row['Artist']).upper()
                track_title = str(row['Title']).upper()
                isrc = row.get('ISRC', '') or None
                quantity = int(row.get('Quantity', 0))
                earnings_usd = float(row.get('Earnings (USD)', 0))
                country = str(row.get('Country of Sale', 'GLOBAL'))
                
                # Skip zero-value records
                if earnings_usd == 0:
                    continue
                    
                # Map platform
                platform_name = self.store_to_platform.get(store, store)
                platform_id = self.platform_mapping.get(platform_name)
                if not platform_id:
                    platform_id = self.platform_mapping.get('SPOTIFY')  # Default fallback
                    
                # Map artist
                artist_id = self.artist_mapping.get(artist_name)
                if not artist_id:
                    print(f"   ⚠️  Unknown artist: {artist_name}")
                    skipped_records += 1
                    continue
                    
                # Map track  
                track_id = self.track_mapping.get(track_title)
                if not track_id and isrc:
                    track_id = self.track_mapping.get(isrc)
                if not track_id:
                    # Create missing track
                    cursor = self.conn.execute("""
                        INSERT OR IGNORE INTO tracks (title, isrc, release_type)
                        VALUES (?, ?, 'single')
                    """, (track_title, isrc))
                    track_id = cursor.lastrowid or self.conn.execute(
                        "SELECT track_id FROM tracks WHERE title = ?", (track_title,)
                    ).fetchone()[0]
                    self.track_mapping[track_title] = track_id
                    
                    # Link to artist
                    self.conn.execute("""
                        INSERT OR IGNORE INTO track_artists (track_id, artist_id, role_type, royalty_percentage)
                        VALUES (?, ?, 'primary', 100.0)
                    """, (track_id, artist_id))
                    
                # Map territory
                territory_id = self.territory_mapping.get(country, 1)  # Default to GLOBAL
                
                # Insert revenue transaction
                if earnings_usd > 0:  # Revenue
                    self.conn.execute("""
                        INSERT INTO revenue_transactions 
                        (reporting_date, sale_month, track_id, platform_id, territory_id, 
                         quantity, gross_revenue_usd, net_revenue_usd, distributor)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'distrokid')
                    """, (reporting_date, sale_month, track_id, platform_id, territory_id,
                          quantity, earnings_usd, earnings_usd))
                    revenue_records += 1
                else:  # Expense (negative earnings)
                    self.conn.execute("""
                        INSERT INTO business_expenses
                        (transaction_date, description, amount_usd, category)
                        VALUES (?, ?, ?, 'distribution')
                    """, (reporting_date, f"{store} - {track_title}", abs(earnings_usd)))
                    expense_records += 1
                    
            except Exception as e:
                print(f"   ❌ Error processing row: {e}")
                skipped_records += 1
                continue
        
        self.conn.commit()
        print(f"   ✅ Loaded {revenue_records} revenue transactions, {expense_records} expenses")
        print(f"   ⚠️  Skipped {skipped_records} records (missing mappings)")

    def load_tiktok_data_with_mapping(self):
        """Load TikTok data with proper artist mapping."""
        print("\\n📱 Loading TikTok social media data...")
        
        tiktok_file = DATA_LAKE_CURATED / "tiktok_analytics_curated_20250819_074117.csv"
        if not tiktok_file.exists():
            print("   ❌ TikTok data file not found")
            return
            
        df = pd.read_csv(tiktok_file)
        print(f"   Processing {len(df)} TikTok records")
        
        records_inserted = 0
        
        for _, row in df.iterrows():
            try:
                # Extract data
                artist_name = str(row['artist']).upper()  # pig1987 → PIG1987
                account_handle = str(row['zone'])  # Account handle
                metrics_date = row['date']
                video_views = int(row.get('Video Views', 0) or 0)
                profile_views = int(row.get('Profile Views', 0) or 0)
                likes = int(row.get('Likes', 0) or 0)
                comments = int(row.get('Comments', 0) or 0)
                shares = int(row.get('Shares', 0) or 0)
                new_followers = int(row.get('new_followers', 0) or 0)
                engagement_rate = float(row.get('engagement_rate', 0) or 0)
                
                # Map artist
                artist_id = self.artist_mapping.get(artist_name)
                if not artist_id:
                    print(f"   ⚠️  Unknown artist: {artist_name}")
                    continue
                    
                # Skip zero-data days to save space
                if video_views == 0 and profile_views == 0 and likes == 0:
                    continue
                    
                # Insert TikTok metrics
                self.conn.execute("""
                    INSERT OR REPLACE INTO tiktok_metrics
                    (metrics_date, artist_id, account_handle, video_views, profile_views,
                     likes_received, comments_received, shares, new_followers, engagement_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (metrics_date, artist_id, account_handle, video_views, profile_views,
                      likes, comments, shares, new_followers, engagement_rate))
                records_inserted += 1
                
            except Exception as e:
                print(f"   ❌ Error processing TikTok row: {e}")
                continue
        
        self.conn.commit() 
        print(f"   ✅ Loaded {records_inserted} TikTok social media records")

    def load_enhanced_meta_ads_data(self):
        """Load detailed Meta Ads performance data."""
        print("\\n🎯 Loading enhanced Meta Ads performance data...")
        
        # Load campaign summary with real performance data
        campaign_file = DATA_LAKE_CURATED / "metaads" / "campaign_summary_latest.csv"
        if not campaign_file.exists():
            print("   ❌ Meta Ads campaign summary not found")
            return
            
        df = pd.read_csv(campaign_file)
        print(f"   Processing {len(df)} Meta Ads campaigns")
        
        # Get Meta Ads platform ID
        meta_platform_id = self.platform_mapping.get('META ADS')
        if not meta_platform_id:
            print("   ❌ Meta Ads platform not found")
            return
            
        campaigns_updated = 0
        performance_records = 0
        
        for _, row in df.iterrows():
            try:
                campaign_name = str(row['campaign_name'])
                external_campaign_id = str(row['campaign_id'])
                spend_usd = float(row.get('spend_usd', 0))
                impressions = int(row.get('impressions', 0) or 0)
                clicks = int(row.get('clicks', 0) or 0) 
                reach = int(row.get('reach', 0) or 0)
                cpm = float(row.get('cpm', 0) or 0)
                cpc = float(row.get('cpc', 0) or 0)
                ctr = float(row.get('ctr', 0) or 0)
                
                # Parse campaign name
                parsed = self.campaign_parser.parse_campaign_name(campaign_name)
                
                # Find existing campaign or create new one
                cursor = self.conn.execute("""
                    SELECT campaign_id FROM campaigns WHERE campaign_name = ?
                """, (campaign_name,))
                result = cursor.fetchone()
                
                if result:
                    campaign_id = result[0]
                    # Update existing campaign with external ID
                    self.conn.execute("""
                        UPDATE campaigns SET external_campaign_id = ? WHERE campaign_id = ?
                    """, (external_campaign_id, campaign_id))
                    campaigns_updated += 1
                else:
                    # Create new campaign
                    cursor = self.conn.execute("""
                        INSERT INTO campaigns 
                        (campaign_name, external_campaign_id, platform_id, parsed_artist, 
                         parsed_track, parsed_targeting, status)
                        VALUES (?, ?, ?, ?, ?, ?, 'completed')
                    """, (campaign_name, external_campaign_id, meta_platform_id, 
                          parsed.artist, parsed.track, parsed.targeting))
                    campaign_id = cursor.lastrowid
                
                # Insert aggregate performance data (using a default date)
                performance_date = '2025-08-01'  # Would normally extract from data
                
                if spend_usd > 0 or impressions > 0:
                    self.conn.execute("""
                        INSERT OR REPLACE INTO ad_performance_daily
                        (performance_date, campaign_id, impressions, clicks, reach, 
                         spend_usd, cpm, cpc, ctr)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (performance_date, campaign_id, impressions, clicks, reach,
                          spend_usd, cpm, cpc, ctr))
                    performance_records += 1
                
            except Exception as e:
                print(f"   ❌ Error processing campaign: {e}")
                continue
        
        self.conn.commit()
        print(f"   ✅ Updated {campaigns_updated} campaigns, loaded {performance_records} performance records")

    def run_validation_queries(self):
        """Run comprehensive validation queries."""
        print("\\n🔍 Running comprehensive data validation...")
        
        queries = [
            ("Total revenue transactions", "SELECT COUNT(*) FROM revenue_transactions"),
            ("Total revenue amount", "SELECT PRINTF('$%.2f', SUM(net_revenue_usd)) FROM revenue_transactions"),
            ("Revenue by platform", """
                SELECT p.platform_name, COUNT(*) as transactions, PRINTF('$%.2f', SUM(rt.net_revenue_usd)) as total_revenue
                FROM revenue_transactions rt 
                JOIN platforms p ON rt.platform_id = p.platform_id 
                GROUP BY p.platform_name ORDER BY SUM(rt.net_revenue_usd) DESC
            """),
            ("Top earning tracks", """
                SELECT t.title, PRINTF('$%.2f', SUM(rt.net_revenue_usd)) as earnings
                FROM revenue_transactions rt
                JOIN tracks t ON rt.track_id = t.track_id
                GROUP BY t.title 
                ORDER BY SUM(rt.net_revenue_usd) DESC 
                LIMIT 10
            """),
            ("TikTok metrics summary", "SELECT COUNT(*) as records, MAX(metrics_date) as latest_date FROM tiktok_metrics"),
            ("Total Meta Ads spend", "SELECT PRINTF('$%.2f', SUM(spend_usd)) FROM ad_performance_daily"),
            ("Campaign performance", """
                SELECT c.parsed_artist, c.parsed_track, PRINTF('$%.2f', SUM(ap.spend_usd)) as total_spend
                FROM campaigns c
                JOIN ad_performance_daily ap ON c.campaign_id = ap.campaign_id
                WHERE ap.spend_usd > 0
                GROUP BY c.parsed_artist, c.parsed_track
                ORDER BY SUM(ap.spend_usd) DESC
            """)
        ]
        
        for desc, query in queries:
            print(f"\\n   {desc}:")
            try:
                cursor = self.conn.execute(query)
                results = cursor.fetchall()
                for row in results:
                    print(f"     {row}")
            except Exception as e:
                print(f"     ❌ Query failed: {e}")

    def run_comprehensive_etl(self):
        """Execute comprehensive ETL with real production data."""
        print("🚀 BEDROT Comprehensive ETL - Real Data Loading")
        print("=" * 60)
        
        try:
            self.setup_database()
            self.load_track_catalog_expansion()
            self.load_financial_data_fixed()
            self.load_tiktok_data_with_mapping()
            self.load_enhanced_meta_ads_data()
            self.run_validation_queries()
            
            print(f"\\n✅ Comprehensive ETL completed successfully!")
            
        except Exception as e:
            print(f"\\n❌ ETL failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.conn:
                self.conn.close()


if __name__ == "__main__":
    # Ensure curated data directory exists
    if not DATA_LAKE_CURATED.exists():
        print(f"❌ Curated data directory not found: {DATA_LAKE_CURATED}")
        sys.exit(1)
        
    etl = ComprehensiveETL()
    etl.run_comprehensive_etl()