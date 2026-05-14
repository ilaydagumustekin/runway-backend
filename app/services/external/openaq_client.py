"""
OpenAQ API v3 client.
Provides air quality data by coordinates.
"""
import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OPENAQ_BASE_URL = "https://api.openaq.org/v3"
_MAX_RETRIES = 5


def _request_json(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resp: httpx.Response | None = None
    for attempt in range(_MAX_RETRIES):
        resp = client.request(method, url, headers=headers, params=params)
        if resp.status_code == 429:
            wait = min(60.0, float(resp.headers.get("Retry-After", 2 * (attempt + 1))))
            logger.warning("OpenAQ 429, %.1fs bekleniyor (deneme %d/%d)", wait, attempt + 1, _MAX_RETRIES)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    if resp is not None:
        resp.raise_for_status()
    raise RuntimeError("OpenAQ isteği başarısız")


def fetch_latest_measurements_by_coordinates(
    lat: float, lon: float, radius_meters: int = 5000, api_key: str | None = None
) -> dict[str, float]:
    """
    Fetches the latest air quality measurements for a given location.
    Returns a dictionary with parameters like pm25, pm10, no2, o3, aqi.
    """
    headers: dict[str, str] = {}
    if api_key:
        headers["X-API-Key"] = api_key

    # Find locations within radius
    try:
        with httpx.Client(timeout=15.0) as client:
            data = _request_json(
                client,
                "GET",
                f"{OPENAQ_BASE_URL}/locations",
                headers=headers,
                params={
                    "coordinates": f"{lat},{lon}",
                    "radius": radius_meters,
                    "limit": 1,
                },
            )

            if not data.get("results"):
                return {}

            location_id = data["results"][0]["id"]
            sensors = data["results"][0].get("sensors", [])
            sensor_map: dict[int, str] = {}
            for s in sensors:
                sensor_id = s.get("id")
                param_name = s.get("parameter", {}).get("name")
                if sensor_id and param_name:
                    sensor_map[sensor_id] = param_name.lower()

            meas_data = _request_json(
                client,
                "GET",
                f"{OPENAQ_BASE_URL}/locations/{location_id}/latest",
                headers=headers,
            )

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
        logger.error("Error fetching from OpenAQ: %s", e)
        return {}
