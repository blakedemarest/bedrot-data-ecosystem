#!/usr/bin/env python3
"""
Wrapper script for running extractors with authentication checks.
Handles cookie validation and prompts for manual authentication when needed.
Enhanced with comprehensive logging using the existing logging infrastructure.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import time
import uuid
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import our existing logging infrastructure
from logging_config import setup_logging, get_logger, with_correlation_id, log_performance

# Initialize logging
loggers = setup_logging(
    log_level=os.getenv('LOG_LEVEL', 'INFO'),
    service_name='pipeline_executor'
)
logger = get_logger('pipeline.executor')
correlation_filter = loggers.get('_correlation_filter')

# Service configuration
AUTH_SERVICES = {
    "spotify": {
        "cookie_max_age_days": 30,
        "manual_script": "src/spotify/extractors/spotify_audience_extractor.py",
        "automated_scripts": [
            "src/spotify/extractors/spotify_audience_extractor.py"
        ]
    },
    "toolost": {
        "cookie_max_age_days": 7,
        "manual_script": "src/toolost/extractors/toolost_scraper.py",
        "automated_scripts": [
            "src/toolost/extractors/toolost_scraper_automated.py"
        ]
    },
    "distrokid": {
        "cookie_max_age_days": 14,
        "manual_script": "src/distrokid/extractors/dk_auth.py",
        "automated_scripts": [
            "src/distrokid/extractors/dk_auth.py"
        ]
    },
    "tiktok": {
        "cookie_max_age_days": 7,
        "manual_script": "src/tiktok/extractors/tiktok_analytics_extractor_zonea0.py",
        "automated_scripts": [
            "src/tiktok/extractors/tiktok_analytics_extractor_zonea0.py",
            "src/tiktok/extractors/tiktok_analytics_extractor_pig1987.py"
        ]
    },
    "linktree": {
        "cookie_max_age_days": 30,
        "manual_script": "src/linktree/extractors/linktree_analytics_extractor.py",
        "automated_scripts": [
            "src/linktree/extractors/linktree_analytics_extractor.py"
        ]
    },
    "metaads": {
        "cookie_max_age_days": 90,
        "manual_script": "src/metaads/extractors/meta_daily_campaigns_extractor.py",
        "automated_scripts": [
            "src/metaads/extractors/meta_daily_campaigns_extractor.py"
        ]
    }
}


def check_cookie_freshness(service: str) -> tuple[bool, str, int]:
    """
    Check if cookies for a service are fresh enough.
    Returns (is_fresh, reason, days_old)
    """
    project_root = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[2]))
    # Cookies are stored in each service's cookies directory
    cookie_file = project_root / "src" / service / "cookies" / f"{service}_cookies.json"
    
    # Special case for TikTok - check for multiple cookie files
    if service == "tiktok":
        cookie_dir = project_root / "src" / service / "cookies"
        if cookie_dir.exists():
            cookie_files = list(cookie_dir.glob("tiktok_cookies_*.json"))
            if cookie_files:
                # Use the most recently modified cookie file
                cookie_file = max(cookie_files, key=lambda f: f.stat().st_mtime)
    
    if not cookie_file.exists():
        return False, "Cookie file does not exist", -1
    
    try:
        # Check file age
        file_age = datetime.now() - datetime.fromtimestamp(cookie_file.stat().st_mtime)
        days_old = file_age.days
        max_age = AUTH_SERVICES[service]["cookie_max_age_days"]
        
        if days_old > max_age:
            return False, f"Cookies are {days_old} days old (max: {max_age})", days_old
        
        # Check cookie content
        with open(cookie_file) as f:
            cookies = json.load(f)
        
        if not cookies:
            return False, "Cookie file is empty", days_old
        
        # Check for expired cookies
        now = datetime.now().timestamp()
        expired_count = 0
        for cookie in cookies:
            if "expires" in cookie and cookie["expires"] > 0 and cookie["expires"] < now:
                expired_count += 1
        
        if expired_count > 0:
            return False, f"{expired_count} cookies have expired", days_old
        
        return True, f"Cookies are {days_old} days old and valid", days_old
        
    except Exception as e:
        return False, f"Error checking cookies: {e}", -1


def run_manual_auth(service: str) -> bool:
    """
    Run manual authentication for a service with logging.
    Returns True if successful.
    """
    if service not in AUTH_SERVICES:
        logger.error(f"Unknown service: {service}")
        return False
    
    manual_script = AUTH_SERVICES[service]["manual_script"]
    
    # Generate correlation ID for this authentication
    auth_id = str(uuid.uuid4())
    if correlation_filter:
        correlation_filter.set_correlation_id(auth_id)
    
    logger.info(f"Starting manual authentication", extra={
        'service': service,
        'script': manual_script,
        'auth_id': auth_id
    })
    
    print("\n" + "="*70)
    print(f"MANUAL AUTHENTICATION REQUIRED FOR {service.upper()}")
    print("="*70)
    print(f"Running: python {manual_script}")
    print("Please complete the login process in the browser window.")
    print("="*70 + "\n")
    
    start_time = time.time()
    
    try:
        # Run the manual authentication script
        result = subprocess.run(
            f"python {manual_script}",
            shell=True,
            cwd=os.getenv("PROJECT_ROOT"),
            capture_output=False  # Allow interactive input/output
        )
        
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"Manual authentication completed successfully", extra={
                'service': service,
                'script': manual_script,
                'auth_id': auth_id,
                'duration_seconds': round(execution_time, 2),
                'exit_code': result.returncode
            })
            print(f"\n[AUTH] OK: Manual authentication for {service} completed successfully")
            return True
        else:
            logger.error(f"Manual authentication failed", extra={
                'service': service,
                'script': manual_script,
                'auth_id': auth_id,
                'duration_seconds': round(execution_time, 2),
                'exit_code': result.returncode
            })
            print(f"\n[AUTH] FAILED: Manual authentication for {service} failed")
            return False
            
    except Exception as e:
        execution_time = time.time() - start_time
        logger.exception(f"Exception during manual authentication", extra={
            'service': service,
            'script': manual_script,
            'auth_id': auth_id,
            'duration_seconds': round(execution_time, 2),
            'error': str(e)
        })
        print(f"\n[AUTH] ERROR: Error running manual authentication: {e}")
        return False
    
    finally:
        # Clear correlation ID
        if correlation_filter:
            correlation_filter.clear_correlation_id()


def run_automated_extractors(service: str) -> bool:
    """
    Run automated extractors for a service with comprehensive logging.
    Returns True if all successful.
    """
    if service not in AUTH_SERVICES:
        logger.error(f"Unknown service: {service}")
        return False
    
    all_success = True
    
    for script in AUTH_SERVICES[service]["automated_scripts"]:
        # Generate correlation ID for this extraction
        extraction_id = str(uuid.uuid4())
        if correlation_filter:
            correlation_filter.set_correlation_id(extraction_id)
        
        logger.info(f"Starting extraction", extra={
            'service': service,
            'script': script,
            'extraction_id': extraction_id,
            'working_dir': os.getenv("PROJECT_ROOT")
        })
        
        # Log the exact command being executed
        command = f"python {script}"
        logger.info(f"Executing command: {command}")
        
        # Record start time
        start_time = time.time()
        
        try:
            # Create the command with proper environment
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'  # Ensure real-time output
            
            # Run the command with Popen for better control
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=os.getenv("PROJECT_ROOT"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            # Capture output in real-time
            stdout_lines = []
            stderr_lines = []
            
            # Read stdout and stderr
            stdout, stderr = process.communicate()
            
            if stdout:
                stdout_lines = stdout.splitlines()
                for line in stdout_lines:
                    logger.debug(f"[{service}] STDOUT: {line}")
            
            if stderr:
                stderr_lines = stderr.splitlines()
                for line in stderr_lines:
                    logger.error(f"[{service}] STDERR: {line}")
            
            # Wait for process to complete
            return_code = process.returncode
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            if return_code == 0:
                logger.info(f"Extraction completed successfully", extra={
                    'service': service,
                    'script': script,
                    'extraction_id': extraction_id,
                    'duration_seconds': round(execution_time, 2),
                    'exit_code': return_code,
                    'stdout_lines': len(stdout_lines),
                    'stderr_lines': len(stderr_lines)
                })
                
                # Also print to console for backward compatibility
                print(f"[AUTH] OK: {script} completed successfully")
                if stdout and logger.level <= 10:  # DEBUG level
                    print(stdout)
            else:
                # Log detailed error information
                logger.error(f"Extraction failed", extra={
                    'service': service,
                    'script': script,
                    'extraction_id': extraction_id,
                    'duration_seconds': round(execution_time, 2),
                    'exit_code': return_code,
                    'stdout_lines': len(stdout_lines),
                    'stderr_lines': len(stderr_lines)
                })
                
                # Log full error output for debugging
                if stderr:
                    logger.error(f"Full error output:\n{stderr}")
                if stdout:
                    logger.error(f"Full standard output:\n{stdout}")
                
                # Also print to console for backward compatibility
                print(f"[AUTH] FAILED: {script} failed with code {return_code}")
                if stderr:
                    print("STDERR:", stderr)
                if stdout:
                    print("STDOUT:", stdout)
                
                all_success = False
                
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Log the exception with full traceback
            logger.exception(f"Exception running extractor", extra={
                'service': service,
                'script': script,
                'extraction_id': extraction_id,
                'duration_seconds': round(execution_time, 2),
                'error': str(e)
            })
            
            # Also print to console
            print(f"[AUTH] ERROR: Error running {script}: {e}")
            all_success = False
        
        finally:
            # Clear correlation ID
            if correlation_filter:
                correlation_filter.clear_correlation_id()
    
    return all_success


def check_and_run_service(service: str, force_manual: bool = False) -> bool:
    """
    Check authentication status and run extractors for a service.
    Returns True if successful.
    """
    print(f"\n{'='*70}")
    print(f"Processing {service.upper()}")
    print('='*70)
    
    if force_manual:
        print(f"[AUTH] Forcing manual authentication for {service}")
        if not run_manual_auth(service):
            return False
    else:
        # Check cookie freshness
        is_fresh, reason, days_old = check_cookie_freshness(service)
        
        print(f"[AUTH] Cookie status for {service}: {reason}")
        
        if not is_fresh:
            # Determine if we should prompt for manual auth
            if days_old >= 0:  # Cookies exist but are old/expired
                print(f"\n[AUTH] ⚠️  Cookies for {service} need refresh")
                
                # In automated mode, skip services with expired cookies
                if os.getenv("AUTOMATED_MODE", "false").lower() == "true":
                    print(f"[AUTH] Skipping {service} - manual authentication required")
                    return False
                
                # Otherwise, prompt for manual auth
                response = input(f"\nRun manual authentication for {service}? (y/n): ").lower()
                if response == 'y':
                    if not run_manual_auth(service):
                        return False
                else:
                    print(f"[AUTH] Skipping {service} extractors")
                    return False
            else:
                # No cookies at all
                print(f"[AUTH] No cookies found for {service}")
                if os.getenv("AUTOMATED_MODE", "false").lower() == "true":
                    print(f"[AUTH] Skipping {service} - no cookies available")
                    return False
                
                response = input(f"\nSetup authentication for {service}? (y/n): ").lower()
                if response == 'y':
                    if not run_manual_auth(service):
                        return False
                else:
                    print(f"[AUTH] Skipping {service} extractors")
                    return False
    
    # Run automated extractors
    return run_automated_extractors(service)


def run_single_script(script_path: str, service: str = "unknown") -> int:
    """
    Run a single script with full logging.
    This can be used to run any Python script, not just extractors.
    Returns the exit code.
    """
    # Generate correlation ID for this execution
    execution_id = str(uuid.uuid4())
    if correlation_filter:
        correlation_filter.set_correlation_id(execution_id)
    
    logger.info(f"Starting script execution", extra={
        'service': service,
        'script': script_path,
        'execution_id': execution_id,
        'working_dir': os.getenv("PROJECT_ROOT", os.getcwd())
    })
    
    command = f"python {script_path}"
    logger.info(f"Executing command: {command}")
    
    start_time = time.time()
    
    try:
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=os.getenv("PROJECT_ROOT", os.getcwd()),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        stdout, stderr = process.communicate()
        return_code = process.returncode
        execution_time = time.time() - start_time
        
        # Log output based on result
        if return_code == 0:
            logger.info(f"Script execution completed successfully", extra={
                'service': service,
                'script': script_path,
                'execution_id': execution_id,
                'duration_seconds': round(execution_time, 2),
                'exit_code': return_code
            })
            if stdout:
                logger.debug(f"Script output:\n{stdout}")
        else:
            logger.error(f"Script execution failed", extra={
                'service': service,
                'script': script_path,
                'execution_id': execution_id,
                'duration_seconds': round(execution_time, 2),
                'exit_code': return_code
            })
            if stderr:
                logger.error(f"Error output:\n{stderr}")
            if stdout:
                logger.error(f"Standard output:\n{stdout}")
        
        return return_code
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.exception(f"Exception running script", extra={
            'service': service,
            'script': script_path,
            'execution_id': execution_id,
            'duration_seconds': round(execution_time, 2),
            'error': str(e)
        })
        return 1
    
    finally:
        if correlation_filter:
            correlation_filter.clear_correlation_id()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run extractors with authentication checks and enhanced logging",
        epilog="Examples:\n"
               "  %(prog)s                    # Run all services\n"
               "  %(prog)s spotify tiktok     # Run specific services\n"
               "  %(prog)s --check-only       # Check auth status only\n"
               "  %(prog)s --script path/to/script.py --service myservice  # Run any script\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("services", nargs="*", 
                       help="Services to process (default: all)")
    parser.add_argument("--manual", "-m", action="store_true",
                       help="Force manual authentication for all services")
    parser.add_argument("--check-only", "-c", action="store_true",
                       help="Only check authentication status, don't run extractors")
    parser.add_argument("--script", "-s", type=str,
                       help="Run a single script with logging (bypasses auth checks)")
    parser.add_argument("--service", type=str, default="unknown",
                       help="Service name for --script mode (for logging)")
    parser.add_argument("--log-level", "-l", type=str, 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       default=os.getenv('LOG_LEVEL', 'INFO'),
                       help="Set logging level")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Suppress console output (logs still written to files)")
    
    args = parser.parse_args()
    
    # Update log level if specified
    if args.log_level != os.getenv('LOG_LEVEL', 'INFO'):
        import logging
        logging.getLogger().setLevel(getattr(logging, args.log_level))
        logger.info(f"Log level set to {args.log_level}")
    
    # Handle single script mode
    if args.script:
        logger.info(f"Running in single script mode: {args.script}")
        exit_code = run_single_script(args.script, args.service)
        return exit_code
    
    # Determine which services to process
    if args.services:
        services = args.services
    else:
        services = list(AUTH_SERVICES.keys())
    
    # Validate services
    invalid_services = [s for s in services if s not in AUTH_SERVICES]
    if invalid_services:
        print(f"ERROR: Unknown services: {invalid_services}")
        print(f"Valid services: {list(AUTH_SERVICES.keys())}")
        return 1
    
    if args.check_only:
        # Just check status
        print("\nAUTHENTICATION STATUS CHECK")
        print("="*70)
        
        for service in services:
            is_fresh, reason, days_old = check_cookie_freshness(service)
            status = "[OK]" if is_fresh else "[NEEDS REFRESH]"
            print(f"{service:12} {status:20} {reason}")
        
        return 0
    
    # Process each service
    failed_services = []
    
    for service in services:
        if not check_and_run_service(service, force_manual=args.manual):
            failed_services.append(service)
    
    # Summary with enhanced logging
    print("\n" + "="*70)
    print("EXTRACTION SUMMARY")
    print("="*70)
    
    successful = [s for s in services if s not in failed_services]
    
    # Log summary to structured logs
    logger.info("Pipeline execution summary", extra={
        'total_services': len(services),
        'successful_services': len(successful),
        'failed_services': len(failed_services),
        'successful': successful,
        'failed': failed_services
    })
    
    if successful:
        print(f"OK: Successful: {', '.join(successful)}")
    
    if failed_services:
        print(f"FAILED: Failed: {', '.join(failed_services)}")
        logger.error(f"Pipeline completed with failures: {', '.join(failed_services)}")
        return 1
    
    logger.info("Pipeline completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())