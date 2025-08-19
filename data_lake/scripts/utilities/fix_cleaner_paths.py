#!/usr/bin/env python
"""Fix directory paths in all cleaner scripts to use numbered directories."""

import os
import re
from pathlib import Path

def fix_cleaner_paths(file_path):
    """Update directory references in a cleaner script."""
    
    replacements = [
        # Directory mappings
        (r'/ "landing" /', '/ "1_landing" /'),
        (r'/ "raw" /', '/ "2_raw" /'),
        (r'/ "staging" /', '/ "3_staging" /'),
        (r'/ "curated" /', '/ "4_curated" /'),
        (r'/ "archive" /', '/ "5_archive" /'),
        (r'"landing"', '"1_landing"'),
        (r'"raw"', '"2_raw"'),
        (r'"staging"', '"3_staging"'),
        (r'"curated"', '"4_curated"'),
        (r'"archive"', '"5_archive"'),
    ]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    for old, new in replacements:
        content = re.sub(old, new, content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix paths in all cleaner scripts."""
    src_path = Path('src')
    
    if not src_path.exists():
        print("[ERROR] src directory not found. Run from data_lake root.")
        return
    
    fixed_count = 0
    total_count = 0
    
    # Find all cleaner scripts
    for service_dir in src_path.iterdir():
        if not service_dir.is_dir() or service_dir.name == 'common':
            continue
        
        cleaners_dir = service_dir / 'cleaners'
        if not cleaners_dir.exists():
            continue
        
        for cleaner_file in cleaners_dir.glob('*.py'):
            total_count += 1
            print(f"Checking {cleaner_file.relative_to(src_path)}...", end=' ')
            
            if fix_cleaner_paths(cleaner_file):
                print("[FIXED]")
                fixed_count += 1
            else:
                print("[OK]")
    
    print(f"\nSummary: Fixed {fixed_count} of {total_count} cleaner scripts")

if __name__ == '__main__':
    main()