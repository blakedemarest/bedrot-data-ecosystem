-- BEDROT Data Warehouse DDL Schema
-- Compatible with SQLite 3.37+ and PostgreSQL 13+
-- Generated from ERD: 21 tables with full normalization

-- =============================================================================
-- MASTER DATA TABLES
-- =============================================================================

-- Artists table: Multi-persona support (PIG1987, ZONE A0, xXMeatWarriorXx)
CREATE TABLE artists (
    artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_name VARCHAR(100) NOT NULL UNIQUE,
    spotify_id VARCHAR(50),
    legal_name VARCHAR(200),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tracks table: Catalog with ISRC/UPC metadata
CREATE TABLE tracks (
    track_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    isrc VARCHAR(12) UNIQUE, -- International Standard Recording Code
    upc VARCHAR(13), -- Universal Product Code (album level)
    release_date DATE,
    release_type VARCHAR(20) CHECK (release_type IN ('single', 'ep', 'album')),
    genre VARCHAR(50),
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Platforms table: Streaming/marketing platforms
CREATE TABLE platforms (
    platform_id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_name VARCHAR(50) NOT NULL UNIQUE,
    platform_type VARCHAR(20) CHECK (platform_type IN ('streaming', 'social', 'advertising', 'distribution')),
    api_endpoint VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Territories table: Geographic analysis support
CREATE TABLE territories (
    territory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_code VARCHAR(2) NOT NULL UNIQUE, -- ISO 3166-1 alpha-2
    country_name VARCHAR(100) NOT NULL,
    region VARCHAR(50),
    currency_code VARCHAR(3), -- ISO currency code
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaigns table: Cross-platform marketing campaigns
CREATE TABLE campaigns (
    campaign_id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_name VARCHAR(200) NOT NULL,
    external_campaign_id VARCHAR(100),
    platform_id INTEGER NOT NULL,
    primary_track_id INTEGER NOT NULL,
    start_date DATE,
    end_date DATE,
    budget_usd DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'completed')),
    campaign_settings TEXT, -- JSON as TEXT for SQLite compatibility
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (platform_id) REFERENCES platforms(platform_id),
    FOREIGN KEY (primary_track_id) REFERENCES tracks(track_id),
    CHECK (end_date >= start_date),
    CHECK (budget_usd > 0)
);

-- =============================================================================
-- STREAMING ANALYTICS TABLES
-- =============================================================================

-- Daily Streams: Platform totals with double-counting prevention
CREATE TABLE daily_streams (
    stream_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_date DATE NOT NULL,
    track_id INTEGER,
    platform_id INTEGER NOT NULL,
    territory_id INTEGER NOT NULL,
    data_source VARCHAR(20) NOT NULL CHECK (data_source IN ('distrokid', 'toolost', 'spotify_api')),
    stream_count BIGINT NOT NULL CHECK (stream_count >= 0),
    revenue_usd DECIMAL(12,4),
    extracted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(track_id),
    FOREIGN KEY (platform_id) REFERENCES platforms(platform_id),
    FOREIGN KEY (territory_id) REFERENCES territories(territory_id)
);

-- Spotify Audience: API demographics (separate to avoid double-counting)
CREATE TABLE spotify_audience (
    audience_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date DATE NOT NULL,
    artist_id INTEGER NOT NULL,
    monthly_listeners INTEGER,
    followers INTEGER,
    streams_28d BIGINT,
    cities_count INTEGER,
    countries_count INTEGER,
    demographic_data TEXT, -- JSON as TEXT
    extracted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
);

-- Playlist Placements: Track positioning data
CREATE TABLE playlist_placements (
    placement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    platform_id INTEGER NOT NULL,
    playlist_name VARCHAR(200),
    playlist_id VARCHAR(100),
    position INTEGER,
    added_date DATE,
    removed_date DATE,
    estimated_reach INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(track_id),
    FOREIGN KEY (platform_id) REFERENCES platforms(platform_id)
);

-- Stream Attribution: Campaign → stream conversion tracking
CREATE TABLE stream_attribution (
    attribution_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_record_id INTEGER NOT NULL,
    campaign_id INTEGER,
    attribution_type VARCHAR(20) CHECK (attribution_type IN ('organic', 'paid', 'viral', 'playlist')),
    attribution_weight DECIMAL(3,2) CHECK (attribution_weight BETWEEN 0.0 AND 1.0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stream_record_id) REFERENCES daily_streams(stream_record_id),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
);

-- =============================================================================
-- FINANCIAL TABLES
-- =============================================================================

-- Royalty Transactions: DistroKid/TooLost earnings
CREATE TABLE royalty_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    reporting_date DATE NOT NULL,
    sale_month DATE NOT NULL,
    track_id INTEGER,
    platform_id INTEGER NOT NULL,
    territory_id INTEGER NOT NULL,
    transaction_type VARCHAR(20) CHECK (transaction_type IN ('streaming', 'download', 'sync', 'other')),
    quantity BIGINT NOT NULL CHECK (quantity >= 0),
    gross_revenue_usd DECIMAL(12,4) NOT NULL CHECK (gross_revenue_usd >= 0),
    net_revenue_usd DECIMAL(12,4) NOT NULL CHECK (net_revenue_usd >= 0),
    royalty_rate DECIMAL(5,2),
    distributor VARCHAR(20) CHECK (distributor IN ('distrokid', 'toolost')),
    extracted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(track_id),
    FOREIGN KEY (platform_id) REFERENCES platforms(platform_id),
    FOREIGN KEY (territory_id) REFERENCES territories(territory_id),
    CHECK (reporting_date <= DATE('now'))
);

-- Business Expenses: Capitol One purchases
CREATE TABLE business_expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_date DATE NOT NULL,
    posted_date DATE NOT NULL,
    description VARCHAR(500) NOT NULL,
    category VARCHAR(50) CHECK (category IN ('advertising', 'software', 'equipment', 'other')),
    amount_usd DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50),
    status VARCHAR(20) CHECK (status IN ('posted', 'pending', 'refunded')),
    expense_metadata TEXT, -- JSON as TEXT
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (posted_date >= transaction_date)
);

