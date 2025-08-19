"""CSV data loader with caching for curated zone data."""
import csv
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from backend.utils.context_loader import get_curated_data_path, get_cache_dir, get_context_var

logger = logging.getLogger(__name__)

class CSVDataLoader:
    """Load and cache CSV data from curated zone."""
    
    def __init__(self):
        self.curated_path = get_curated_data_path()
        self.cache_dir = get_cache_dir()
        self.cache_ttl = int(get_context_var("CACHE_TTL", "300"))  # 5 minutes default
        
    def _get_cache_key(self, file_path: Path) -> str:
        """Generate cache key for file."""
        stat = file_path.stat()
        content = f"{file_path}_{stat.st_mtime}_{stat.st_size}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache is still valid."""
        if not cache_path.exists():
            return False
        
        cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        return cache_age.total_seconds() < self.cache_ttl
    
    def load_csv(self, filename: str, force_reload: bool = False) -> List[Dict[str, Any]]:
        """Load CSV file with caching.
        
        Args:
            filename: Name of CSV file in curated zone
            force_reload: Force reload from disk, bypass cache
            
        Returns:
            List of dictionaries representing CSV rows
        """
        file_path = self.curated_path / filename
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        # Check cache
        cache_key = self._get_cache_key(file_path)
        cache_path = self._get_cache_path(cache_key)
        
        if not force_reload and self._is_cache_valid(cache_path):
            logger.info(f"Loading from cache: {filename}")
            with open(cache_path, 'r') as f:
                return json.load(f)
        
        # Load from CSV
        logger.info(f"Loading from disk: {filename}")
        data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert numeric fields
                    for key, value in row.items():
                        if value:
                            # Try to convert to number
                            try:
                                if '.' in value:
                                    row[key] = float(value)
                                else:
                                    row[key] = int(value)
                            except ValueError:
                                pass  # Keep as string
                    data.append(row)
            
            # Save to cache
            with open(cache_path, 'w') as f:
                json.dump(data, f)
            
            logger.info(f"Loaded {len(data)} rows from {filename}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return []
    
    def load_multiple(self, filenames: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Load multiple CSV files.
        
        Args:
            filenames: List of CSV filenames
            
        Returns:
            Dictionary mapping filename to data
        """
        result = {}
        for filename in filenames:
            result[filename] = self.load_csv(filename)
        return result
    
    def get_latest_file(self, pattern: str) -> Optional[str]:
        """Get the latest file matching a pattern.
        
        Args:
            pattern: Glob pattern (e.g., 'tiktok_analytics_curated_*.csv')
            
        Returns:
            Filename of the latest matching file
        """
        files = list(self.curated_path.glob(pattern))
        if not files:
            return None
        
        # Sort by modification time
        latest = max(files, key=lambda f: f.stat().st_mtime)
        return latest.name
    
    def list_available_files(self) -> List[str]:
        """List all available CSV files in curated zone."""
        csv_files = self.curated_path.glob("*.csv")
        return sorted([f.name for f in csv_files])
    
    def get_file_metadata(self, filename: str) -> Dict[str, Any]:
        """Get metadata about a CSV file.
        
        Args:
            filename: Name of CSV file
            
        Returns:
            Dictionary with file metadata
        """
        file_path = self.curated_path / filename
        
        if not file_path.exists():
            return {}
        
        stat = file_path.stat()
        data = self.load_csv(filename)
        
        return {
            "filename": filename,
            "path": str(file_path),
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "row_count": len(data),
            "column_count": len(data[0]) if data else 0,
            "columns": list(data[0].keys()) if data else []
        }