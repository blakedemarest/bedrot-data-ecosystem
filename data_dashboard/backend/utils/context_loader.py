"""Context loader following ultrathink standards."""
from dotenv import load_dotenv
import os
from pathlib import Path

# Load context without override
context_path = Path(__file__).parent.parent.parent / ".env.context"
load_dotenv(dotenv_path=context_path, override=False)

def get_context_var(key: str, default: str = None) -> str:
    """Get context variable from environment.
    
    Args:
        key: Environment variable key
        default: Default value if not found
        
    Returns:
        Context value or default
    """
    return os.getenv(key, default)

# Convenience functions for common paths
def get_project_root() -> Path:
    """Get project root path."""
    return Path(get_context_var("PROJECT_ROOT"))

def get_curated_data_path() -> Path:
    """Get curated data path."""
    return Path(get_context_var("CURATED_DATA_PATH"))

def get_cache_dir() -> Path:
    """Get cache directory path."""
    cache_dir = get_project_root() / get_context_var("CACHE_DIR", "backend/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir