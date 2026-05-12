"""
Rota onerme servisi.

Hibrit mantik (B + E):
  1) A* algoritmasi cevresel olarak en iyi mahalle waypoint'lerini secer
     (dusuk AQI + yuksek yesil alan + dusuk gurultu -> dusuk maliyet).
  2) OpenRouteService Directions API ile bu waypoint'ler gercek yol agina
     snap edilir; mobil tarafta polyline duz cizgi yerine sokak takip eder.

ORS API key yoksa veya servis hata verirse waypoint listesi oldugu gibi
donulur (`routing_source='centroid'`, `snap_to_roads=false`). Mock veri
uretilmez.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.schemas.routes import Coordinate, RouteRecommendRequest, RouteRecommendResponse
from app.services.external.openrouteservice_client import (
    fetch_directions,
    get_ors_profile,
)
from app.services.route_optimizer import (
    find_best_route,
    get_environmental_cost,
    haversine_distance,
)

logger = logging.getLogger(__name__)

_SPEED_MAP: dict[str, float] = {
    "walking": 5.0,
    "walk": 5.0,
    "bicycle": 15.0,
    "bike": 15.0,
    "cycling": 15.0,
    "scooter": 20.0,
}

_CANONICAL: dict[str, str] = {
    "walk": "walking",
    "bike": "bicycle",
    "cycling": "bicycle",
}

# Iki ardisik waypoint arasi minimum mesafe (metre). Cok yakin noktalar
# birlestirilir; aksi halde ORS "no route found" verebilir.
_MIN_WAYPOINT_SPACING_KM = 0.025


def _normalize_mode(raw: str) -> str:
    return _CANONICAL.get(raw.lower(), raw.lower())


def _path_distance_km(path: list[Coordinate]) -> float:
    if len(path) < 2:
        return 0.0
    return sum(
        haversine_distance(
            path[i].latitude, path[i].longitude,
            path[i + 1].latitude, path[i + 1].longitude,
        )
        for i in range(len(path) - 1)
    )


def _duration_minutes(distance_km: float, speed_kmh: float) -> int:
    if speed_kmh <= 0:
        return 1
    return max(1, round(distance_km / speed_kmh * 60))


def _dedupe_close_points(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Cok yakin (<25m) ardisik noktalari sadeleştirir."""
    if not points:
        return points
    cleaned: list[tuple[float, float]] = [points[0]]
    for lat, lon in points[1:]:
        prev_lat, prev_lon = cleaned[-1]
        if haversine_distance(prev_lat, prev_lon, lat, lon) >= _MIN_WAYPOINT_SPACING_KM:
            cleaned.append((lat, lon))
    if len(cleaned) < 2 and len(points) >= 2:
        # Son nokta her zaman hedef olsun
        cleaned.append(points[-1])
    return cleaned


def recommend_route(db: Session, payload: RouteRecommendRequest) -> RouteRecommendResponse:
    mode = _normalize_mode(payload.transport_mode)
    speed_kmh = _SPEED_MAP.get(mode, 5.0)

    logger.info(
        "[ROUTE] start=(%.5f,%.5f) end=(%.5f,%.5f) mode=%s",
        payload.start.latitude, payload.start.longitude,
        payload.destination.latitude, payload.destination.longitude,
        mode,
    )

    # 1) A* ile cevresel waypoint'ler
    path_nodes = find_best_route(
        db=db,
        start_lat=payload.start.latitude,
        start_lon=payload.start.longitude,
        end_lat=payload.destination.latitude,
        end_lon=payload.destination.longitude,
        optimize_for="environment",
    )

    waypoints_latlon: list[tuple[float, float]] = [
        (payload.start.latitude, payload.start.longitude)
    ]
    environmental_score: float | None = None

    if path_nodes:
        for node in path_nodes:
            waypoints_latlon.append((node.latitude, node.longitude))
        costs = [get_environmental_cost(db, n) for n in path_nodes]
        environmental_score = round(
            sum(100.0 - c for c in costs) / len(costs), 2
        )
    waypoints_latlon.append(
        (payload.destination.latitude, payload.destination.longitude)
    )
    waypoints_latlon = _dedupe_close_points(waypoints_latlon)

    waypoint_coords = [
        Coordinate(latitude=lat, longitude=lon) for lat, lon in waypoints_latlon
    ]

    # 2) ORS ile yol agina snap
    profile = get_ors_profile(mode)
    ors_result = fetch_directions(waypoints_latlon, profile=profile)

    if ors_result and len(ors_result["path"]) >= 2:
        path_coords = [
            Coordinate(latitude=lat, longitude=lon)
            for lat, lon in ors_result["path"]
        ]
        distance_km = round(ors_result["distance_km"], 2)
        duration = max(1, round(ors_result["duration_min"]))
        snap_to_roads = True
        routing_source = "openrouteservice"
        logger.info(
            "[ROUTE] ORS basarili; %d nokta, %.2f km, %d dk",
            len(path_coords), distance_km, duration,
        )
    else:
        # ORS yok / hata -> waypoint'lerle dondur (duz cizgi olur, dürüst raporla)
        path_coords = waypoint_coords
        distance_km = round(_path_distance_km(path_coords), 2)
        duration = _duration_minutes(distance_km, speed_kmh)
        snap_to_roads = False
        routing_source = "centroid"
        logger.warning(
            "[ROUTE] ORS kullanilamadi; waypoint sayisi=%d, distance_km=%.2f",
            len(path_coords), distance_km,
        )

    route_name = (
        "Cevresel Optimize Rota" if path_nodes else "Dogrudan Rota"
    )

    return RouteRecommendResponse(
        route_name=route_name,
        estimated_duration_minutes=duration,
        environmental_score=environmental_score,
        path=path_coords,
        distance_km=distance_km,
        transport_mode=mode,
        speed_kmh=speed_kmh,
        snap_to_roads=snap_to_roads,
        waypoints=waypoint_coords,
        routing_source=routing_source,
    )
