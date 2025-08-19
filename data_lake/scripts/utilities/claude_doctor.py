#!/usr/bin/env python
"""Claude Doctor - Diagnose data lake environment issues."""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_section(text):
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-'*len(text)}{Colors.ENDC}")

def check_environment():
    """Check environment setup."""
    issues = []
    
    # Check PROJECT_ROOT
    project_root = os.environ.get('PROJECT_ROOT')
    if not project_root:
        issues.append("PROJECT_ROOT environment variable not set")
    elif not Path(project_root).exists():
        issues.append(f"PROJECT_ROOT path does not exist: {project_root}")
    
    # Check virtual environment
    if not Path('.venv').exists():
        issues.append("Virtual environment .venv not found")
    
    # Check Python version
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        issues.append(f"Python version {version.major}.{version.minor} is too old (need 3.8+)")
    
    return issues

def check_dependencies():
    """Check if required packages are installed."""
    issues = []
    required = [
        'pandas', 'numpy', 'requests', 'playwright', 
        'bs4', 'dotenv', 'loguru', 'tqdm', 'lxml',
        'boto3', 'sqlalchemy', 'openpyxl'
    ]
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            issues.append(f"Missing package: {pkg}")
    
    return issues

def check_directory_structure():
    """Check if required directories exist."""
    issues = []
    required_dirs = [
        '1_landing', '2_raw', '3_staging', '4_curated', '5_archive',
        '6_automated_cronjob', 'src', 'tests', 'docs', 'logs'
    ]
    
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            issues.append(f"Missing directory: {dir_name}")
    
    return issues

def check_data_freshness():
    """Check how fresh the data is in each zone."""
    freshness = {}
    zones = ['1_landing', '2_raw', '3_staging', '4_curated']
    
    for zone in zones:
        zone_path = Path(zone)
        if zone_path.exists():
            latest_time = None
            file_count = 0
            
            for file in zone_path.rglob('*'):
                if file.is_file():
                    file_count += 1
                    mtime = datetime.fromtimestamp(file.stat().st_mtime)
                    if latest_time is None or mtime > latest_time:
                        latest_time = mtime
            
            if latest_time:
                age = datetime.now() - latest_time
                freshness[zone] = {
                    'latest_file': latest_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'age_days': age.days,
                    'file_count': file_count
                }
            else:
                freshness[zone] = {'status': 'empty'}
    
    return freshness

def check_cookies():
    """Check cookie status for each service."""
    cookie_status = {}
    services = ['spotify', 'distrokid', 'tiktok', 'toolost', 'linktree', 'metaads']
    
    for service in services:
        cookie_path = Path(f'src/{service}/cookies')
        if cookie_path.exists():
            cookie_files = list(cookie_path.glob('*.json'))
            if cookie_files:
                latest = max(cookie_files, key=lambda p: p.stat().st_mtime)
                age = datetime.now() - datetime.fromtimestamp(latest.stat().st_mtime)
                cookie_status[service] = {
                    'file': latest.name,
                    'age_days': age.days,
                    'status': 'OK' if age.days < 7 else 'OLD' if age.days < 30 else 'EXPIRED'
                }
            else:
                cookie_status[service] = {'status': 'NO_COOKIES'}
        else:
            cookie_status[service] = {'status': 'NO_COOKIE_DIR'}
    
    return cookie_status

def check_recent_errors():
    """Check for recent errors in logs."""
    errors = []
    log_dir = Path('logs')
    
    if log_dir.exists():
        # Check last 24 hours of logs
        cutoff = datetime.now() - timedelta(days=1)
        
        for log_file in log_dir.glob('*.log'):
            if datetime.fromtimestamp(log_file.stat().st_mtime) > cutoff:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if 'ERROR' in line or 'FAILED' in line:
                            errors.append({
                                'file': log_file.name,
                                'error': line.strip()[:200]
                            })
    
    return errors[-10:] if errors else []  # Last 10 errors

