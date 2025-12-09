"""
Spotify Songs Staging->Curated cleaner for song metrics data.

Creates two business-ready outputs:
1. Fact Table: Song metrics per track/period/extraction_date (for trend analysis)
2. Dimension Table: Static track metadata (deduplicated by track_id)

Implements star schema design to avoid double-counting overlapping time windows.

Guided by LLM_cleaner_guidelines.md

Zones:
    staging/spotify/songs -> curated/
"""

# %% Imports & Constants
import argparse
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Tuple

import pandas as pd

PLATFORM = "spotify"
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])
STAGING_DIR = PROJECT_ROOT / "3_staging" / PLATFORM / "songs"
CURATED_DIR = PROJECT_ROOT / "4_curated"
ARCHIVE_DIR = PROJECT_ROOT / "5_archive" / PLATFORM / "songs"

# Ensure directories exist
CURATED_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# Tracked artists - filter to only these
TRACKED_ARTISTS = {"zone_a0", "pig1987"}

# Fact table columns (metrics)
FACT_COLUMNS = [
    "track_id",
    "artist_id",
    "artist_name",
    "time_period",
    "extraction_date",
    "streams",
    "listeners",
    "savers",
    "canvas_views",
    "curated_at",
]

# Dimension table columns (track metadata)
DIMENSION_COLUMNS = [
    "track_id",
    "track_name",
    "track_uri",
    "release_date",
    "image_url",
    "artist_id",
    "artist_name",
    "first_seen",
    "last_updated",
]


# %% Helper functions

def load_existing_curated() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load existing curated fact and dimension tables if they exist."""
    fact_files = list(CURATED_DIR.glob("spotify_song_metrics_curated_*.csv"))
    dim_files = list(CURATED_DIR.glob("spotify_tracks_dimension_*.csv"))

    fact_df = pd.DataFrame()
    dim_df = pd.DataFrame()

    if fact_files:
        # Load most recent fact table
        latest_fact = max(fact_files, key=lambda p: p.stat().st_mtime)
        fact_df = pd.read_csv(latest_fact)
        print(f"[CURATED] Loaded {len(fact_df)} historical records from {latest_fact.name}")

    if dim_files:
        # Load most recent dimension table
        latest_dim = max(dim_files, key=lambda p: p.stat().st_mtime)
        dim_df = pd.read_csv(latest_dim)
        print(f"[CURATED] Loaded {len(dim_df)} historical tracks from {latest_dim.name}")

    return fact_df, dim_df


def archive_existing_files(pattern: str, archive_dir: Path) -> int:
    """Archive existing curated files before overwriting."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archived_count = 0

    existing_files = list(CURATED_DIR.glob(pattern))
    for file_path in existing_files:
        archive_name = f"{file_path.stem}_archived_{timestamp}{file_path.suffix}"
        archive_path = archive_dir / archive_name
        shutil.move(str(file_path), str(archive_path))
        print(f"[ARCHIVE] {file_path.name} -> {archive_name}")
        archived_count += 1

    return archived_count


