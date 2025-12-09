"""
Spotify Songs Landing->Raw cleaner for song metrics data.

Processes JSON files from Spotify song metrics extractor.
Validates, transforms, and converts JSON data to NDJSON format in raw zone.
Handles multiple artists and time periods.

Guided by LLM_cleaner_guidelines.md

Zones:
    landing/spotify/songs -> raw/spotify/songs
"""

# %% Imports & Constants
import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

PLATFORM = "spotify"
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])
LANDING_DIR = PROJECT_ROOT / "1_landing" / PLATFORM / "songs"
RAW_DIR = PROJECT_ROOT / "2_raw" / PLATFORM / "songs"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Artist ID mappings (same as audience cleaner)
ARTIST_MAPPINGS = {
    "62owJQCD2XzVB2o19CVsFM": "zone_a0",
    "1Eu67EqPy2NutiM0lqCarw": "pig1987",
}

# Valid time periods
VALID_PERIODS = {"1day", "7day", "28day", "1year", "all"}


# %% Helper functions

def parse_filename(filename: str) -> Dict[str, str]:
    """
    Extract metadata from filename.

    Pattern: spotify_songs_{artist_id}_{period}_{timestamp}.json
    Example: spotify_songs_62owJQCD2XzVB2o19CVsFM_1year_20251202_132232.json
    """
    result = {
        "artist_id": "unknown",
        "artist_name": "unknown",
        "time_period": "unknown",
        "extraction_date": datetime.now().strftime("%Y-%m-%d"),
    }

    # Remove extension
    base = filename.replace('.json', '')
    parts = base.split('_')

    # Expected: ['spotify', 'songs', '<artist_id>', '<period>', '<date>', '<time>']
    if len(parts) >= 5:
        artist_id = parts[2]
        time_period = parts[3]
        date_part = parts[4]

        result["artist_id"] = artist_id
        result["artist_name"] = ARTIST_MAPPINGS.get(artist_id, f"artist_{artist_id}")

        if time_period in VALID_PERIODS:
            result["time_period"] = time_period

        # Parse extraction date from timestamp (YYYYMMDD)
        if len(date_part) == 8 and date_part.isdigit():
            result["extraction_date"] = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"

    return result


def safe_int(value) -> int:
    """Safely convert string to int, handling None and empty strings."""
    if value is None or value == "":
        return 0
    try:
        return int(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0


def transform_song_record(song: Dict, metadata: Dict, source_file: str) -> Dict:
    """Transform a single song from API response to raw record."""
    return {
        "track_id": song.get("id", ""),
        "track_name": song.get("trackName", ""),
        "track_uri": song.get("trackUri", ""),
        "release_date": song.get("releaseDate", ""),
        "image_url": song.get("imageUrl", ""),
        "streams": safe_int(song.get("numStreams")),
        "listeners": safe_int(song.get("numListeners")),
        "savers": safe_int(song.get("numSavers")),
        "canvas_views": safe_int(song.get("numCanvasViews")),
        "is_disabled": song.get("isDisabled", False),
        "artist_id": metadata["artist_id"],
        "artist_name": metadata["artist_name"],
        "time_period": metadata["time_period"],
        "extraction_date": metadata["extraction_date"],
        "source_file": source_file,
        "processed_at": datetime.now().isoformat(),
    }


def process_json_file(json_path: Path) -> int:
    """Process a single JSON file from landing to raw."""
    try:
        print(f"[RAW] Processing {json_path.name}")

        # Extract metadata from filename
        metadata = parse_filename(json_path.name)

        # Read JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle wrapper structure: {data: {songs: [...]}} or just {songs: [...]}
        if "data" in data and isinstance(data["data"], dict):
            songs = data["data"].get("songs", [])
        elif "songs" in data:
            songs = data.get("songs", [])
        else:
            print(f"[ERROR] No songs array found in {json_path.name}")
            return 0

        if not songs:
            print(f"[WARN] Empty songs array in {json_path.name}")
            return 0

        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"spotify_songs_{metadata['artist_name']}_{metadata['time_period']}_{timestamp}.ndjson"
        output_path = RAW_DIR / output_name

        # Transform and write records
        record_count = 0
        with open(output_path, 'w', encoding='utf-8') as f:
            for song in songs:
                # Skip songs without ID
                if not song.get("id"):
                    continue

                record = transform_song_record(song, metadata, json_path.name)
                f.write(json.dumps(record) + '\n')
                record_count += 1

        print(f"[RAW] {json_path.name} -> {output_name} ({record_count} tracks)")
        return record_count

    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in {json_path.name}: {e}")
        return 0
    except Exception as e:
        print(f"[ERROR] Failed to process {json_path.name}: {e}")
        return 0


# %% Core processing

def run(file_path: Optional[Path] = None, pattern: str = "*.json") -> int:
    """Main processing function."""
    print("[INFO] Starting Spotify songs landing -> raw processing...")
    print(f"[INFO] Landing dir: {LANDING_DIR}")
    print(f"[INFO] Raw dir: {RAW_DIR}")

    if file_path:
        json_files = [file_path] if file_path.exists() else []
    else:
        json_files = list(LANDING_DIR.glob(pattern))

    if not json_files:
        print("[WARN] No JSON files found to process.")
        return 0

    print(f"[INFO] Found {len(json_files)} files to process")

    total_records = 0
    processed_files = 0

    for json_file in sorted(json_files):
        records = process_json_file(json_file)
        if records > 0:
            total_records += records
            processed_files += 1

    if total_records == 0:
        print("[WARN] No records were processed successfully")
        return 0

    print(f"[RAW] Processed {processed_files} files with {total_records} total track records")
    return total_records


# %% CLI

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Spotify songs landing -> raw cleaner")
    parser.add_argument("--file", type=str, help="Specific JSON file to process")
    parser.add_argument("--pattern", type=str, default="*.json", help="Glob pattern for files")
    args = parser.parse_args()

    file_path = Path(args.file) if args.file else None

    try:
        run(file_path, args.pattern)
    except Exception as e:
        print(f"[ERROR] {e}")
        exit(1)


if __name__ == "__main__":
    main()
