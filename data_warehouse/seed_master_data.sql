-- BEDROT Data Warehouse Master Data Seeding
-- Created: 2025-08-28
-- Must be run AFTER create_schema.sql

-- ======================
-- SEED ARTISTS (ALL CAPS)
-- ======================
INSERT INTO artists (artist_name, status) VALUES
('PIG1987', 'active'),
('ZONE A0', 'active'),
('XXMEATWARRIOR69XX', 'active'),
('IWARY', 'active'),
('ZONE A0 X SXNCTUARY', 'active');

-- ======================
-- SEED PLATFORMS
-- ======================
INSERT INTO platforms (platform_name, platform_type, is_active) VALUES
-- Streaming platforms
('Spotify', 'streaming', TRUE),
('Apple Music', 'streaming', TRUE),
('YouTube Music', 'streaming', TRUE),
('SoundCloud', 'streaming', TRUE),
('Bandcamp', 'streaming', TRUE),

-- Social platforms  
('TikTok', 'social', TRUE),
('Instagram', 'social', TRUE),
('YouTube', 'social', TRUE),
('Linktree', 'social', TRUE),

-- Advertising platforms
('Meta Ads', 'advertising', TRUE),
('Google Ads', 'advertising', TRUE),
('TikTok Ads', 'advertising', TRUE),

-- Distribution platforms
('DistroKid', 'distribution', TRUE),
('TooLost', 'distribution', TRUE);

-- ======================
-- SEED TERRITORIES
-- ======================
-- Default territory for current data (no geographic scraping yet)
INSERT INTO territories (country_code, country_name, region, currency_code) VALUES
('GLOBAL', 'Global/Unknown', 'Global', 'USD');

-- Future territories (ready for when geographic scraping is implemented)
INSERT INTO territories (country_code, country_name, region, currency_code) VALUES
('US', 'United States', 'North America', 'USD'),
('CA', 'Canada', 'North America', 'CAD'),
('GB', 'United Kingdom', 'Europe', 'GBP'),
('DE', 'Germany', 'Europe', 'EUR'),
('FR', 'France', 'Europe', 'EUR'),
('AU', 'Australia', 'Oceania', 'AUD'),
('JP', 'Japan', 'Asia', 'JPY'),
('BR', 'Brazil', 'South America', 'BRL'),
('MX', 'Mexico', 'North America', 'MXN');

-- ======================
-- SEED KNOWN TRACKS
-- ======================
-- Based on campaign analysis from Meta Ads data
INSERT INTO tracks (title, release_type) VALUES
('THE STATE OF THE WORLD', 'single'),
('THE SOURCE', 'single'),
('RENEGADE PIPELINE', 'single'),
('THE SCALE', 'single'),
('IWARY', 'single'),
('TRANSFORMER ARCHITECTURE', 'single');

-- ======================
-- SEED TRACK-ARTIST RELATIONSHIPS
-- ======================
-- Get artist and track IDs for relationships
INSERT INTO track_artists (track_id, artist_id, role_type, royalty_percentage)
SELECT 
    t.track_id,
    a.artist_id,
    'primary',
    100.0
FROM tracks t, artists a
WHERE 
    (t.title = 'THE STATE OF THE WORLD' AND a.artist_name = 'PIG1987') OR
    (t.title = 'THE SOURCE' AND a.artist_name = 'ZONE A0') OR
    (t.title = 'RENEGADE PIPELINE' AND a.artist_name = 'PIG1987') OR
    (t.title = 'THE SCALE' AND a.artist_name = 'ZONE A0') OR
    (t.title = 'IWARY' AND a.artist_name = 'PIG1987') OR
    (t.title = 'TRANSFORMER ARCHITECTURE' AND a.artist_name = 'PIG1987');

-- ======================
-- VERIFICATION QUERIES
-- ======================
-- Uncomment to verify data was inserted correctly

-- SELECT 'Artists:' as table_name;
-- SELECT artist_id, artist_name, status FROM artists ORDER BY artist_name;

-- SELECT 'Platforms:' as table_name;  
-- SELECT platform_id, platform_name, platform_type FROM platforms ORDER BY platform_type, platform_name;

-- SELECT 'Territories:' as table_name;
-- SELECT territory_id, country_code, country_name FROM territories ORDER BY territory_id;

-- SELECT 'Tracks with Artists:' as table_name;
-- SELECT t.title, a.artist_name, ta.role_type, ta.royalty_percentage
-- FROM tracks t
-- JOIN track_artists ta ON t.track_id = ta.track_id  
-- JOIN artists a ON ta.artist_id = a.artist_id
-- ORDER BY t.title;