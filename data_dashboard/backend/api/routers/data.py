"""General data access API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional

from backend.data.csv_loader import CSVDataLoader

router = APIRouter()
loader = CSVDataLoader()

@router.get("/files")
async def list_available_files() -> Dict[str, Any]:
    """List all available CSV files in curated zone.
    
    Returns:
        List of available files with metadata
    """
    try:
        files = loader.list_available_files()
        
        # Get metadata for each file
        file_info = []
        for filename in files:
            metadata = loader.get_file_metadata(filename)
            if metadata:
                file_info.append(metadata)
        
        return {
            "success": True,
            "data": file_info,
            "metadata": {
                "total_files": len(file_info),
                "data_zone": "curated",
                "description": "Production-ready datasets"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/file/{filename}")
async def get_file_data(
    filename: str,
    limit: Optional[int] = Query(None, description="Limit number of rows returned"),
    offset: Optional[int] = Query(0, description="Skip first N rows")
) -> Dict[str, Any]:
    """Get data from a specific CSV file.
    
    Args:
        filename: Name of the CSV file
        limit: Maximum number of rows to return
        offset: Number of rows to skip
        
    Returns:
        File data with metadata
    """
    try:
        data = loader.load_csv(filename)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        # Apply pagination
        total_rows = len(data)
        if offset:
            data = data[offset:]
        if limit:
            data = data[:limit]
        
        return {
            "success": True,
            "data": data,
            "metadata": {
                "filename": filename,
                "total_rows": total_rows,
                "returned_rows": len(data),
                "offset": offset,
                "limit": limit,
                "columns": list(data[0].keys()) if data else []
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metadata/{filename}")
async def get_file_metadata(filename: str) -> Dict[str, Any]:
    """Get metadata about a specific CSV file.
    
    Args:
        filename: Name of the CSV file
        
    Returns:
        File metadata
    """
    try:
        metadata = loader.get_file_metadata(filename)
        
        if not metadata:
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        return {
            "success": True,
            "data": metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reload-cache")
async def reload_cache(filename: Optional[str] = None) -> Dict[str, Any]:
    """Force reload data from disk, bypassing cache.
    
    Args:
        filename: Specific file to reload, or None for all
        
    Returns:
        Reload status
    """
    try:
        if filename:
            data = loader.load_csv(filename, force_reload=True)
            return {
                "success": True,
                "message": f"Reloaded {filename}",
                "rows_loaded": len(data)
            }
        else:
            # Reload all common files
            files_to_reload = [
                "dk_bank_details.csv",
                "tidy_daily_streams.csv",
                "metaads_campaigns_daily.csv"
            ]
            
            results = {}
            for file in files_to_reload:
                try:
                    data = loader.load_csv(file, force_reload=True)
                    results[file] = len(data)
                except:
                    results[file] = "error"
            
            return {
                "success": True,
                "message": "Cache reloaded",
                "files": results
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schema")
async def get_data_schema() -> Dict[str, Any]:
    """Get schema information for all available datasets.
    
    Returns:
        Schema information with field descriptions
    """
    schemas = {
        "dk_bank_details.csv": {
            "description": "DistroKid streaming revenue transactions",
            "fields": {
                "Reporting Date": "Date of transaction (YYYY-MM-DD)",
                "Sale Month": "Month of the sale (YYYY-MM)",
                "Store": "Platform name (Spotify, Apple Music, etc.)",
                "Artist": "Artist name (PIG1987 or ZONE A0)",
                "Title": "Track or album title",
                "Quantity": "Number of streams or sales",
                "Earnings (USD)": "Revenue in USD"
            }
        },
        "tidy_daily_streams.csv": {
            "description": "Consolidated daily streaming metrics",
            "fields": {
                "date": "Stream date (YYYY-MM-DD)",
                "spotify_streams": "Daily Spotify streams",
                "apple_streams": "Daily Apple Music streams",
                "combined_streams": "Total daily streams",
                "source": "Data source (distrokid or toolost)"
            }
        },
        "metaads_campaigns_daily.csv": {
            "description": "Meta advertising campaign performance",
            "fields": {
                "date": "Campaign date (YYYY-MM-DD)",
                "campaign_id": "Meta campaign identifier",
                "campaign_name": "Human-readable campaign name",
                "impressions": "Number of ad impressions",
                "clicks": "Number of link clicks",
                "spend": "Daily ad spend in USD",
                "conversions": "Number of conversion events",
                "cpc": "Cost per click",
                "ctr": "Click-through rate percentage"
            }
        },
        "tiktok_analytics_curated_*.csv": {
            "description": "TikTok Creator analytics",
            "fields": {
                "date": "Analytics date (YYYY-MM-DD)",
                "artist": "TikTok account (pig1987 or zonea0)",
                "video_views": "Daily video views",
                "profile_views": "Profile page views",
                "likes": "Total likes received",
                "comments": "Comments received",
                "shares": "Video shares",
                "new_followers": "Net follower change",
                "engagement_rate": "Engagement rate percentage"
            }
        }
    }
    
    return {
        "success": True,
        "data": schemas,
        "metadata": {
            "description": "Data schema for AI agent consumption",
            "note": "Use this to understand available fields before querying"
        }
    }