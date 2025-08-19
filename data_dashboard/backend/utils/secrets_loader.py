"""Secrets loader following ultrathink standards."""
from dotenv import load_dotenv
import os
from pathlib import Path

# Load secrets with override
secrets_path = Path(__file__).parent.parent.parent / ".env.secrets"
load_dotenv(dotenv_path=secrets_path, override=True)

def get_secret(key: str, default: str = None) -> str:
    """Get secret from environment variables.
    
    Args:
        key: Environment variable key
        default: Default value if not found
        
    Returns:
        Secret value or default
    """
    return os.getenv(key, default)