"""KPI (Key Performance Indicators) API endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime

from backend.services.revenue.revenue_calculator import RevenueCalculator
from backend.data.csv_loader import CSVDataLoader

router = APIRouter()
calculator = RevenueCalculator()
loader = CSVDataLoader()

@router.get("/summary")
async def get_summary_kpis() -> Dict[str, Any]:
    """Get summary KPIs for dashboard.
    
    Returns:
        Dictionary with key performance indicators
    """
    try:
        kpis = calculator.get_summary_kpis()
        
        # Add social media KPIs
        tiktok_file = loader.get_latest_file("tiktok_analytics_curated_*.csv")
        if tiktok_file:
            tiktok_data = loader.load_csv(tiktok_file)
            if tiktok_data:
                latest_tiktok = tiktok_data[-1]
                kpis["tiktok"] = {
                    "video_views": latest_tiktok.get("video_views", 0),
                    "engagement_rate": latest_tiktok.get("engagement_rate", 0)
                }
        
        # Add marketing KPIs
        metaads_data = loader.load_csv("metaads_campaigns_daily.csv")
        if metaads_data:
            total_spend = sum(row.get("spend", 0) for row in metaads_data)
            total_impressions = sum(row.get("impressions", 0) for row in metaads_data)
            total_clicks = sum(row.get("clicks", 0) for row in metaads_data)
            kpis["marketing"] = {
                "total_ad_spend": total_spend,
                "total_impressions": total_impressions,
                "average_cpc": total_spend / total_clicks if total_clicks > 0 else 0,
                "total_clicks": total_clicks
            }
        
        return {
            "success": True,
            "data": kpis,
            "metadata": {
                "sources": [
                    "dk_bank_details.csv",
                    "tidy_daily_streams.csv",
                    "tiktok_analytics_curated_*.csv",
                    "metaads_campaigns_daily.csv"
                ],
                "last_updated": datetime.now().isoformat(),
                "refresh_interval_seconds": 300
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/realtime")
async def get_realtime_kpis() -> Dict[str, Any]:
    """Get real-time KPIs (simulated for now).
    
    Returns:
        Dictionary with real-time metrics
    """
    try:
        # Load latest data
        streaming_data = loader.load_csv("tidy_daily_streams.csv")
        
        if not streaming_data:
            return {
                "success": False,
                "error": "No streaming data available"
            }
        
        # Get today's data (or latest)
        latest = streaming_data[-1]
        yesterday = streaming_data[-2] if len(streaming_data) > 1 else latest
        
        # Calculate changes
        spotify_change = latest.get("spotify_streams", 0) - yesterday.get("spotify_streams", 0)
        apple_change = latest.get("apple_streams", 0) - yesterday.get("apple_streams", 0)
        
        return {
            "success": True,
            "data": {
                "current_day": {
                    "date": latest.get("date"),
                    "spotify_streams": latest.get("spotify_streams", 0),
                    "apple_streams": latest.get("apple_streams", 0),
                    "total_streams": latest.get("combined_streams", 0)
                },
                "daily_change": {
                    "spotify": spotify_change,
                    "apple": apple_change,
                    "total": spotify_change + apple_change,
                    "spotify_percent": (spotify_change / yesterday.get("spotify_streams", 1)) * 100 if yesterday.get("spotify_streams") else 0,
                    "apple_percent": (apple_change / yesterday.get("apple_streams", 1)) * 100 if yesterday.get("apple_streams") else 0
                }
            },
            "metadata": {
                "source": "tidy_daily_streams.csv",
                "last_updated": datetime.now().isoformat(),
                "is_realtime": False,
                "note": "Currently showing latest daily data"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/goals")
async def get_goal_tracking() -> Dict[str, Any]:
    """Track progress toward business goals.
    
    Returns:
        Dictionary with goal tracking metrics
    """
    try:
        # Define goals
        goals = {
            "monthly_revenue": {
                "target": 500.00,  # $500/month target
                "current": 0,
                "progress": 0,
                "status": "pending"
            },
            "monthly_streams": {
                "target": 200000,  # 200k streams/month
                "current": 0,
                "progress": 0,
                "status": "pending"
            },
            "spotify_followers": {
                "target": 10000,  # 10k followers
                "current": 0,
                "progress": 0,
                "status": "pending"
            }
        }
        
        # Calculate current month revenue
        monthly_data = calculator.get_monthly_revenue()
        current_month = datetime.now().strftime("%Y-%m")
        
        for month_record in monthly_data:
            if month_record["month"] == current_month:
                goals["monthly_revenue"]["current"] = month_record.get("actual_revenue", 0)
                goals["monthly_streams"]["current"] = month_record.get("total_streams", 0)
                break
        
        # Calculate progress
        for goal_name, goal_data in goals.items():
            if goal_data["target"] > 0:
                progress = (goal_data["current"] / goal_data["target"]) * 100
                goal_data["progress"] = min(progress, 100)  # Cap at 100%
                
                if progress >= 100:
                    goal_data["status"] = "achieved"
                elif progress >= 75:
                    goal_data["status"] = "on_track"
                elif progress >= 50:
                    goal_data["status"] = "behind"
                else:
                    goal_data["status"] = "at_risk"
        
        return {
            "success": True,
            "data": goals,
            "metadata": {
                "month": current_month,
                "last_updated": datetime.now().isoformat(),
                "note": "Goals are configurable and can be adjusted"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_kpi_alerts() -> Dict[str, Any]:
    """Get alerts for significant KPI changes.
    
    Returns:
        List of alerts
    """
    try:
        alerts = []
        
        # Check for revenue anomalies
        monthly_data = calculator.get_monthly_revenue()
        if monthly_data and len(monthly_data) > 1:
            latest = monthly_data[-1]
            previous = monthly_data[-2]
            
            revenue_change = latest["actual_revenue"] - previous["actual_revenue"]
            if abs(revenue_change) > 100:  # Significant change
                alerts.append({
                    "type": "revenue",
                    "severity": "high" if revenue_change < 0 else "info",
                    "message": f"Revenue {'decreased' if revenue_change < 0 else 'increased'} by ${abs(revenue_change):.2f}",
                    "timestamp": datetime.now().isoformat()
                })
        
        # Check for streaming drops
        streaming_data = loader.load_csv("tidy_daily_streams.csv")
        if streaming_data and len(streaming_data) > 7:
            recent_avg = sum(row.get("combined_streams", 0) for row in streaming_data[-7:]) / 7
            previous_avg = sum(row.get("combined_streams", 0) for row in streaming_data[-14:-7]) / 7
            
            if previous_avg > 0:
                change_percent = ((recent_avg - previous_avg) / previous_avg) * 100
                if change_percent < -20:  # 20% drop
                    alerts.append({
                        "type": "streaming",
                        "severity": "warning",
                        "message": f"Weekly streaming average dropped by {abs(change_percent):.1f}%",
                        "timestamp": datetime.now().isoformat()
                    })
        
        return {
            "success": True,
            "data": alerts,
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "alert_count": len(alerts)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))