#!/usr/bin/env python3
"""Test script for BEDROT Data Dashboard API."""
import sys
import asyncio
import httpx
from typing import Dict, Any
from loguru import logger

# API base URL
BASE_URL = "http://localhost:8000"

async def test_endpoint(client: httpx.AsyncClient, method: str, path: str, **kwargs) -> Dict[str, Any]:
    """Test a single API endpoint."""
    try:
        response = await client.request(method, f"{BASE_URL}{path}", **kwargs)
        response.raise_for_status()
        return {
            "path": path,
            "status": "success",
            "status_code": response.status_code,
            "data": response.json()
        }
    except Exception as e:
        return {
            "path": path,
            "status": "error",
            "error": str(e)
        }

async def run_tests():
    """Run all API tests."""
    logger.info("Starting API tests...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test endpoints
        endpoints = [
            ("GET", "/"),
            ("GET", "/health"),
            ("GET", "/api/kpis/summary"),
            ("GET", "/api/revenue/platform"),
            ("GET", "/api/revenue/artist"),
            ("GET", "/api/revenue/distributor"),
            ("GET", "/api/revenue/monthly"),
            ("GET", "/api/revenue/delays"),
            ("GET", "/api/streaming/summary"),
            ("GET", "/api/streaming/daily?days=7"),
            ("GET", "/api/data/files"),
            ("GET", "/api/data/schema"),
        ]
        
        results = []
        for method, path in endpoints:
            logger.info(f"Testing {method} {path}")
            result = await test_endpoint(client, method, path)
            results.append(result)
            
            if result["status"] == "success":
                logger.success(f"✓ {path} - {result['status_code']}")
            else:
                logger.error(f"✗ {path} - {result.get('error', 'Unknown error')}")
        
        # Summary
        success_count = sum(1 for r in results if r["status"] == "success")
        total_count = len(results)
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Test Results: {success_count}/{total_count} passed")
        
        if success_count == total_count:
            logger.success("All tests passed!")
        else:
            logger.warning(f"{total_count - success_count} tests failed")
            
        # Show sample data from key endpoints
        logger.info(f"\n{'='*50}")
        logger.info("Sample Data from Key Endpoints:")
        
        for result in results:
            if result["status"] == "success" and result["path"] in ["/api/kpis/summary", "/api/revenue/distributor"]:
                logger.info(f"\n{result['path']}:")
                data = result.get("data", {})
                if isinstance(data, dict) and "data" in data:
                    # Show first few items
                    if isinstance(data["data"], dict):
                        for key, value in list(data["data"].items())[:3]:
                            logger.info(f"  {key}: {value}")
                    elif isinstance(data["data"], list) and data["data"]:
                        logger.info(f"  First item: {data['data'][0]}")

if __name__ == "__main__":
    logger.info("BEDROT Data Dashboard API Test Suite")
    logger.info(f"Testing API at: {BASE_URL}")
    
    try:
        asyncio.run(run_tests())
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        sys.exit(1)