def create_fact_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create the fact table with deduplicated metrics.

    Primary Key: (track_id, artist_id, time_period, extraction_date)
    Deduplication: Keep last (most recent processing) for each key combination.
    """
    # Sort by staged_at to ensure we keep the latest processing
    df = df.sort_values("staged_at")

    # Deduplicate on composite key, keeping last
    dedup_cols = ["track_id", "artist_id", "time_period", "extraction_date"]
    before_count = len(df)
    df = df.drop_duplicates(subset=dedup_cols, keep="last")
    after_count = len(df)

    if before_count != after_count:
        print(f"[CURATED] Deduplicated: {before_count} -> {after_count} records")

    # Add curated timestamp
    df["curated_at"] = datetime.now().isoformat()

    # Select fact columns
    fact_df = df[FACT_COLUMNS].copy()

    # Sort by artist, extraction_date, track for clean output
    fact_df = fact_df.sort_values(
        ["artist_name", "extraction_date", "time_period", "streams"],
        ascending=[True, True, True, False]
    )

    return fact_df


def create_dimension_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create the dimension table with track metadata.

    Primary Key: track_id
    Keeps latest track_name, release_date, image_url, track_uri per track.
    Tracks first_seen and last_updated timestamps.
    """
    # Sort by staged_at to get chronological order
    df = df.sort_values("staged_at")

    # Group by track_id to get first_seen (earliest extraction_date)
    first_seen = df.groupby("track_id")["extraction_date"].min().reset_index()
    first_seen.columns = ["track_id", "first_seen"]

    # Get latest record per track for other metadata
    latest = df.drop_duplicates(subset=["track_id"], keep="last").copy()

    # Merge first_seen
    latest = latest.merge(first_seen, on="track_id", how="left")

    # Add last_updated timestamp
    latest["last_updated"] = datetime.now().isoformat()

    # Select dimension columns
    dimension_df = latest[DIMENSION_COLUMNS].copy()

    # Sort by artist, track_name
    dimension_df = dimension_df.sort_values(["artist_name", "track_name"])

    return dimension_df


def generate_summary_stats(fact_df: pd.DataFrame, dimension_df: pd.DataFrame) -> None:
    """Print summary statistics for curated data."""
    print("\n" + "=" * 60)
    print("CURATED DATA SUMMARY")
    print("=" * 60)

    # Fact table stats
    print("\n[FACT TABLE]")
    print(f"  Total records: {len(fact_df)}")
    print(f"  Unique tracks: {fact_df['track_id'].nunique()}")
    print(f"  Artists: {fact_df['artist_name'].nunique()}")
    print(f"  Time periods: {sorted(fact_df['time_period'].unique())}")
    print(f"  Extraction dates: {fact_df['extraction_date'].nunique()}")

    # Per-artist breakdown
    print("\n  Per-Artist Breakdown:")
    for artist in sorted(fact_df['artist_name'].unique()):
        artist_data = fact_df[fact_df['artist_name'] == artist]
        tracks = artist_data['track_id'].nunique()
        total_streams = artist_data[artist_data['time_period'] == 'all']['streams'].sum()
        print(f"    {artist}: {tracks} tracks, {total_streams:,} all-time streams")

    # Dimension table stats
    print("\n[DIMENSION TABLE]")
    print(f"  Total tracks: {len(dimension_df)}")
    print(f"  Release date range: {dimension_df['release_date'].min()} to {dimension_df['release_date'].max()}")

    # Top tracks by streams (from fact table, using 'all' period)
    print("\n  Top 5 Tracks (All-Time Streams):")
    top_tracks = fact_df[fact_df['time_period'] == 'all'].nlargest(5, 'streams')
    for _, row in top_tracks.iterrows():
        track_info = dimension_df[dimension_df['track_id'] == row['track_id']]
        if not track_info.empty:
            track_name = track_info.iloc[0]['track_name']
            print(f"    - {track_name} ({row['artist_name']}): {row['streams']:,} streams")

    print("=" * 60 + "\n")


# %% Core processing

