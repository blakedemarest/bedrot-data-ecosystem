"""Streaming data API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from backend.data.csv_loader import CSVDataLoader

router = APIRouter()
loader = CSVDataLoader()

@router.get("/daily")
async def get_daily_streams(
    days: int = Query(30, description="Number of days to retrieve", ge=1, le=365)
) -> Dict[str, Any]:
    """Get daily streaming data.
    
    Args:
        days: Number of days to retrieve
        
    Returns:
        Dictionary with daily streaming data
    """
    try:
        data = loader.load_csv("tidy_daily_streams.csv")
        
        # Get last N days
        if data:
            data = data[-days:]
        
        return {
            "success": True,
            "data": data,
            "metadata": {
                "source": "tidy_daily_streams.csv",
                "days_requested": days,
                "days_returned": len(data),
                "last_updated": datetime.now().isoformat(),
                "limitations": [
                    "No artist-level detail available",
                    "Aggregated from multiple distributors"
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_streaming_summary() -> Dict[str, Any]:
    """Get streaming summary statistics.
    
    Returns:
        Dictionary with summary statistics
    """
    try:
        data = loader.load_csv("tidy_daily_streams.csv")
        
        if not data:
            return {
                "success": False,
                "error": "No streaming data available"
            }
        
        # Calculate summary statistics
        total_spotify = sum(row.get("spotify_streams", 0) for row in data)
        total_apple = sum(row.get("apple_streams", 0) for row in data)
        total_combined = sum(row.get("combined_streams", 0) for row in data)
        
        # Group by source
        by_source = defaultdict(lambda: {"spotify": 0, "apple": 0, "total": 0, "days": 0})
        for row in data:
            source = row.get("source", "unknown")
            by_source[source]["spotify"] += row.get("spotify_streams", 0)
            by_source[source]["apple"] += row.get("apple_streams", 0)
            by_source[source]["total"] += row.get("combined_streams", 0)
            by_source[source]["days"] += 1
        
        return {
            "success": True,
            "data": {
                "total_streams": {
                    "spotify": total_spotify,
                    "apple": total_apple,
                    "combined": total_combined
                },
                "by_distributor": dict(by_source),
                "date_range": {
                    "start": data[0]["date"] if data else None,
                    "end": data[-1]["date"] if data else None,
                    "days": len(data)
                },
                "daily_average": {
                    "spotify": total_spotify / len(data) if data else 0,
                    "apple": total_apple / len(data) if data else 0,
                    "combined": total_combined / len(data) if data else 0
                }
            },
            "metadata": {
                "source": "tidy_daily_streams.csv",
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/growth")
async def get_streaming_growth(
    period: str = Query("monthly", description="Growth period: daily, weekly, monthly")
) -> Dict[str, Any]:
    """Calculate streaming growth metrics.
    
    Args:
        period: Period for growth calculation
        
    Returns:
        Dictionary with growth metrics
    """
    try:
        data = loader.load_csv("tidy_daily_streams.csv")
        
        if not data or len(data) < 2:
            return {
                "success": False,
                "error": "Insufficient data for growth calculation"
            }
        
        # Group by period
        grouped = defaultdict(lambda: {"spotify": 0, "apple": 0, "total": 0})
        
        for row in data:
            date_str = row.get("date", "")
            if not date_str:
                continue
            
            if period == "daily":
                key = date_str
            elif period == "weekly":
                # Get week number
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                key = date_obj.strftime("%Y-W%U")
            else:  # monthly
                key = date_str[:7]  # YYYY-MM
            
            grouped[key]["spotify"] += row.get("spotify_streams", 0)
            grouped[key]["apple"] += row.get("apple_streams", 0)
            grouped[key]["total"] += row.get("combined_streams", 0)
        
        # Calculate growth rates
        periods = sorted(grouped.keys())
        growth_data = []
        
        for i in range(1, len(periods)):
            prev_period = periods[i-1]
            curr_period = periods[i]
            
            prev_data = grouped[prev_period]
            curr_data = grouped[curr_period]
            
            growth_record = {
                "period": curr_period,
                "spotify_streams": curr_data["spotify"],
                "apple_streams": curr_data["apple"],
                "total_streams": curr_data["total"],
                "growth": {
                    "spotify": ((curr_data["spotify"] - prev_data["spotify"]) / prev_data["spotify"] * 100) if prev_data["spotify"] > 0 else 0,
                    "apple": ((curr_data["apple"] - prev_data["apple"]) / prev_data["apple"] * 100) if prev_data["apple"] > 0 else 0,
                    "total": ((curr_data["total"] - prev_data["total"]) / prev_data["total"] * 100) if prev_data["total"] > 0 else 0
                }
            }
            growth_data.append(growth_record)
        
        return {
            "success": True,
            "data": growth_data[-12:],  # Last 12 periods
            "metadata": {
                "source": "tidy_daily_streams.csv",
                "period": period,
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/spotify-audience")
async def get_spotify_audience() -> Dict[str, Any]:
    """Get Spotify audience analytics.
    
    Returns:
        Dictionary with Spotify audience data
    """
    try:
        # Get latest Spotify audience file
        filename = loader.get_latest_file("spotify_audience_curated_*.csv")
        
        if not filename:
            return {
                "success": False,
                "error": "No Spotify audience data available"
            }
        
        data = loader.load_csv(filename)
        
        return {
            "success": True,
            "data": data,
            "metadata": {
                "source": filename,
                "last_updated": datetime.now().isoformat(),
                "description": "Spotify for Artists audience demographics"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))