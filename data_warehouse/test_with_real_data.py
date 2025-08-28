"""
BEDROT Data Warehouse Real Data Testing
Created: 2025-08-28

Tests the database schema using REAL curated data from the data lake.
NO dummy data - only actual production data from 4_curated/.

This will ultrathink reveal actual ETL issues and validate our schema design.
"""

import sqlite3
import pandas as pd
import os
import sys
from pathlib import Path
from datetime import datetime
import json
from campaign_parser import BEDROTCampaignParser

# Set up paths
PROJECT_ROOT = Path("/mnt/c/Users/Earth/BEDROT PRODUCTIONS/bedrot-data-ecosystem")
DATA_LAKE_CURATED = PROJECT_ROOT / "data_lake" / "4_curated"
WAREHOUSE_DIR = PROJECT_ROOT / "data_warehouse"
DB_PATH = WAREHOUSE_DIR / "bedrot_analytics.db"

class RealDataTester:
    """Test database schema with actual curated data."""
    
    def __init__(self):
        self.conn = None
        self.campaign_parser = BEDROTCampaignParser()
        
    def setup_database(self):
        """Create database and run schema + seed scripts."""
        print("🏗️  Setting up database with schema and master data...")
        
        # Remove existing database
        if DB_PATH.exists():
            DB_PATH.unlink()
            print(f"   Removed existing database: {DB_PATH}")
        
        # Create new database
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Run schema creation
        schema_path = WAREHOUSE_DIR / "create_schema.sql"
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        self.conn.executescript(schema_sql)
        print("   ✅ Schema created")
        
        # Run master data seeding
        seed_path = WAREHOUSE_DIR / "seed_master_data.sql" 
        with open(seed_path, 'r') as f:
            seed_sql = f.read()
            
        self.conn.executescript(seed_sql)
        print("   ✅ Master data seeded")
        
        self.conn.commit()
        
    def get_platform_id(self, platform_name):
        """Get platform_id from database."""
        cursor = self.conn.execute(
            "SELECT platform_id FROM platforms WHERE platform_name = ?",
            (platform_name,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
        
    def get_artist_id(self, artist_name):
        """Get artist_id from database (ALL CAPS)."""
        cursor = self.conn.execute(
            "SELECT artist_id FROM artists WHERE artist_name = ?", 
            (artist_name.upper(),)
        )
        result = cursor.fetchone()
        return result[0] if result else None
        
    def get_track_id(self, track_title):
        """Get track_id from database."""
        cursor = self.conn.execute(
            "SELECT track_id FROM tracks WHERE title = ?",
            (track_title.upper(),)
        )
        result = cursor.fetchone()
        return result[0] if result else None

    def load_streaming_data(self):
        """Load tidy_daily_streams.csv with wide-to-tall transformation."""
        print("\n📊 Loading streaming data (tidy_daily_streams.csv)...")
        
        # Find the tidy_daily_streams file
        stream_files = list(DATA_LAKE_CURATED.glob("tidy_daily_streams*.csv"))
        if not stream_files:
            print("   ❌ No tidy_daily_streams.csv found")
            return
            
        stream_file = stream_files[0]
        print(f"   Reading: {stream_file.name}")
        
        df = pd.read_csv(stream_file)
        print(f"   Loaded {len(df)} rows")
        print(f"   Columns: {list(df.columns)}")
        
        # Get platform IDs
        spotify_id = self.get_platform_id("Spotify")
        apple_id = self.get_platform_id("Apple Music") 
        
        if not spotify_id or not apple_id:
            print("   ❌ Missing platform IDs")
            return
            
        # Transform wide to tall format
        records_inserted = 0
        
        for _, row in df.iterrows():
            stream_date = row['date']
            source = row['source']
            
            # Insert Spotify streams
            if pd.notna(row['spotify_streams']) and row['spotify_streams'] > 0:
                self.conn.execute("""
                    INSERT INTO content_streams 
                    (stream_date, platform_id, territory_id, data_source, stream_count)
                    VALUES (?, ?, 1, ?, ?)
                """, (stream_date, spotify_id, source, int(row['spotify_streams'])))
                records_inserted += 1
                
            # Insert Apple Music streams  
            if pd.notna(row['apple_streams']) and row['apple_streams'] > 0:
                self.conn.execute("""
                    INSERT INTO content_streams
                    (stream_date, platform_id, territory_id, data_source, stream_count) 
                    VALUES (?, ?, 1, ?, ?)
                """, (stream_date, apple_id, source, int(row['apple_streams'])))
                records_inserted += 1
        
        self.conn.commit()
        print(f"   ✅ Inserted {records_inserted} stream records")

    def load_financial_data(self):
        """Load dk_bank_details.csv revenue data."""
        print("\n💰 Loading financial data (dk_bank_details.csv)...")
        
        bank_files = list(DATA_LAKE_CURATED.glob("dk_bank_details*.csv"))
        if not bank_files:
            print("   ❌ No dk_bank_details.csv found")
            return
            
        bank_file = bank_files[0] 
        print(f"   Reading: {bank_file.name}")
        
        df = pd.read_csv(bank_file)
        print(f"   Loaded {len(df)} rows")
        print(f"   Columns: {list(df.columns)}")
        
        # Get platform IDs for revenue mapping
        spotify_id = self.get_platform_id("Spotify")
        apple_id = self.get_platform_id("Apple Music")
        
        records_inserted = 0
        
        for _, row in df.iterrows():
            # Try to determine platform from description or other fields
            description = str(row.get('description', '')).upper()
            platform_id = spotify_id  # Default to Spotify
            
            if 'APPLE' in description:
                platform_id = apple_id
                
            # Insert as business expense if it's a cost, or revenue transaction if it's income
            amount = float(row.get('amount', 0))
            
            if amount < 0:  # Expense
                self.conn.execute("""
                    INSERT INTO business_expenses 
                    (transaction_date, description, amount_usd, category)
                    VALUES (?, ?, ?, 'distribution')
                """, (row.get('date'), str(row.get('description', '')), abs(amount)))
                records_inserted += 1
            elif amount > 0:  # Revenue 
                # Would need track mapping logic here - for now skip or create generic
                pass
                
        self.conn.commit()
        print(f"   ✅ Inserted {records_inserted} financial records")

    def load_campaign_data(self):
        """Load Meta ads campaign data with parsing."""
        print("\n🎯 Loading campaign data with parsing...")
        
        # Look for Meta ads files
        meta_files = list(DATA_LAKE_CURATED.glob("*meta*campaign*.csv")) + \
                    list(DATA_LAKE_CURATED.glob("*metaads*.csv"))
                    
        if not meta_files:
            print("   ❌ No Meta ads campaign files found")
            return
            
        for meta_file in meta_files[:1]:  # Test with first file
            print(f"   Reading: {meta_file.name}")
            
            df = pd.read_csv(meta_file)
            print(f"   Loaded {len(df)} rows") 
            print(f"   Columns: {list(df.columns)}")
            
            # Get Meta Ads platform ID
            meta_platform_id = self.get_platform_id("Meta Ads")
            if not meta_platform_id:
                print("   ❌ Meta Ads platform not found")
                continue
                
            records_inserted = 0
            
            for _, row in df.iterrows():
                campaign_name = str(row.get('campaign_name', ''))
                if not campaign_name or campaign_name == 'nan':
                    continue
                    
                # Parse campaign name
                parsed = self.campaign_parser.parse_campaign_name(campaign_name)
                
                print(f"   📝 Parsed '{campaign_name}' -> Artist: {parsed.artist}, Track: {parsed.track}, Targeting: {parsed.targeting}")
                
                # Insert campaign
                cursor = self.conn.execute("""
                    INSERT INTO campaigns 
                    (campaign_name, platform_id, parsed_artist, parsed_track, parsed_targeting, status)
                    VALUES (?, ?, ?, ?, ?, 'completed')
                """, (campaign_name, meta_platform_id, parsed.artist, parsed.track, parsed.targeting))
                
                campaign_id = cursor.lastrowid
                
                # Insert ad performance if we have the data
                spend = row.get('spend_usd', 0)
                impressions = row.get('impressions', 0)
                clicks = row.get('clicks', 0)
                reach = row.get('reach', 0)
                
                if spend > 0 or impressions > 0:
                    # Use a default date - would normally parse from filename or row
                    performance_date = '2025-08-01'
                    
                    self.conn.execute("""
                        INSERT INTO ad_performance_daily
                        (performance_date, campaign_id, impressions, clicks, reach, spend_usd)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (performance_date, campaign_id, impressions or 0, clicks or 0, reach or 0, spend or 0))
                
                records_inserted += 1
                
            self.conn.commit()
            print(f"   ✅ Inserted {records_inserted} campaign records")

    def load_tiktok_data(self):
        """Load TikTok analytics data.""" 
        print("\n📱 Loading TikTok data...")
        
        tiktok_files = list(DATA_LAKE_CURATED.glob("*tiktok*.csv"))
        if not tiktok_files:
            print("   ❌ No TikTok files found")
            return
            
        tiktok_file = tiktok_files[0]
        print(f"   Reading: {tiktok_file.name}")
        
        df = pd.read_csv(tiktok_file)
        print(f"   Loaded {len(df)} rows")
        print(f"   Columns: {list(df.columns)}")
        
        # For now, just report what we found - would need artist mapping logic
        print("   ℹ️  TikTok data structure analyzed (artist mapping needed for insertion)")

    def run_validation_queries(self):
        """Run queries to validate data was loaded correctly."""
        print("\n🔍 Validating loaded data...")
        
        queries = [
            ("Total stream records", "SELECT COUNT(*) FROM content_streams"),
            ("Total campaigns", "SELECT COUNT(*) FROM campaigns"), 
            ("Total expenses", "SELECT COUNT(*) FROM business_expenses"),
            ("Platforms with data", "SELECT p.platform_name, COUNT(cs.stream_id) as streams FROM platforms p LEFT JOIN content_streams cs ON p.platform_id = cs.platform_id GROUP BY p.platform_name"),
            ("Campaign parsing results", "SELECT parsed_artist, parsed_track, COUNT(*) as count FROM campaigns WHERE parsed_artist IS NOT NULL GROUP BY parsed_artist, parsed_track")
        ]
        
        for desc, query in queries:
            print(f"\n   {desc}:")
            cursor = self.conn.execute(query)
            results = cursor.fetchall()
            for row in results:
                print(f"     {row}")

    def run_test(self):
        """Execute complete test with real data."""
        print("🧪 BEDROT Database Real Data Test")
        print("=" * 50)
        
        try:
            self.setup_database()
            self.load_streaming_data()
            self.load_financial_data() 
            self.load_campaign_data()
            self.load_tiktok_data()
            self.run_validation_queries()
            
            print(f"\n✅ Test completed! Database created at: {DB_PATH}")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.conn:
                self.conn.close()

if __name__ == "__main__":
    # Ensure we're in the right directory
    if not DATA_LAKE_CURATED.exists():
        print(f"❌ Curated data directory not found: {DATA_LAKE_CURATED}")
        sys.exit(1)
        
    tester = RealDataTester()
    tester.run_test()