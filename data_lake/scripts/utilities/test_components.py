#!/usr/bin/env python
"""Test individual pipeline components to identify failures."""

import os
import sys
import subprocess
from pathlib import Path

# Set up environment
PROJECT_ROOT = Path(__file__).parent.absolute()
os.environ['PROJECT_ROOT'] = str(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

def test_import(module_name):
    """Test if a module can be imported."""
    try:
        __import__(module_name)
        print(f"[OK] {module_name} imported successfully")
        return True
    except ImportError as e:
        print(f"[FAIL] {module_name} import failed: {e}")
        return False

def test_script(script_path, description):
    """Test if a script runs without errors."""
    print(f"\nTesting: {description}")
    script_path = PROJECT_ROOT / script_path
    
    if not script_path.exists():
        print(f"[FAIL] Script not found: {script_path}")
        return False
    
    try:
        # Run script with --help or --test flag if available
        result = subprocess.run(
            [sys.executable, str(script_path), '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 or 'usage:' in result.stdout.lower():
            print(f"[OK] {script_path.name} can be executed")
            return True
        else:
            print(f"[FAIL] {script_path.name} failed with code {result.returncode}")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"[FAIL] {script_path.name} timed out")
        return False
    except Exception as e:
        print(f"[FAIL] {script_path.name} error: {e}")
        return False

def main():
    """Run component tests."""
    print("=" * 60)
    print("BEDROT DATA LAKE COMPONENT TEST")
    print("=" * 60)
    
    # Test core imports
    print("\n1. Testing Core Imports:")
    print("-" * 30)
    
    core_modules = [
        'pandas',
        'numpy',
        'requests',
        'playwright',
        'beautifulsoup4',
        'dotenv',
        'loguru',
        'tqdm'
    ]
    
    import_results = {}
    for module in core_modules:
        import_results[module] = test_import(module)
    
    # Test common utilities
    print("\n2. Testing Common Utilities:")
    print("-" * 30)
    
    common_modules = [
        'common.cookies',
        'common.utils.hash_helpers',
    ]
    
    for module in common_modules:
        test_import(module)
    
    # Test key scripts
    print("\n3. Testing Key Scripts:")
    print("-" * 30)
    
    scripts = [
        ('src/common/pipeline_health_monitor.py', 'Pipeline Health Monitor'),
        ('src/spotify/extractors/spotify_audience_extractor.py', 'Spotify Extractor'),
        ('src/spotify/cleaners/spotify_landing2raw.py', 'Spotify Landing2Raw'),
        ('src/linktree/extractors/linktree_analytics_extractor.py', 'Linktree Extractor'),
        ('src/distrokid/extractors/dk_auth.py', 'DistroKid Extractor'),
    ]
    
    script_results = {}
    for script_path, desc in scripts:
        script_results[script_path] = test_script(script_path, desc)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    failed_imports = [m for m, r in import_results.items() if not r]
    failed_scripts = [s for s, r in script_results.items() if not r]
    
    if failed_imports:
        print(f"\nFailed imports ({len(failed_imports)}):")
        for module in failed_imports:
            print(f"  - {module}")
    
    if failed_scripts:
        print(f"\nFailed scripts ({len(failed_scripts)}):")
        for script in failed_scripts:
            print(f"  - {script}")
    
    if not failed_imports and not failed_scripts:
        print("\n[SUCCESS] All components passed!")
    else:
        print(f"\n[FAILED] {len(failed_imports)} imports and {len(failed_scripts)} scripts failed")
        print("\nNext steps:")
        print("1. Install missing packages: pip install -r requirements-minimal.txt")
        print("2. Check PROJECT_ROOT environment variable")
        print("3. Verify file paths and permissions")

if __name__ == '__main__':
    main()