from sqlalchemy.orm import Session
from app.schemas.routes import Coordinate, RouteRecommendRequest, RouteRecommendResponse
from app.services.route_optimizer import find_best_route, get_environmental_cost, haversine_distance


def _estimate_walking_minutes(path: list[Coordinate]) -> int:
    if len(path) < 2:
        return 1

    total_km = sum(
        haversine_distance(
            path[index].latitude,
            path[index].longitude,
            path[index + 1].latitude,
            path[index + 1].longitude,
        )
        for index in range(len(path) - 1)
    )
    return max(1, round(total_km / 5.0 * 60))


def recommend_route(db: Session, payload: RouteRecommendRequest) -> RouteRecommendResponse:
    """
    Kullanıcının başlangıç ve bitiş koordinatları arasında A* algoritması ile
    çevresel olarak en optimize rotayı bulur.
    """
    path_nodes = find_best_route(
        db=db,
        start_lat=payload.start.latitude,
        start_lon=payload.start.longitude,
        end_lat=payload.destination.latitude,
        end_lon=payload.destination.longitude,
        optimize_for="environment"
    )
    
    if not path_nodes:
        mid_lat = (payload.start.latitude + payload.destination.latitude) / 2
        mid_lon = (payload.start.longitude + payload.destination.longitude) / 2
        direct_path = [
            payload.start,
            Coordinate(latitude=mid_lat, longitude=mid_lon),
            payload.destination,
        ]
        return RouteRecommendResponse(
            route_name="Doğrudan Yaya Rotası",
            estimated_duration_minutes=_estimate_walking_minutes(direct_path),
            environmental_score=50.0,
            path=direct_path,
        )

    # Convert nodes to coordinates
    path_coords = [Coordinate(latitude=n.latitude, longitude=n.longitude) for n in path_nodes]
    environmental_score = round(
        sum(100.0 - get_environmental_cost(db, node) for node in path_nodes) / len(path_nodes),
        2,
    )
    
    return RouteRecommendResponse(
        route_name="A* Çevresel Optimize Rota",
        estimated_duration_minutes=_estimate_walking_minutes(path_coords),
        environmental_score=environmental_score,
        path=path_coords,
    )
