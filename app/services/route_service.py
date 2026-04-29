from app.schemas.routes import Coordinate, RouteRecommendRequest, RouteRecommendResponse


def recommend_route(payload: RouteRecommendRequest) -> RouteRecommendResponse:
    mid_lat = (payload.start.latitude + payload.destination.latitude) / 2
    mid_lon = (payload.start.longitude + payload.destination.longitude) / 2

    return RouteRecommendResponse(
        route_name="Daha Temiz ve Sessiz Yaya Rotasi (Mock)",
        estimated_duration_minutes=18,
        environmental_score=78.5,
        path=[
            payload.start,
            Coordinate(latitude=mid_lat, longitude=mid_lon),
            payload.destination,
        ],
    )
