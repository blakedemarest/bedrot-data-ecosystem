#!/usr/bin/env python3
"""
Test script to validate the complete data pipeline integrity.
Performs dry-run tests and validates configuration without modifying data.
"""

import os
import sys
from pathlib import Path
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple

# Try to import pandas, but don't fail if not available
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "data_lake" / "src"))

def check_environment_setup() -> Dict[str, bool]:
    """Check if environment variables and paths are correctly configured."""
    print("\n🔍 Checking Environment Setup...")
    results = {}
    
    # Check for harmonized .env files
    env_files = [
        Path(__file__).parent.parent / ".env",
        Path(__file__).parent.parent / "data_lake" / ".env",
        Path(__file__).parent.parent / "data-warehouse" / ".env",
        Path(__file__).parent.parent / "data_dashboard" / ".env",
    ]
    
    for env_file in env_files:
        exists = env_file.exists()
        results[f"{env_file.name} exists"] = exists
        if exists:
            # Check for PROJECT_ROOT consistency
            with open(env_file, 'r') as f:
                content = f.read()
                has_project_root = 'PROJECT_ROOT=' in content
                results[f"{env_file.parent.name}/PROJECT_ROOT defined"] = has_project_root
    
    # Check for security warnings
    data_lake_env = Path(__file__).parent.parent / "data_lake" / ".env"
    if data_lake_env.exists():
        with open(data_lake_env, 'r') as f:
            content = f.read()
            has_warning = "SECURITY WARNING" in content
            results["Security warning added"] = has_warning
    
    return results

def check_data_integrity_framework() -> Dict[str, bool]:
    """Check if data integrity framework is properly installed."""
    print("\n🔍 Checking Data Integrity Framework...")
    results = {}
    
    # Check if integrity checks module exists
    integrity_module = Path(__file__).parent.parent / "data_lake" / "src" / "common" / "integrity_checks.py"
    results["integrity_checks.py exists"] = integrity_module.exists()
    
    if integrity_module.exists():
        # Try to import it
        try:
            from common.integrity_checks import DataIntegrityChecker, DATASET_SCHEMAS
            results["Module imports successfully"] = True
            results["DataIntegrityChecker available"] = True
            results["Dataset schemas defined"] = len(DATASET_SCHEMAS) > 0
        except Exception as e:
            results["Module imports successfully"] = False
            results["Import error"] = str(e)
    
    # Check validation reports directory
    validation_dir = Path(__file__).parent.parent / "data_lake" / "validation_reports"
    results["Validation reports directory exists"] = validation_dir.exists()
    
    return results

def check_curated_documentation() -> Dict[str, bool]:
    """Check if curated zone documentation is properly configured."""
    print("\n🔍 Checking Curated Zone Documentation...")
    results = {}
    
    # Check DATASET_CONTEXT.md
    context_file = Path(__file__).parent.parent / "data_lake" / "curated" / "DATASET_CONTEXT.md"
    results["DATASET_CONTEXT.md exists"] = context_file.exists()
    
    if context_file.exists():
        with open(context_file, 'r') as f:
            content = f.read()
            # Check for key sections
            results["Financial data documented"] = "dk_bank_details.csv" in content
            results["Streaming data documented"] = "tidy_daily_streams.csv" in content
            results["Social media data documented"] = "tiktok_analytics_curated" in content
            results["Quality checks documented"] = "Quality Checks:" in content
    
    # Check if it's properly gitignored
    gitignore_path = Path(__file__).parent.parent / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            gitignore = f.read()
            results["DATASET_CONTEXT.md gitignored"] = "data_lake/curated/DATASET_CONTEXT.md" in gitignore
    
    return results

def check_cron_job_integration() -> Dict[str, bool]:
    """Check if cron job properly includes warehouse ETL."""
    print("\n🔍 Checking Cron Job Integration...")
    results = {}
    
    # Check main cron job
    cron_file = Path(__file__).parent.parent / "data_lake" / "cronjob" / "run_datalake_cron.bat"
    results["Cron job exists"] = cron_file.exists()
    
    if cron_file.exists():
        with open(cron_file, 'r') as f:
            content = f.read()
            # Check for warehouse ETL integration
            results["Warehouse ETL included"] = "Data Warehouse ETL Pipeline" in content
            results["run_all_etl.py called"] = "run_all_etl.py" in content
            results["Error handling present"] = "WAREHOUSE_ERRORLEVEL" in content
            results["Directory navigation present"] = "cd /d" in content and "data-warehouse" in content
    
    return results

