"""
OpenAQ API v3 client.
Provides air quality data by coordinates.
"""
import logging
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OPENAQ_BASE_URL = "https://api.openaq.org/v3"

def fetch_latest_measurements_by_coordinates(
    lat: float, lon: float, radius_meters: int = 5000, api_key: str | None = None
) -> dict[str, float]:
    """
    Fetches the latest air quality measurements for a given location.
    Returns a dictionary with parameters like pm25, pm10, no2, o3, aqi.
    """
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    # Find locations within radius
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f"{OPENAQ_BASE_URL}/locations",
                params={
                    "coordinates": f"{lat},{lon}",
                    "radius": radius_meters,
                    "limit": 1
                },
                headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
            
            if not data.get("results"):
                return {}
                
            location_id = data["results"][0]["id"]
            sensors = data["results"][0].get("sensors", [])
            sensor_map = {}
            for s in sensors:
                sensor_id = s.get("id")
                param_name = s.get("parameter", {}).get("name")
                if sensor_id and param_name:
                    sensor_map[sensor_id] = param_name.lower()
            
            # Fetch latest measurements for this location
            meas_resp = client.get(
                f"{OPENAQ_BASE_URL}/locations/{location_id}/latest",
                headers=headers
            )
            meas_resp.raise_for_status()
            meas_data = meas_resp.json()
            
            if not meas_data.get("results"):
                return {}
                
            results: dict[str, float] = {}
            for item in meas_data["results"]:
                sid = item.get("sensorsId")
                val = item.get("value")
                if sid in sensor_map and val is not None:
                    results[sensor_map[sid]] = float(val)
                    
            return results
    except Exception as e:
        logger.error(f"Error fetching from OpenAQ: {e}")
        return {}
