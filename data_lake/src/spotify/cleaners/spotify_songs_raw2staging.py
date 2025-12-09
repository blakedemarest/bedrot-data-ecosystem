"""
Spotify Songs Raw->Staging cleaner for song metrics data.

Merges NDJSON files from raw zone into consolidated CSV in staging zone.
Validates data types, standardizes formats, and prepares for curated processing.

Guided by LLM_cleaner_guidelines.md

Zones:
    raw/spotify/songs -> staging/spotify/songs
"""

# %% Imports & Constants
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

PLATFORM = "spotify"
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])
RAW_DIR = PROJECT_ROOT / "2_raw" / PLATFORM / "songs"
STAGING_DIR = PROJECT_ROOT / "3_staging" / PLATFORM / "songs"

# Ensure directories exist
STAGING_DIR.mkdir(parents=True, exist_ok=True)

# Expected columns in raw NDJSON
EXPECTED_COLUMNS = [
    "track_id",
    "track_name",
    "track_uri",
    "release_date",
    "image_url",
    "streams",
    "listeners",
    "savers",
    "canvas_views",
    "is_disabled",
    "artist_id",
    "artist_name",
    "time_period",
    "extraction_date",
    "source_file",
    "processed_at",
]

# Numeric columns to validate
NUMERIC_COLUMNS = ["streams", "listeners", "savers", "canvas_views"]


# %% Helper functions

def load_ndjson_file(file_path: Path) -> List[dict]:
    """Load records from an NDJSON file."""
    records = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError as e:
                    print(f"[WARN] Invalid JSON at line {line_num} in {file_path.name}: {e}")
        return records
    except Exception as e:
        print(f"[ERROR] Failed to read {file_path.name}: {e}")
        return []


def validate_and_clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validate data types and clean the DataFrame."""
    # Ensure all expected columns exist
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            print(f"[WARN] Missing column '{col}', adding with default value")
            if col in NUMERIC_COLUMNS:
                df[col] = 0
            else:
                df[col] = ""

    # Coerce numeric columns
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Validate extraction_date
    df["extraction_date"] = pd.to_datetime(df["extraction_date"], errors="coerce")
    invalid_dates = df["extraction_date"].isna().sum()
    if invalid_dates > 0:
        print(f"[WARN] {invalid_dates} records with invalid extraction_date, using today")
        df["extraction_date"] = df["extraction_date"].fillna(pd.Timestamp.now().normalize())
    df["extraction_date"] = df["extraction_date"].dt.strftime("%Y-%m-%d")

    # Validate release_date (can be empty for some tracks)
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df["release_date"] = df["release_date"].dt.strftime("%Y-%m-%d").fillna("")

    # Ensure boolean for is_disabled
    df["is_disabled"] = df["is_disabled"].fillna(False).astype(bool)

    # Strip whitespace from string columns
    string_cols = ["track_id", "track_name", "track_uri", "image_url", "artist_id", "artist_name", "time_period"]
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df


# %% Core processing

def run(pattern: str = "*.ndjson") -> int:
    """Main processing function."""
    print("[INFO] Starting Spotify songs raw -> staging processing...")
    print(f"[INFO] Raw dir: {RAW_DIR}")
    print(f"[INFO] Staging dir: {STAGING_DIR}")

    # Find all NDJSON files
    ndjson_files = list(RAW_DIR.glob(pattern))

    if not ndjson_files:
        print("[WARN] No NDJSON files found to process.")
        return 0

    print(f"[INFO] Found {len(ndjson_files)} NDJSON files to process")

    # Load all records
    all_records = []
    for ndjson_file in sorted(ndjson_files):
        records = load_ndjson_file(ndjson_file)
        if records:
            print(f"[STAGING] Loaded {len(records)} records from {ndjson_file.name}")
            all_records.extend(records)

    if not all_records:
        print("[WARN] No records loaded from NDJSON files")
        return 0

    print(f"[INFO] Total records loaded: {len(all_records)}")

    # Convert to DataFrame
    df = pd.DataFrame(all_records)

    # Validate and clean
    df = validate_and_clean_dataframe(df)

    # Add staging timestamp
    df["staged_at"] = datetime.now().isoformat()

    # Sort by artist, track, period, extraction_date
    df = df.sort_values(
        ["artist_name", "track_name", "time_period", "extraction_date"],
        ascending=[True, True, True, True]
    )

    # Create output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = f"spotify_songs_staging_{timestamp}.csv"
    output_path = STAGING_DIR / output_name

    # Select columns in order
    output_columns = EXPECTED_COLUMNS + ["staged_at"]
    df = df[output_columns]

    # Write to CSV
    df.to_csv(output_path, index=False, encoding='utf-8')

    record_count = len(df)
    unique_tracks = df["track_id"].nunique()
    unique_periods = df["time_period"].nunique()
    unique_artists = df["artist_name"].nunique()

    print(f"[STAGING] Created {output_name}")
    print(f"[STAGING] Summary:")
    print(f"  - Total records: {record_count}")
    print(f"  - Unique tracks: {unique_tracks}")
    print(f"  - Time periods: {unique_periods}")
    print(f"  - Artists: {unique_artists}")

    return record_count


# %% CLI

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Spotify songs raw -> staging cleaner")
    parser.add_argument("--pattern", type=str, default="*.ndjson", help="Glob pattern for files")
    args = parser.parse_args()

    try:
        run(args.pattern)
    except Exception as e:
        print(f"[ERROR] {e}")
        exit(1)


if __name__ == "__main__":
    main()