def check_data_flow_paths() -> Dict[str, bool]:
    """Verify data flow paths are correctly configured."""
    print("\n🔍 Checking Data Flow Paths...")
    results = {}
    
    # Check curated data path
    curated_path = Path(__file__).parent.parent / "data_lake" / "curated"
    results["Curated directory exists"] = curated_path.exists()
    
    if curated_path.exists():
        csv_files = list(curated_path.glob("*.csv"))
        results["CSV files in curated"] = len(csv_files) > 0
        results["Number of curated files"] = len(csv_files)
    
    # Check warehouse database
    db_path = Path(__file__).parent.parent / "data-warehouse" / "bedrot_analytics.db"
    results["Warehouse database exists"] = db_path.exists()
    
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            results["Database has tables"] = len(tables) > 0
            results["Number of tables"] = len(tables)
            
            # Check for key tables
            key_tables = ['artists', 'tracks', 'financial_transactions', 'streaming_performance']
            for table in key_tables:
                results[f"Table '{table}' exists"] = table in tables
            
            conn.close()
        except Exception as e:
            results["Database error"] = str(e)
    
    return results

def test_sample_integrity_check() -> Dict[str, bool]:
    """Run a sample integrity check on existing data."""
    print("\n🔍 Testing Sample Integrity Check...")
    results = {}
    
    if not PANDAS_AVAILABLE:
        results["Pandas not available"] = "Skipping data validation tests"
        return results
    
    try:
        from common.integrity_checks import DataIntegrityChecker
        
        # Try to load a sample curated file
        curated_path = Path(__file__).parent.parent / "data_lake" / "curated"
        sample_files = list(curated_path.glob("*.csv"))
        
        if sample_files:
            sample_file = sample_files[0]
            results["Test file"] = sample_file.name
            
            # Load data
            df = pd.read_csv(sample_file)
            results["Rows loaded"] = len(df)
            
            # Run integrity check
            checker = DataIntegrityChecker(sample_file.stem)
            passed, validation_results = checker.validate_curated_promotion(df)
            
            results["Integrity check passed"] = passed
            results["Checks performed"] = validation_results.get('checks_performed', 0)
            results["Checks passed"] = validation_results.get('checks_passed', 0)
            
            # Extract specific check results
            if 'validation_details' in validation_results:
                details = validation_results['validation_details']
                results["Row count check"] = details.get('row_count', {}).get('passed', False)
                results["Data freshness check"] = details.get('data_freshness', {}).get('passed', False)
        else:
            results["No curated files found"] = True
            
    except Exception as e:
        results["Test error"] = str(e)
    
    return results

def generate_summary_report(all_results: Dict[str, Dict[str, any]]) -> None:
    """Generate a summary report of all checks."""
    print("\n" + "="*60)
    print("📊 PIPELINE INTEGRITY TEST SUMMARY")
    print("="*60)
    
    total_checks = 0
    passed_checks = 0
    
    for category, results in all_results.items():
        print(f"\n{category}:")
        print("-" * 40)
        
        for check, result in results.items():
            total_checks += 1
            status = "✅" if result == True else "❌" if result == False else "ℹ️"
            
            if result == True:
                passed_checks += 1
            
            # Format the output
            if isinstance(result, bool):
                print(f"  {status} {check}")
            else:
                print(f"  {status} {check}: {result}")
    
    # Overall summary
    print("\n" + "="*60)
    success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
    overall_status = "✅ PASSED" if success_rate >= 80 else "⚠️ NEEDS ATTENTION" if success_rate >= 60 else "❌ FAILED"
    
    print(f"Overall Status: {overall_status}")
    print(f"Checks Passed: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
    print("="*60)
    
    # Recommendations
    if success_rate < 100:
        print("\n📝 Recommendations:")
        
        if not all_results.get("Environment Setup", {}).get("Security warning added", False):
            print("  - Add security warnings to sensitive .env files")
            
        if not all_results.get("Curated Documentation", {}).get("DATASET_CONTEXT.md exists", False):
            print("  - Create DATASET_CONTEXT.md documentation")
            
        if not all_results.get("Cron Job Integration", {}).get("Warehouse ETL included", False):
            print("  - Update cron job to include warehouse ETL")
            
        if not all_results.get("Data Flow Paths", {}).get("Warehouse database exists", False):
            print("  - Initialize warehouse database with create_database.py")

def main():
    """Run all pipeline integrity tests."""
    print("🚀 BEDROT Data Pipeline Integrity Test")
    print("=" * 60)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: DRY RUN (no data modifications)")
    
    # Run all checks
    all_results = {
        "Environment Setup": check_environment_setup(),
        "Data Integrity Framework": check_data_integrity_framework(),
        "Curated Documentation": check_curated_documentation(),
        "Cron Job Integration": check_cron_job_integration(),
        "Data Flow Paths": check_data_flow_paths(),
    }
    
    # Run sample integrity check if framework is available
    if all_results["Data Integrity Framework"].get("Module imports successfully", False):
        all_results["Sample Integrity Check"] = test_sample_integrity_check()
    
    # Generate summary
    generate_summary_report(all_results)
    
    # Save detailed results
    results_file = Path(__file__).parent / f"pipeline_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Exit with appropriate code
    success_rate = sum(
        sum(1 for v in results.values() if v == True) 
        for results in all_results.values()
    ) / sum(len(results) for results in all_results.values()) * 100
    
    sys.exit(0 if success_rate >= 80 else 1)

if __name__ == "__main__":
    main()