def run_diagnosis():
    """Run full diagnosis."""
    print_header("CLAUDE DOCTOR - DATA LAKE DIAGNOSIS")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working Directory: {os.getcwd()}")
    
    # Environment check
    print_section("1. Environment Check")
    env_issues = check_environment()
    if env_issues:
        for issue in env_issues:
            print(f"{Colors.FAIL}✗ {issue}{Colors.ENDC}")
    else:
        print(f"{Colors.OKGREEN}✓ Environment configured correctly{Colors.ENDC}")
    
    # Dependencies check
    print_section("2. Dependencies Check")
    dep_issues = check_dependencies()
    if dep_issues:
        for issue in dep_issues:
            print(f"{Colors.FAIL}✗ {issue}{Colors.ENDC}")
    else:
        print(f"{Colors.OKGREEN}✓ All required packages installed{Colors.ENDC}")
    
    # Directory structure
    print_section("3. Directory Structure")
    dir_issues = check_directory_structure()
    if dir_issues:
        for issue in dir_issues:
            print(f"{Colors.WARNING}⚠ {issue}{Colors.ENDC}")
    else:
        print(f"{Colors.OKGREEN}✓ All required directories present{Colors.ENDC}")
    
    # Data freshness
    print_section("4. Data Freshness")
    freshness = check_data_freshness()
    for zone, info in freshness.items():
        if 'status' in info and info['status'] == 'empty':
            print(f"{Colors.WARNING}⚠ {zone}: Empty{Colors.ENDC}")
        else:
            age = info['age_days']
            color = Colors.OKGREEN if age < 7 else Colors.WARNING if age < 30 else Colors.FAIL
            print(f"{color}• {zone}: {info['file_count']} files, latest from {age} days ago{Colors.ENDC}")
    
    # Cookie status
    print_section("5. Cookie Status")
    cookies = check_cookies()
    for service, info in cookies.items():
        if 'status' in info:
            if info['status'] == 'OK':
                print(f"{Colors.OKGREEN}✓ {service}: {info['status']}{Colors.ENDC}")
            elif info['status'] == 'OLD':
                print(f"{Colors.WARNING}⚠ {service}: {info['status']} ({info.get('age_days', '?')} days){Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}✗ {service}: {info['status']}{Colors.ENDC}")
    
    # Recent errors
    print_section("6. Recent Errors")
    errors = check_recent_errors()
    if errors:
        for error in errors[-5:]:  # Show last 5
            print(f"{Colors.FAIL}• {error['file']}: {error['error'][:100]}...{Colors.ENDC}")
    else:
        print(f"{Colors.OKGREEN}✓ No recent errors found{Colors.ENDC}")
    
    # Recommendations
    print_section("7. Recommendations")
    
    recommendations = []
    
    if env_issues:
        recommendations.append("Set PROJECT_ROOT environment variable")
    
    if dep_issues:
        recommendations.append("Run: pip install -r requirements-minimal.txt")
    
    if any(info.get('status') in ['OLD', 'EXPIRED', 'NO_COOKIES'] for info in cookies.values()):
        recommendations.append("Refresh cookies for expired services")
    
    if any(info.get('age_days', 0) > 7 for info in freshness.values() if 'age_days' in info):
        recommendations.append("Run data pipeline to update stale data")
    
    if recommendations:
        print(f"{Colors.WARNING}Actions needed:{Colors.ENDC}")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    else:
        print(f"{Colors.OKGREEN}✓ System appears healthy!{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Next step: Run 'python test_components.py' for detailed component testing{Colors.ENDC}")

if __name__ == '__main__':
    # Set PROJECT_ROOT if not set
    if not os.environ.get('PROJECT_ROOT'):
        os.environ['PROJECT_ROOT'] = str(Path(__file__).parent.absolute())
    
    try:
        run_diagnosis()
    except Exception as e:
        print(f"{Colors.FAIL}Doctor crashed: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()