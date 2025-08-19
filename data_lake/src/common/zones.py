"""
Centralized zone configuration for BEDROT Data Lake.
Uses environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional

# Load environment variables from .env.context if it exists
def load_env_context():
    """Load environment variables from .env.context file if it exists."""
    env_file = Path(__file__).parent.parent.parent / ".env.context"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value

# Load context on import
load_env_context()

# Project root - must be set by calling script
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path(__file__).parent.parent.parent))

# Zone directories - using environment variables with defaults
LANDING_ZONE = PROJECT_ROOT / os.getenv("LANDING_ZONE", "1_landing")
RAW_ZONE = PROJECT_ROOT / os.getenv("RAW_ZONE", "2_raw")
STAGING_ZONE = PROJECT_ROOT / os.getenv("STAGING_ZONE", "3_staging")
CURATED_ZONE = PROJECT_ROOT / os.getenv("CURATED_ZONE", "4_curated")
ARCHIVE_ZONE = PROJECT_ROOT / os.getenv("ARCHIVE_ZONE", "5_archive")

# Log directory
LOG_DIR = PROJECT_ROOT / os.getenv("LOG_DIR", "logs")

# Service-specific zone helpers
def get_service_zone(service: str, zone: Path) -> Path:
    """Get the service-specific subdirectory within a zone."""
    return zone / service

def get_landing_path(service: str, subdir: Optional[str] = None) -> Path:
    """Get landing path for a service, optionally with subdirectory."""
    path = LANDING_ZONE / service
    if subdir:
        path = path / subdir
    return path

def get_raw_path(service: str, subdir: Optional[str] = None) -> Path:
    """Get raw path for a service, optionally with subdirectory."""
    path = RAW_ZONE / service
    if subdir:
        path = path / subdir
    return path

def get_staging_path(service: str, subdir: Optional[str] = None) -> Path:
    """Get staging path for a service, optionally with subdirectory."""
    path = STAGING_ZONE / service
    if subdir:
        path = path / subdir
    return path

def get_curated_path(filename: Optional[str] = None) -> Path:
    """Get curated path, optionally with filename."""
    if filename:
        return CURATED_ZONE / filename
    return CURATED_ZONE

def get_archive_path(service: str, subdir: Optional[str] = None) -> Path:
    """Get archive path for a service, optionally with subdirectory."""
    path = ARCHIVE_ZONE / service
    if subdir:
        path = path / subdir
    return path

# Cookie paths
def get_cookie_path(service: str) -> Path:
    """Get the cookie file path for a service."""
    cookie_filename = os.getenv(f"{service.upper()}_COOKIE_FILE", f"{service}_cookies.json")
    return PROJECT_ROOT / "src" / service / "cookies" / cookie_filename

# Service URLs
def get_service_url(service: str, url_type: str) -> str:
    """Get a service URL from environment variables."""
    env_key = f"{service.upper()}_{url_type.upper()}_URL"
    url = os.getenv(env_key)
    if not url:
        raise ValueError(f"No URL configured for {env_key}")
    return url

# Create all zone directories if they don't exist
def ensure_zones_exist():
    """Create all zone directories if they don't exist."""
    for zone in [LANDING_ZONE, RAW_ZONE, STAGING_ZONE, CURATED_ZONE, ARCHIVE_ZONE, LOG_DIR]:
        zone.mkdir(parents=True, exist_ok=True)

# Configuration validation
def validate_configuration():
    """Validate that all required environment variables are set."""
    required_vars = ["PROJECT_ROOT"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Export all zone paths
__all__ = [
    'PROJECT_ROOT',
    'LANDING_ZONE',
    'RAW_ZONE', 
    'STAGING_ZONE',
    'CURATED_ZONE',
    'ARCHIVE_ZONE',
    'LOG_DIR',
    'get_service_zone',
    'get_landing_path',
    'get_raw_path',
    'get_staging_path',
    'get_curated_path',
    'get_archive_path',
    'get_cookie_path',
    'get_service_url',
    'ensure_zones_exist',
    'validate_configuration'
]