-- Revenue Recognition: Accounting period allocation
CREATE TABLE revenue_recognition (
    recognition_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL,
    accounting_period DATE NOT NULL,
    recognized_amount_usd DECIMAL(12,4) NOT NULL CHECK (recognized_amount_usd >= 0),
    recognition_basis VARCHAR(10) CHECK (recognition_basis IN ('accrual', 'cash')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES royalty_transactions(transaction_id)
);

-- =============================================================================
-- SOCIAL MEDIA TABLES
-- =============================================================================

-- TikTok Daily Metrics: Engagement by artist account
CREATE TABLE tiktok_daily_metrics (
    tiktok_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    metrics_date DATE NOT NULL,
    artist_id INTEGER NOT NULL,
    account_handle VARCHAR(50),
    video_views BIGINT NOT NULL CHECK (video_views >= 0),
    profile_views BIGINT NOT NULL CHECK (profile_views >= 0),
    likes_received INTEGER NOT NULL CHECK (likes_received >= 0),
    comments_received INTEGER NOT NULL CHECK (comments_received >= 0),
    shares INTEGER NOT NULL CHECK (shares >= 0),
    new_followers INTEGER, -- Can be negative
    engagement_rate DECIMAL(5,2),
    extracted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
);

-- Linktree Analytics: Click-through performance
CREATE TABLE linktree_analytics (
    linktree_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    analytics_date DATE NOT NULL,
    artist_id INTEGER NOT NULL,
    total_views INTEGER NOT NULL CHECK (total_views >= 0),
    unique_views INTEGER NOT NULL CHECK (unique_views >= 0),
    total_clicks INTEGER NOT NULL CHECK (total_clicks >= 0),
    unique_clicks INTEGER NOT NULL CHECK (unique_clicks >= 0),
    click_through_rate DECIMAL(5,2),
    top_link VARCHAR(500),
    top_link_clicks INTEGER,
    extracted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id),
    CHECK (unique_views <= total_views),
    CHECK (unique_clicks <= total_clicks),
    CHECK (top_link_clicks <= total_clicks)
);

