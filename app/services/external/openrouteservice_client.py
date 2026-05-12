"""
OpenRouteService Directions API istemcisi.

Verilen waypoint listesi (mahalle merkezleri vb.) icin gercek yol agina snap
edilmis yuruyus/bisiklet rotasi doner. API key yoksa veya servis cevap
vermezse None doner; cagriyan kod buna gore graceful degrade eder.
"""
from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.openrouteservice.org/v2/directions"

_PROFILE_MAP: dict[str, str] = {
    "walking": "foot-walking",
    "walk": "foot-walking",
    "bicycle": "cycling-regular",
    "bike": "cycling-regular",
    "cycling": "cycling-regular",
    "scooter": "cycling-regular",
}


def get_ors_profile(transport_mode: str) -> str:
    return _PROFILE_MAP.get(transport_mode.lower(), "foot-walking")


def fetch_directions(
    waypoints: list[tuple[float, float]],
    profile: str = "foot-walking",
    timeout_seconds: float = 15.0,
) -> dict | None:
    """
    waypoints: [(lat, lon), ...] sirasi onemli; en az 2 nokta gerekli.
    Donus: {"path": [(lat, lon), ...], "distance_km": float, "duration_min": float}
    Hata/key yok -> None.
    """
    api_key = settings.openrouteservice_api_key
    if not api_key:
        logger.warning("OPENROUTESERVICE_API_KEY tanimli degil; yol snap edilemiyor.")
        return None

    if len(waypoints) < 2:
        logger.warning("ORS icin en az 2 waypoint gerekli; alindi=%d", len(waypoints))
        return None

    coords_lonlat = [[lon, lat] for lat, lon in waypoints]
    url = f"{_BASE_URL}/{profile}/geojson"
    payload = {
        "coordinates": coords_lonlat,
        "instructions": False,
    }
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json, application/geo+json",
    }

    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=timeout_seconds)
    except httpx.HTTPError as exc:
        logger.warning("ORS istek hatasi: %s", exc)
        return None

    if resp.status_code != 200:
        logger.warning("ORS HTTP %s: %s", resp.status_code, resp.text[:200])
        return None

    try:
        data = resp.json()
        feature = data["features"][0]
        coords = feature["geometry"]["coordinates"]
        summary = feature["properties"]["summary"]
    except (KeyError, IndexError, ValueError) as exc:
        logger.warning("ORS yanit parse hatasi: %s", exc)
        return None

    path_latlon: list[tuple[float, float]] = [(c[1], c[0]) for c in coords]
    distance_m = float(summary.get("distance", 0.0))
    duration_s = float(summary.get("duration", 0.0))

    return {
        "path": path_latlon,
        "distance_km": distance_m / 1000.0,
        "duration_min": duration_s / 60.0,
    }
