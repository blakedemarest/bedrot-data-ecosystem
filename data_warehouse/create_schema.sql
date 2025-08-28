-- BEDROT Data Warehouse Schema
-- Created: 2025-08-28
-- Based on: BEDROT_REFINED_WAREHOUSE_ERD.md

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- ======================
-- MASTER DATA TABLES
-- ======================

-- Artists table with ALL CAPS constraint
CREATE TABLE artists (
    artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_name TEXT NOT NULL UNIQUE CHECK (artist_name = UPPER(artist_name)),
    spotify_id TEXT,
    status TEXT CHECK (status IN ('active', 'inactive', 'archived')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tracks catalog
CREATE TABLE tracks (
    track_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    isrc TEXT UNIQUE, -- International Standard Recording Code
    upc TEXT, -- Universal Product Code
    release_date DATE,
    release_type TEXT CHECK (release_type IN ('single', 'ep', 'album')),
    genre TEXT, -- cybercore, sextrance, shoegaze, etc.
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Platforms (streaming, social, advertising)
CREATE TABLE platforms (
    platform_id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_name TEXT NOT NULL UNIQUE,
    platform_type TEXT CHECK (platform_type IN ('streaming', 'social', 'advertising', 'distribution')) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Territories (future geographic expansion ready)
CREATE TABLE territories (
    territory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_code TEXT NOT NULL UNIQUE, -- ISO 3166-1 alpha-2, DEFAULT: GLOBAL
    country_name TEXT,
    region TEXT, -- North America, Europe, Asia
    currency_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Track-Artist relationships with royalty splits
CREATE TABLE track_artists (
    track_artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    artist_id INTEGER NOT NULL,
    role_type TEXT CHECK (role_type IN ('primary', 'featured', 'producer')) DEFAULT 'primary',
    royalty_percentage DECIMAL(5,2) CHECK (royalty_percentage >= 0 AND royalty_percentage <= 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(track_id),
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id),
    UNIQUE(track_id, artist_id, role_type)
);

-- ======================
-- CONTENT PERFORMANCE TABLES
-- ======================

-- Content streams (single source of truth for consumption)
CREATE TABLE content_streams (
    stream_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_date DATE NOT NULL,
    track_id INTEGER, -- NULL for platform aggregates from tidy_daily_streams
    platform_id INTEGER NOT NULL,
    territory_id INTEGER NOT NULL DEFAULT 1, -- Default to GLOBAL
    data_source TEXT CHECK (data_source IN ('distrokid', 'toolost')) NOT NULL,
    stream_count BIGINT NOT NULL CHECK (stream_count >= 0),
    revenue_usd DECIMAL(10,4), -- Optional distributor revenue data
    extracted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(track_id),
    FOREIGN KEY (platform_id) REFERENCES platforms(platform_id),
    FOREIGN KEY (territory_id) REFERENCES territories(territory_id)
);

-- ======================
-- FINANCIAL OPERATIONS TABLES
-- ======================

-- Revenue transactions from distributors
CREATE TABLE revenue_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    reporting_date DATE NOT NULL,
    sale_month DATE, -- Actual month of consumption
    track_id INTEGER NOT NULL,
    platform_id INTEGER NOT NULL,
    territory_id INTEGER NOT NULL DEFAULT 1,
    quantity BIGINT NOT NULL, -- Streams/downloads
    gross_revenue_usd DECIMAL(10,4) NOT NULL,
    net_revenue_usd DECIMAL(10,4) NOT NULL, -- After platform fees
    royalty_rate DECIMAL(5,4), -- Platform revenue share
    distributor TEXT CHECK (distributor IN ('distrokid', 'toolost')) NOT NULL,
    extracted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(track_id),
    FOREIGN KEY (platform_id) REFERENCES platforms(platform_id),
    FOREIGN KEY (territory_id) REFERENCES territories(territory_id)
);

-- Business expenses tracking
CREATE TABLE business_expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_date DATE NOT NULL,
    posted_date DATE,
    description TEXT NOT NULL,
    category TEXT CHECK (category IN ('advertising', 'software', 'equipment', 'distribution', 'other')),
    amount_usd DECIMAL(10,2) NOT NULL,
    payment_method TEXT,
    status TEXT CHECK (status IN ('posted', 'pending', 'refunded')) DEFAULT 'posted',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ======================
-- MARKETING PERFORMANCE TABLES
-- ======================

-- Advertising campaigns
CREATE TABLE campaigns (
    campaign_id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_name TEXT NOT NULL,
    external_campaign_id TEXT, -- Meta platform ID
    platform_id INTEGER NOT NULL, -- Advertising platform
    primary_track_id INTEGER, -- Track being promoted
    parsed_artist TEXT, -- Extracted from campaign name (ALL CAPS)
    parsed_track TEXT, -- Extracted from campaign name
    parsed_targeting TEXT, -- BROAD, TECHNO, SPOTIFY, etc
    start_date DATE,
    end_date DATE,
    budget_usd DECIMAL(10,2),
    status TEXT CHECK (status IN ('active', 'paused', 'completed')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (platform_id) REFERENCES platforms(platform_id),
    FOREIGN KEY (primary_track_id) REFERENCES tracks(track_id)
);

-- Daily ad performance metrics
CREATE TABLE ad_performance_daily (
    performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    performance_date DATE NOT NULL,
    campaign_id INTEGER NOT NULL,
    impressions BIGINT DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    spend_usd DECIMAL(10,4) DEFAULT 0,
    cpm DECIMAL(10,4), -- Cost per thousand
    cpc DECIMAL(10,4), -- Cost per click
    ctr DECIMAL(6,4), -- Click-through rate
    conversion_events TEXT, -- Pixel data as JSON
    extracted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
);

-- Conversion events tracking
CREATE TABLE conversion_events (
    conversion_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_timestamp TIMESTAMP NOT NULL,
    campaign_id INTEGER NOT NULL,
    track_id INTEGER,
    conversion_type TEXT CHECK (conversion_type IN ('stream', 'follow', 'save', 'purchase')),
    conversion_value DECIMAL(10,4), -- Estimated value
    platform_event_id TEXT, -- Tracking ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
    FOREIGN KEY (track_id) REFERENCES tracks(track_id)
);

-- ======================
-- SOCIAL MEDIA ENGAGEMENT TABLES
-- ======================

-- TikTok daily metrics
CREATE TABLE tiktok_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    metrics_date DATE NOT NULL,
    artist_id INTEGER NOT NULL,
    account_handle TEXT, -- pig1987, zonea0
    video_views BIGINT DEFAULT 0,
    profile_views BIGINT DEFAULT 0,
    likes_received INTEGER DEFAULT 0,
    comments_received INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    new_followers INTEGER DEFAULT 0, -- Can be negative
    engagement_rate DECIMAL(6,4),
    extracted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
);

-- Linktree analytics
CREATE TABLE linktree_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    analytics_date DATE NOT NULL,
    artist_id INTEGER NOT NULL,
    total_views INTEGER DEFAULT 0,
    unique_views INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    unique_clicks INTEGER DEFAULT 0,
    click_through_rate DECIMAL(6,4),
    top_link TEXT, -- Most clicked link
    top_link_clicks INTEGER DEFAULT 0,
    extracted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
);

-- ======================
-- INDEXES FOR PERFORMANCE
-- ======================

-- Time-series query optimization
CREATE INDEX idx_content_streams_date ON content_streams(stream_date);
CREATE INDEX idx_content_streams_platform ON content_streams(platform_id);
CREATE INDEX idx_content_streams_track ON content_streams(track_id);

CREATE INDEX idx_revenue_transactions_date ON revenue_transactions(reporting_date);
CREATE INDEX idx_revenue_transactions_track ON revenue_transactions(track_id);

CREATE INDEX idx_ad_performance_date ON ad_performance_daily(performance_date);
CREATE INDEX idx_ad_performance_campaign ON ad_performance_daily(campaign_id);

CREATE INDEX idx_tiktok_metrics_date ON tiktok_metrics(metrics_date);
CREATE INDEX idx_tiktok_metrics_artist ON tiktok_metrics(artist_id);

CREATE INDEX idx_linktree_metrics_date ON linktree_metrics(analytics_date);
CREATE INDEX idx_linktree_metrics_artist ON linktree_metrics(artist_id);

-- ======================
-- TRIGGERS FOR UPDATED_AT
-- ======================

CREATE TRIGGER update_artists_timestamp 
    AFTER UPDATE ON artists
    BEGIN
        UPDATE artists SET updated_at = CURRENT_TIMESTAMP WHERE artist_id = NEW.artist_id;
    END;

CREATE TRIGGER update_tracks_timestamp 
    AFTER UPDATE ON tracks
    BEGIN
        UPDATE tracks SET updated_at = CURRENT_TIMESTAMP WHERE track_id = NEW.track_id;
    END;

CREATE TRIGGER update_platforms_timestamp 
    AFTER UPDATE ON platforms
    BEGIN
        UPDATE platforms SET updated_at = CURRENT_TIMESTAMP WHERE platform_id = NEW.platform_id;
    END;