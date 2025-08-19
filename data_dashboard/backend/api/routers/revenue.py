"""Revenue API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.services.revenue.revenue_calculator import RevenueCalculator

router = APIRouter()
calculator = RevenueCalculator()

@router.get("/platform")
async def get_revenue_by_platform() -> Dict[str, Any]:
    """Get revenue breakdown by platform.
    
    Returns:
        Dictionary with platform statistics and metadata for AI safety
    """
    try:
        data = calculator.get_revenue_by_platform()
        
        return {
            "success": True,
            "data": data,
            "metadata": {
                "source": "dk_bank_details.csv",
                "last_updated": datetime.now().isoformat(),
                "data_quality": "high",
                "limitations": [
                    "Only includes cleared payments from DistroKid",
                    "Does not include TooLost revenue data"
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/artist")
async def get_revenue_by_artist() -> Dict[str, Any]:
    """Get revenue breakdown by artist.
    
    Returns:
        Dictionary with artist statistics
    """
    try:
        data = calculator.get_revenue_by_artist()
        
        return {
            "success": True,
            "data": data,
            "metadata": {
                "source": "dk_bank_details.csv",
                "last_updated": datetime.now().isoformat(),
                "artists": list(data.keys()),
                "limitations": [
                    "Historical data back to 2019",
                    "May not include all revenue sources"
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/distributor")
async def get_revenue_by_distributor() -> Dict[str, Any]:
    """Get revenue breakdown by distributor.
    
    Returns:
        Dictionary with distributor statistics
    """
    try:
        data = calculator.get_revenue_by_distributor()
        
        return {
            "success": True,
            "data": data,
            "metadata": {
                "source": "tidy_daily_streams.csv",
                "calculation_method": "estimated based on stream counts and RPS rates",
                "last_updated": datetime.now().isoformat(),
                "limitations": [
                    "Revenue is estimated, not actual",
                    "Based on average RPS rates per platform"
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monthly")
async def get_monthly_revenue(
    include_expected: bool = Query(True, description="Include expected revenue calculations")
) -> Dict[str, Any]:
    """Get monthly revenue with expected vs actual tracking.
    
    Args:
        include_expected: Whether to include expected revenue calculations
        
    Returns:
        List of monthly revenue records
    """
    try:
        data = calculator.get_monthly_revenue(include_expected)
        
        return {
            "success": True,
            "data": data,
            "metadata": {
                "sources": ["dk_bank_details.csv", "tidy_daily_streams.csv"],
                "last_updated": datetime.now().isoformat(),
                "payment_delay_months": 2,
                "limitations": [
                    "Expected revenue based on stream counts",
                    "Actual revenue has 2-month reporting delay"
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/delays")
async def get_payment_delays() -> Dict[str, Any]:
    """Analyze payment delay patterns.
    
    Returns:
        Dictionary with delay statistics
    """
    try:
        data = calculator.get_payment_delays()
        
        return {
            "success": True,
            "data": data,
            "metadata": {
                "source": "dk_bank_details.csv",
                "last_updated": datetime.now().isoformat(),
                "description": "Analysis of reporting delays between sale month and payment date"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rps-rates")
async def get_rps_rates() -> Dict[str, Any]:
    """Get revenue per stream rates by platform.
    
    Returns:
        Dictionary with RPS rates
    """
    return {
        "success": True,
        "data": RevenueCalculator.RPS_RATES,
        "metadata": {
            "description": "Revenue per stream rates in USD",
            "source": "Analysis of dk_bank_details.csv",
            "last_updated": "2024-08-04"
        }
    }