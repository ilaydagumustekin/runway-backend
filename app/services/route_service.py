from sqlalchemy.orm import Session
from app.schemas.routes import Coordinate, RouteRecommendRequest, RouteRecommendResponse
from app.services.route_optimizer import find_best_route

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
        # Fallback to direct mock route
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

    # Convert nodes to coordinates
    path_coords = [Coordinate(latitude=n.latitude, longitude=n.longitude) for n in path_nodes]
    
    # Hesaplanan rota süresi ve skoru (basit tahmin)
    # Her mahalle arasi yaklasik 1.5 km varsayalim, yaya 5 km/h hiziyla.
    total_minutes = len(path_coords) * 15 
    
    return RouteRecommendResponse(
        route_name="A* Çevresel Optimize Rota",
        estimated_duration_minutes=total_minutes,
        environmental_score=85.0, # Ortalama MYKI alinabilir
        path=path_coords,
    )
