"""
BEDROT Data Warehouse - SQLite Database Schema Creation
Creates normalized 3NF database structure for BEDROT Productions analytics.

Database Location: /data-warehouse/bedrot_analytics.db
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

# Database configuration
DB_PATH = Path(__file__).parent / "bedrot_analytics.db"
ECOSYSTEM_ROOT = Path(__file__).parent.parent
DATA_LAKE_PATH = ECOSYSTEM_ROOT / "data_lake"

def get_connection():
    """Create database connection with optimized settings for analytics."""
    conn = sqlite3.connect(str(DB_PATH))
    
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Optimize for analytical queries
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL") 
    conn.execute("PRAGMA cache_size = 10000")
    conn.execute("PRAGMA temp_store = memory")
    
    return conn

def create_artists_table(conn):
    """Create Artists table - Musical artists and their metadata."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
            artist_name TEXT NOT NULL UNIQUE,
            spotify_artist_id TEXT UNIQUE,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    
    # Create indexes for performance
    conn.execute("CREATE INDEX IF NOT EXISTS idx_artists_name ON artists(artist_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_artists_spotify_id ON artists(spotify_artist_id)")

def create_platforms_table(conn):
    """Create Platforms table - Distribution and streaming platforms."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS platforms (
            platform_id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform_name TEXT NOT NULL UNIQUE,
            platform_type TEXT NOT NULL CHECK (platform_type IN ('Streaming', 'Social', 'Distribution', 'Advertising', 'Analytics')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    
    conn.execute("CREATE INDEX IF NOT EXISTS idx_platforms_name ON platforms(platform_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_platforms_type ON platforms(platform_type)")

def create_tracks_table(conn):
    """Create Tracks table - Musical tracks and albums."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            track_id INTEGER PRIMARY KEY AUTOINCREMENT,
            artist_id INTEGER NOT NULL,
            track_title TEXT NOT NULL,
            isrc TEXT UNIQUE,
            upc TEXT,
            content_type TEXT NOT NULL CHECK (content_type IN ('Song', 'Album')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
        )
    """)
    
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_artist_id ON tracks(artist_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_title ON tracks(track_title)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_isrc ON tracks(isrc)")

def create_campaigns_table(conn):
    """Create Campaigns table - Marketing and advertising campaigns."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            campaign_id INTEGER PRIMARY KEY,
            artist_id INTEGER NOT NULL,
            platform_id INTEGER NOT NULL,
            campaign_name TEXT NOT NULL,
            campaign_objective TEXT,
            status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'PAUSED', 'COMPLETED')),
            start_date TEXT,
            end_date TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (artist_id) REFERENCES artists(artist_id),
            FOREIGN KEY (platform_id) REFERENCES platforms(platform_id)
        )
    """)
    
    conn.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_artist_id ON campaigns(artist_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_platform_id ON campaigns(platform_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status)")

def create_financial_transactions_table(conn):
    """Create Financial_Transactions table - All financial records."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS financial_transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            category TEXT,
            status TEXT,
            source_platform_id INTEGER,
            artist_id INTEGER,
            track_id INTEGER,
            country TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (source_platform_id) REFERENCES platforms(platform_id),
            FOREIGN KEY (artist_id) REFERENCES artists(artist_id),
            FOREIGN KEY (track_id) REFERENCES tracks(track_id)
        )
    """)
    
    conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_date_artist ON financial_transactions(transaction_date, artist_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_platform ON financial_transactions(source_platform_id)")

def create_streaming_performance_table(conn):
    """Create Streaming_Performance table - Daily streaming and audience metrics."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS streaming_performance (
            performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            artist_id INTEGER NOT NULL,
            platform_id INTEGER NOT NULL,
            track_id INTEGER,
            listeners INTEGER DEFAULT 0,
            streams INTEGER DEFAULT 0,
            followers INTEGER DEFAULT 0,
            data_source TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (artist_id) REFERENCES artists(artist_id),
            FOREIGN KEY (platform_id) REFERENCES platforms(platform_id),
            FOREIGN KEY (track_id) REFERENCES tracks(track_id)
        )
    """)
    
    conn.execute("CREATE INDEX IF NOT EXISTS idx_streaming_date_artist ON streaming_performance(date, artist_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_streaming_platform ON streaming_performance(platform_id)")

def create_social_media_performance_table(conn):
    """Create Social_Media_Performance table - Social media engagement metrics."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS social_media_performance (
            social_performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            artist_id INTEGER NOT NULL,
            platform_id INTEGER NOT NULL,
            video_views INTEGER DEFAULT 0,
            profile_views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0.0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (artist_id) REFERENCES artists(artist_id),
            FOREIGN KEY (platform_id) REFERENCES platforms(platform_id)
        )
    """)
    
    conn.execute("CREATE INDEX IF NOT EXISTS idx_social_date_artist ON social_media_performance(date, artist_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_social_platform ON social_media_performance(platform_id)")

def create_advertising_performance_table(conn):
    """Create Advertising_Performance table - Daily advertising campaign performance."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS advertising_performance (
            ad_performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            campaign_id INTEGER NOT NULL,
            spend_usd REAL DEFAULT 0.0,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            reach INTEGER DEFAULT 0,
            cpc REAL DEFAULT 0.0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
        )
    """)
    
    conn.execute("CREATE INDEX IF NOT EXISTS idx_advertising_date_campaign ON advertising_performance(date, campaign_id)")

def create_meta_pixel_events_table(conn):
    """Create Meta_Pixel_Events table - Meta advertising pixel events."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meta_pixel_events (
            pixel_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_performance_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_count INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (ad_performance_id) REFERENCES advertising_performance(ad_performance_id)
        )
    """)
    
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pixel_events_performance ON meta_pixel_events(ad_performance_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pixel_events_type ON meta_pixel_events(event_type)")

def create_link_analytics_table(conn):
    """Create Link_Analytics table - Link tracking and conversion data."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS link_analytics (
            link_analytics_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            artist_id INTEGER NOT NULL,
            track_id INTEGER,
            link_id TEXT NOT NULL,
            source TEXT,
            country TEXT,
            utm_campaign TEXT,
            utm_source TEXT,
            utm_medium TEXT,
            opened INTEGER DEFAULT 0,
            clicked INTEGER DEFAULT 0,
            conversion_rate REAL DEFAULT 0.0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (artist_id) REFERENCES artists(artist_id),
            FOREIGN KEY (track_id) REFERENCES tracks(track_id)
        )
    """)
    
    conn.execute("CREATE INDEX IF NOT EXISTS idx_link_analytics_date_artist ON link_analytics(date, artist_id)")

def seed_platform_data(conn):
    """Seed Platforms table with known platforms from the data."""
    platforms = [
        ('Spotify', 'Streaming'),
        ('Apple Music', 'Streaming'),
        ('YouTube', 'Streaming'),
        ('TikTok', 'Social'),
        ('Meta Ads', 'Advertising'),
        ('Instagram', 'Social'),
        ('DistroKid', 'Distribution'),
        ('Linktree', 'Analytics'),
        ('SubmitHub', 'Analytics'),
        ('Capitol One', 'Financial'),
        ('ToolOst', 'Analytics')
    ]
    
    conn.executemany(
        "INSERT OR IGNORE INTO platforms (platform_name, platform_type) VALUES (?, ?)",
        platforms
    )

def create_database_info_table(conn):
    """Create table to track database metadata and ETL runs."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS database_info (
            info_id INTEGER PRIMARY KEY AUTOINCREMENT,
            schema_version TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_etl_run TEXT,
            total_records INTEGER DEFAULT 0,
            data_sources TEXT
        )
    """)
    
    # Insert initial database info
    conn.execute("""
        INSERT OR REPLACE INTO database_info 
        (info_id, schema_version, data_sources) 
        VALUES (1, '1.0.0', 'CSV Files from BEDROT Data Lake')
    """)

def create_database():
    """Create complete BEDROT analytics database with all tables."""
    print(f"Creating BEDROT Analytics Database at: {DB_PATH}")
    
    # Remove existing database if it exists
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Removed existing database")
    
    # Create database and tables
    conn = get_connection()
    
    try:
        print("Creating tables...")
        
        # Create all tables in dependency order
        create_artists_table(conn)
        print("✓ Artists table created")
        
        create_platforms_table(conn)
        print("✓ Platforms table created")
        
        create_tracks_table(conn)
        print("✓ Tracks table created")
        
        create_campaigns_table(conn)
        print("✓ Campaigns table created")
        
        create_financial_transactions_table(conn)
        print("✓ Financial_Transactions table created")
        
        create_streaming_performance_table(conn)
        print("✓ Streaming_Performance table created")
        
        create_social_media_performance_table(conn)
        print("✓ Social_Media_Performance table created")
        
        create_advertising_performance_table(conn)
        print("✓ Advertising_Performance table created")
        
        create_meta_pixel_events_table(conn)
        print("✓ Meta_Pixel_Events table created")
        
        create_link_analytics_table(conn)
        print("✓ Link_Analytics table created")
        
        create_database_info_table(conn)
        print("✓ Database_Info table created")
        
        # Seed platform data
        seed_platform_data(conn)
        print("✓ Platform data seeded")
        
        conn.commit()
        print(f"\n🎉 Database created successfully!")
        print(f"Location: {DB_PATH}")
        print(f"Size: {DB_PATH.stat().st_size / 1024:.1f} KB")
        
        # Show table count
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables created: {len(tables)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def show_database_info():
    """Display database schema information."""
    if not DB_PATH.exists():
        print("Database does not exist. Run create_database() first.")
        return
    
    conn = get_connection()
    
    try:
        print(f"\n📊 BEDROT Analytics Database Info")
        print(f"Location: {DB_PATH}")
        print(f"Size: {DB_PATH.stat().st_size / 1024:.1f} KB")
        
        # Show tables
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\nTables ({len(tables)}):")
        for table in tables:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count:,} records")
        
        # Show database info
        cursor = conn.execute("SELECT * FROM database_info WHERE info_id = 1")
        info = cursor.fetchone()
        if info:
            print(f"\nSchema Version: {info[1]}")
            print(f"Created: {info[2]}")
            print(f"Last ETL Run: {info[3] or 'Never'}")
            print(f"Total Records: {info[4]:,}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    create_database()
    show_database_info()