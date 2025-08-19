# %%
# ─── Cell 1: Imports & Environment Setup ────────────────────────────────────────
# Process Meta Ads CSV files from landing zone and convert to NDJSON in raw zone
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT"))
LANDING = PROJECT_ROOT / os.getenv("LANDING_ZONE", "1_landing")
RAW = PROJECT_ROOT / os.getenv("RAW_ZONE", "2_raw")

# %%
# ─── Cell 2: Process Meta Ads CSV Files ─────────────────────────────────────────
meta_landing = LANDING / "metaads"
raw_meta = RAW / "metaads"
raw_meta.mkdir(parents=True, exist_ok=True)

# Track processed files
hash_file = raw_meta / "_processed_hashes.json"
processed_hashes = {}
if hash_file.exists():
    with open(hash_file, 'r') as f:
        processed_hashes = json.load(f)

def file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of a file"""
    h = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def is_duplicate(file_path: Path, file_hash_val: str) -> bool:
    """Check if file has already been processed"""
    file_name = file_path.name
    return processed_hashes.get(file_name) == file_hash_val

# %%
# ─── Cell 3: Convert CSV to NDJSON and Promote ──────────────────────────────────
promoted = []
errors = []

# Process all CSV files in landing/metaads
csv_files = list(meta_landing.glob("*.csv"))

if not csv_files:
    print(f"[INFO] No CSV files found in {meta_landing}")
else:
    print(f"[INFO] Found {len(csv_files)} CSV files to process")
    
    for csv_file in sorted(csv_files):
        try:
            # Calculate file hash
            hash_val = file_hash(csv_file)
            
            # Skip if already processed
            if is_duplicate(csv_file, hash_val):
                print(f"[SKIP] {csv_file.name} already processed")
                continue
            
            # Read CSV file
            df = pd.read_csv(csv_file, encoding='utf-8')
            print(f"[PROCESSING] {csv_file.name} - {len(df)} rows")
            
            # Add metadata
            df['_source_file'] = csv_file.name
            df['_processed_at'] = datetime.utcnow().isoformat()
            
            # Handle different file types
            if 'campaign_daily' in csv_file.name:
                # Daily campaign data
                output_name = f"campaign_daily_{datetime.utcnow():%Y%m%d_%H%M%S}.ndjson"
            elif 'campaign' in csv_file.name:
                # Campaign metadata
                output_name = f"campaigns_{datetime.utcnow():%Y%m%d_%H%M%S}.ndjson"
            elif 'BEDROT-ADS' in csv_file.name:
                # Manual export from Ads Manager
                output_name = f"manual_export_{datetime.utcnow():%Y%m%d_%H%M%S}.ndjson"
            else:
                # Generic Meta ads data
                output_name = f"metaads_{datetime.utcnow():%Y%m%d_%H%M%S}.ndjson"
            
            # Convert to NDJSON (one JSON object per line)
            output_path = raw_meta / output_name
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for _, row in df.iterrows():
                    # Convert row to dict and handle NaN values
                    row_dict = row.to_dict()
                    # Replace NaN with None for proper JSON serialization
                    row_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
                    f.write(json.dumps(row_dict, ensure_ascii=False) + '\n')
            
            # Update processed hashes
            processed_hashes[csv_file.name] = hash_val
            promoted.append(output_name)
            
            print(f"[SUCCESS] Promoted to {output_name}")
            
            # Archive the original file (optional - comment out if you want to keep originals)
            # archive_dir = meta_landing / "archived"
            # archive_dir.mkdir(exist_ok=True)
            # csv_file.rename(archive_dir / csv_file.name)
            
        except Exception as e:
            print(f"[ERROR] Failed to process {csv_file.name}: {e}")
            errors.append((csv_file.name, str(e)))
            continue

# %%
# ─── Cell 4: Save Processing Metadata ────────────────────────────────────────────
# Save updated hash file
with open(hash_file, 'w') as f:
    json.dump(processed_hashes, f, indent=2)

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Files processed: {len(promoted)}")
print(f"Files skipped (duplicates): {len(csv_files) - len(promoted) - len(errors)}")
print(f"Errors: {len(errors)}")

if promoted:
    print("\nPromoted files:")
    for file in promoted[:5]:  # Show first 5
        print(f"  - {file}")
    if len(promoted) > 5:
        print(f"  ... and {len(promoted) - 5} more")

if errors:
    print("\nErrors encountered:")
    for file, error in errors:
        print(f"  - {file}: {error}")

print(f"\nRaw zone location: {raw_meta}")