def run(pattern: str = "*.csv") -> Tuple[int, int]:
    """Main processing function."""
    print("[INFO] Starting Spotify songs staging -> curated processing...")
    print(f"[INFO] Staging dir: {STAGING_DIR}")
    print(f"[INFO] Curated dir: {CURATED_DIR}")

    # Find staging files
    staging_files = list(STAGING_DIR.glob(pattern))

    if not staging_files:
        print("[WARN] No staging CSV files found to process.")
        return 0, 0

    print(f"[INFO] Found {len(staging_files)} staging files to process")

    # Load and combine all staging files
    dfs = []
    for staging_file in sorted(staging_files):
        try:
            df = pd.read_csv(staging_file)
            print(f"[CURATED] Loaded {len(df)} records from {staging_file.name}")
            dfs.append(df)
        except Exception as e:
            print(f"[ERROR] Failed to read {staging_file.name}: {e}")

    if not dfs:
        print("[WARN] No data loaded from staging files")
        return 0, 0

    # Combine all dataframes
    combined_df = pd.concat(dfs, ignore_index=True)
    print(f"[INFO] Combined {len(combined_df)} total records")

    # Filter to tracked artists only
    before_filter = len(combined_df)
    combined_df = combined_df[combined_df["artist_name"].isin(TRACKED_ARTISTS)]
    after_filter = len(combined_df)

    if before_filter != after_filter:
        print(f"[CURATED] Filtered to tracked artists: {before_filter} -> {after_filter} records")

    if combined_df.empty:
        print("[WARN] No records for tracked artists")
        return 0, 0

    # Load existing curated data BEFORE archiving
    historical_fact_df, historical_dim_df = load_existing_curated()

    # Archive existing curated files
    archive_existing_files("spotify_song_metrics_curated_*.csv", ARCHIVE_DIR)
    archive_existing_files("spotify_tracks_dimension_*.csv", ARCHIVE_DIR)

    # Keep original staging data (with full track metadata) for dimension table
    staging_df_for_dimension = combined_df.copy()

    # Merge historical fact data with new staging data FOR FACT TABLE ONLY
    if not historical_fact_df.empty:
        # Need to add staged_at column to historical data for deduplication
        if "staged_at" not in historical_fact_df.columns:
            # Use a timestamp BEFORE the new data so new data takes precedence
            historical_fact_df["staged_at"] = "2000-01-01T00:00:00"

        # Add required columns to historical data if missing (just for concat compatibility)
        staging_cols_needed = ["track_name", "track_uri", "release_date", "image_url", "is_disabled", "source_file"]
        for col in staging_cols_needed:
            if col not in historical_fact_df.columns:
                historical_fact_df[col] = ""

        print(f"[CURATED] Merging {len(historical_fact_df)} historical + {len(combined_df)} new records")
        combined_df = pd.concat([historical_fact_df, combined_df], ignore_index=True)
        print(f"[CURATED] Total after merge: {len(combined_df)} records")

    # Merge historical dimension data to preserve first_seen dates
    first_seen_map = {}
    if not historical_dim_df.empty:
        # Create mapping of track_id -> first_seen from historical data
        first_seen_map = dict(zip(historical_dim_df["track_id"], historical_dim_df["first_seen"]))
        print(f"[CURATED] Preserving first_seen dates for {len(first_seen_map)} historical tracks")

    # Create fact table from merged data (historical + new)
    fact_df = create_fact_table(combined_df)

    # Create dimension table from STAGING DATA ONLY (has full track metadata)
    dimension_df = create_dimension_table(staging_df_for_dimension)

    # Restore historical first_seen dates for existing tracks
    if first_seen_map:
        def restore_first_seen(row):
            if row["track_id"] in first_seen_map:
                return first_seen_map[row["track_id"]]
            return row["first_seen"]
        dimension_df["first_seen"] = dimension_df.apply(restore_first_seen, axis=1)

    # Generate output filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fact_filename = f"spotify_song_metrics_curated_{timestamp}.csv"
    dimension_filename = f"spotify_tracks_dimension_{timestamp}.csv"

    # Write fact table
    fact_path = CURATED_DIR / fact_filename
    fact_df.to_csv(fact_path, index=False, encoding='utf-8')
    print(f"[CURATED] Created fact table: {fact_filename} ({len(fact_df)} records)")

    # Write dimension table
    dimension_path = CURATED_DIR / dimension_filename
    dimension_df.to_csv(dimension_path, index=False, encoding='utf-8')
    print(f"[CURATED] Created dimension table: {dimension_filename} ({len(dimension_df)} tracks)")

    # Generate summary
    generate_summary_stats(fact_df, dimension_df)

    return len(fact_df), len(dimension_df)


# %% CLI

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Spotify songs staging -> curated cleaner")
    parser.add_argument("--pattern", type=str, default="*.csv", help="Glob pattern for staging files")
    args = parser.parse_args()

    try:
        fact_count, dim_count = run(args.pattern)
        if fact_count == 0:
            print("[WARN] No curated data generated")
            exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        exit(1)


if __name__ == "__main__":
    main()
