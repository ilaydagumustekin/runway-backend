import logging

from sqlalchemy.orm import Session

from app.schemas.routes import Coordinate, RouteRecommendRequest, RouteRecommendResponse
from app.services.route_optimizer import find_best_route, get_environmental_cost, haversine_distance

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


def recommend_route(db: Session, payload: RouteRecommendRequest) -> RouteRecommendResponse:
    mode = _normalize_mode(payload.transport_mode)
    speed_kmh = _SPEED_MAP.get(mode, 5.0)

    logger.info(
        "[ROUTE_DEBUG] recommend start=(%.5f,%.5f) destination=(%.5f,%.5f) transport_mode=%s",
        payload.start.latitude, payload.start.longitude,
        payload.destination.latitude, payload.destination.longitude,
        mode,
    )

    path_nodes = find_best_route(
        db=db,
        start_lat=payload.start.latitude,
        start_lon=payload.start.longitude,
        end_lat=payload.destination.latitude,
        end_lon=payload.destination.longitude,
        optimize_for="environment",
    )

    if not path_nodes:
        mid_lat = (payload.start.latitude + payload.destination.latitude) / 2
        mid_lon = (payload.start.longitude + payload.destination.longitude) / 2
        direct_path = [
            payload.start,
            Coordinate(latitude=mid_lat, longitude=mid_lon),
            payload.destination,
        ]
        distance_km = round(_path_distance_km(direct_path), 2)
        duration = _duration_minutes(distance_km, speed_kmh)
        logger.info(
            "[ROUTE_DEBUG] distance_km=%.2f speed_kmh=%.1f duration_minutes=%d (direct fallback)",
            distance_km, speed_kmh, duration,
        )
        return RouteRecommendResponse(
            route_name="Doğrudan Rota",
            estimated_duration_minutes=duration,
            environmental_score=50.0,
            path=direct_path,
            distance_km=distance_km,
            transport_mode=mode,
            speed_kmh=speed_kmh,
        )

    path_coords = [Coordinate(latitude=n.latitude, longitude=n.longitude) for n in path_nodes]
    distance_km = round(_path_distance_km(path_coords), 2)
    duration = _duration_minutes(distance_km, speed_kmh)
    environmental_score = round(
        sum(100.0 - get_environmental_cost(db, node) for node in path_nodes) / len(path_nodes),
        2,
    )

    logger.info(
        "[ROUTE_DEBUG] distance_km=%.2f speed_kmh=%.1f duration_minutes=%d",
        distance_km, speed_kmh, duration,
    )

    return RouteRecommendResponse(
        route_name="A* Çevresel Optimize Rota",
        estimated_duration_minutes=duration,
        environmental_score=environmental_score,
        path=path_coords,
        distance_km=distance_km,
        transport_mode=mode,
        speed_kmh=speed_kmh,
    )