-- Social Engagement Events: Granular interaction data
CREATE TABLE social_engagement_events (
    engagement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_timestamp TIMESTAMP NOT NULL,
    platform_id INTEGER NOT NULL,
    artist_id INTEGER NOT NULL,
    track_id INTEGER,
    engagement_type VARCHAR(20) CHECK (engagement_type IN ('like', 'comment', 'share', 'save', 'click')),
    user_id VARCHAR(100),
    event_metadata TEXT, -- JSON as TEXT
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (platform_id) REFERENCES platforms(platform_id),
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id),
    FOREIGN KEY (track_id) REFERENCES tracks(track_id)
);

-- =============================================================================
-- MARKETING & CAMPAIGN TABLES
-- =============================================================================

-- Ad Campaigns: Meta Ads campaign data
CREATE TABLE ad_campaigns (
    ad_campaign_id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL,
    external_ad_id VARCHAR(100),
    ad_name VARCHAR(200),
    objective VARCHAR(50) CHECK (objective IN ('reach', 'conversions', 'traffic', 'engagement')),
    daily_budget_usd DECIMAL(10,2) CHECK (daily_budget_usd > 0),
    targeting_criteria TEXT, -- JSON as TEXT
    status VARCHAR(20) CHECK (status IN ('active', 'paused', 'completed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
);

-- Ad Performance Daily: Daily spend/conversion metrics
CREATE TABLE ad_performance_daily (
    performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    performance_date DATE NOT NULL,
    ad_campaign_id INTEGER NOT NULL,
    impressions BIGINT NOT NULL CHECK (impressions >= 0),
    clicks INTEGER NOT NULL CHECK (clicks >= 0),
    reach INTEGER NOT NULL CHECK (reach >= 0),
    spend_usd DECIMAL(10,2) NOT NULL CHECK (spend_usd >= 0),
    cpm DECIMAL(6,2),
    cpc DECIMAL(6,2),
    ctr DECIMAL(5,2),
    conversion_events TEXT, -- JSON as TEXT
    extracted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ad_campaign_id) REFERENCES ad_campaigns(ad_campaign_id)
);

-- Campaign Creatives: Ad creative performance
CREATE TABLE campaign_creatives (
    creative_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_campaign_id INTEGER NOT NULL,
    creative_name VARCHAR(200),
    creative_type VARCHAR(20) CHECK (creative_type IN ('image', 'video', 'carousel', 'story')),
    asset_url VARCHAR(500),
    creative_specs TEXT, -- JSON as TEXT
    status VARCHAR(20) CHECK (status IN ('active', 'inactive', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ad_campaign_id) REFERENCES ad_campaigns(ad_campaign_id)
);

-- SubmitHub Submissions: Blog/playlist submissions
CREATE TABLE submithub_submissions (
    submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    submission_date DATE NOT NULL,
    blog_name VARCHAR(200),
    curator_name VARCHAR(100),
    submission_status VARCHAR(20) CHECK (submission_status IN ('pending', 'approved', 'declined')),
    feedback_text TEXT,
    shares_generated INTEGER CHECK (shares_generated >= 0),
    clicks_generated INTEGER CHECK (clicks_generated >= 0),
    cost_usd DECIMAL(6,2) CHECK (cost_usd >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(track_id)
);

-- Conversion Events: Pixel tracking data
CREATE TABLE conversion_events (
    conversion_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_timestamp TIMESTAMP NOT NULL,
    ad_campaign_id INTEGER,
    track_id INTEGER,
    conversion_type VARCHAR(20) CHECK (conversion_type IN ('stream', 'follow', 'save', 'purchase', 'click')),
    platform_event_id VARCHAR(100),
    conversion_value DECIMAL(8,2),
    event_data TEXT, -- JSON as TEXT
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ad_campaign_id) REFERENCES ad_campaigns(ad_campaign_id),
    FOREIGN KEY (track_id) REFERENCES tracks(track_id)
);

-- Campaign Attribution: Multi-touch attribution
CREATE TABLE campaign_attribution (
    attribution_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversion_id INTEGER NOT NULL,
    campaign_id INTEGER NOT NULL,
    attribution_model VARCHAR(20) CHECK (attribution_model IN ('first_touch', 'last_touch', 'linear', 'time_decay')),
    attribution_credit DECIMAL(3,2) CHECK (attribution_credit BETWEEN 0.0 AND 1.0),
    touchpoint_position INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversion_id) REFERENCES conversion_events(conversion_id),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
);

-- =============================================================================
-- JUNCTION/BRIDGE TABLES
-- =============================================================================

-- Track Artists: Many-to-many track-artist relationships
CREATE TABLE track_artists (
    track_artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    artist_id INTEGER NOT NULL,
    role_type VARCHAR(20) CHECK (role_type IN ('primary', 'featured', 'producer', 'writer')),
    royalty_percentage DECIMAL(5,2) CHECK (royalty_percentage BETWEEN 0 AND 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(track_id),
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id),
    UNIQUE(track_id, artist_id, role_type)
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =============================================================================

-- Time-series indexes for analytics workloads
CREATE INDEX idx_daily_streams_date_platform ON daily_streams(stream_date, platform_id);
CREATE INDEX idx_daily_streams_track_date ON daily_streams(track_id, stream_date);
CREATE INDEX idx_daily_streams_data_source ON daily_streams(data_source, platform_id);

-- Financial analytics indexes
CREATE INDEX idx_royalty_transactions_period ON royalty_transactions(sale_month, platform_id);
CREATE INDEX idx_royalty_transactions_track ON royalty_transactions(track_id, reporting_date);

-- Campaign performance indexes
CREATE INDEX idx_ad_performance_date_campaign ON ad_performance_daily(performance_date, ad_campaign_id);
CREATE INDEX idx_conversion_events_timestamp ON conversion_events(event_timestamp, ad_campaign_id);

-- Artist performance indexes
CREATE INDEX idx_track_artists_artist_id ON track_artists(artist_id);
CREATE INDEX idx_spotify_audience_date_artist ON spotify_audience(snapshot_date, artist_id);
CREATE INDEX idx_tiktok_metrics_date_artist ON tiktok_daily_metrics(metrics_date, artist_id);

-- Social engagement indexes
CREATE INDEX idx_social_engagement_timestamp ON social_engagement_events(event_timestamp, platform_id);
CREATE INDEX idx_linktree_analytics_date_artist ON linktree_analytics(analytics_date, artist_id);

-- Attribution and campaign indexes
CREATE INDEX idx_stream_attribution_stream_id ON stream_attribution(stream_record_id);
CREATE INDEX idx_campaign_attribution_campaign_id ON campaign_attribution(campaign_id, conversion_id);

-- =============================================================================
-- INITIAL DATA INSERTS
-- =============================================================================

-- Insert core artists
INSERT INTO artists (artist_name, spotify_id, legal_name, status) VALUES 
('PIG1987', '1Eu67EqPy2NutiM0lqCarw', 'Blake Demarest', 'active'),
('ZONE A0', '4Z7kJZ8Z3Z3Z3Z3Z3Z3Z3Z', 'Blake Demarest', 'active'),
('xXMeatWarriorXx', NULL, 'Blake Demarest', 'draft');

-- Insert core platforms
INSERT INTO platforms (platform_name, platform_type, is_active) VALUES 
('Spotify', 'streaming', TRUE),
('Apple Music', 'streaming', TRUE),
('TikTok', 'social', TRUE),
('Meta Ads', 'advertising', TRUE),
('DistroKid', 'distribution', TRUE),
('TooLost', 'distribution', TRUE),
('Linktree', 'social', TRUE),
('SubmitHub', 'advertising', TRUE);

-- Insert common territories
INSERT INTO territories (country_code, country_name, region, currency_code) VALUES 
('US', 'United States', 'North America', 'USD'),
('CA', 'Canada', 'North America', 'CAD'),
('GB', 'United Kingdom', 'Europe', 'GBP'),
('DE', 'Germany', 'Europe', 'EUR'),
('FR', 'France', 'Europe', 'EUR'),
('JP', 'Japan', 'Asia', 'JPY'),
('AU', 'Australia', 'Oceania', 'AUD'),
('CN', 'China', 'Asia', 'CNY'),
('MA', 'Morocco', 'Africa', 'MAD'),
('SA', 'Saudi Arabia', 'Middle East', 'SAR'),
('GLOBAL', 'Global/Unknown', 'Global', 'USD');

-- =============================================================================
-- VIEWS FOR BUSINESS INTELLIGENCE
-- =============================================================================

-- Monthly Artist Performance (Spotify double-counting safe)
CREATE VIEW v_monthly_artist_performance AS
SELECT 
    ta.artist_id,
    a.artist_name,
    strftime('%Y-%m', ds.stream_date) as performance_month,
    p.platform_name,
    SUM(ds.stream_count) as total_streams,
    SUM(ds.revenue_usd) as total_revenue,
    COUNT(DISTINCT ds.track_id) as active_tracks
FROM daily_streams ds
JOIN tracks t ON ds.track_id = t.track_id  
JOIN track_artists ta ON t.track_id = ta.track_id AND ta.role_type = 'primary'
JOIN artists a ON ta.artist_id = a.artist_id
JOIN platforms p ON ds.platform_id = p.platform_id
WHERE ds.data_source IN ('distrokid', 'toolost') -- Avoid Spotify double-counting
GROUP BY ta.artist_id, a.artist_name, performance_month, p.platform_name;

-- Campaign ROI Analysis
CREATE VIEW v_campaign_roi AS
SELECT 
    c.campaign_id,
    c.campaign_name,
    SUM(apd.spend_usd) as total_spend,
    COUNT(ce.conversion_id) as total_conversions,
    SUM(COALESCE(ce.conversion_value, 0)) as total_conversion_value,
    CASE 
        WHEN SUM(apd.spend_usd) > 0 
        THEN (SUM(COALESCE(ce.conversion_value, 0)) - SUM(apd.spend_usd)) / SUM(apd.spend_usd) * 100 
        ELSE 0 
    END as roi_percentage
FROM campaigns c
JOIN ad_campaigns ac ON c.campaign_id = ac.campaign_id
JOIN ad_performance_daily apd ON ac.ad_campaign_id = apd.ad_campaign_id
LEFT JOIN conversion_events ce ON ac.ad_campaign_id = ce.ad_campaign_id
GROUP BY c.campaign_id, c.campaign_name;

-- Track Performance Summary
CREATE VIEW v_track_performance_summary AS
SELECT 
    t.track_id,
    t.title,
    t.isrc,
    t.release_date,
    GROUP_CONCAT(a.artist_name) as artists,
    SUM(CASE WHEN p.platform_name = 'Spotify' AND ds.data_source != 'spotify_api' THEN ds.stream_count ELSE 0 END) as spotify_streams,
    SUM(CASE WHEN p.platform_name = 'Apple Music' THEN ds.stream_count ELSE 0 END) as apple_streams,
    SUM(ds.revenue_usd) as total_revenue,
    COUNT(DISTINCT ds.territory_id) as territories_count
FROM tracks t
JOIN track_artists ta ON t.track_id = ta.track_id
JOIN artists a ON ta.artist_id = a.artist_id
LEFT JOIN daily_streams ds ON t.track_id = ds.track_id
LEFT JOIN platforms p ON ds.platform_id = p.platform_id
GROUP BY t.track_id, t.title, t.isrc, t.release_date;

-- =============================================================================
-- TRIGGERS FOR DATA CONSISTENCY
-- =============================================================================

-- Update timestamps on record modification
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

CREATE TRIGGER update_campaigns_timestamp 
    AFTER UPDATE ON campaigns
BEGIN
    UPDATE campaigns SET updated_at = CURRENT_TIMESTAMP WHERE campaign_id = NEW.campaign_id;
END;

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

-- Table documentation (SQLite doesn't support table comments, so using -- comments)
-- artists: Multi-persona support for PIG1987, ZONE A0, xXMeatWarriorXx
-- tracks: Music catalog with ISRC/UPC codes for rights management
-- daily_streams: CRITICAL - data_source field prevents Spotify double-counting
-- spotify_audience: Separate table for Spotify API data to avoid stream duplication
-- royalty_transactions: Financial data from DistroKid/TooLost distributors
-- campaign_attribution: Multi-touch attribution for marketing ROI analysis