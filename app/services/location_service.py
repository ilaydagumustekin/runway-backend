from math import asin, cos, radians, sin, sqrt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.neighborhood import Neighborhood
from app.schemas.location import (
    NearbyNeighborhoodResponse,
    NeighborhoodMarkerResponse,
    NeighborhoodMarkerWithScoreResponse,
    NearestNeighborhoodItem,
    NearestNeighborhoodResponse,
)
from app.services.myki_service import calculate_myki_from_environmental_data
from app.services.statistics_service import get_latest_environmental_record


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return round(earth_radius_km * c, 2)


def get_all_neighborhoods(db: Session) -> list[Neighborhood]:
    return list(db.scalars(select(Neighborhood)).all())


def find_nearest_neighborhood(
    db: Session, latitude: float, longitude: float
) -> NearestNeighborhoodResponse | None:
    neighborhoods = get_all_neighborhoods(db)
    if not neighborhoods:
        return None

    nearest = min(
        neighborhoods,
        key=lambda neighborhood: calculate_distance_km(
            latitude, longitude, neighborhood.latitude, neighborhood.longitude
        ),
    )
    distance_km = calculate_distance_km(latitude, longitude, nearest.latitude, nearest.longitude)

    return NearestNeighborhoodResponse(
        neighborhood=NearestNeighborhoodItem(
            id=nearest.id,
            name=nearest.name,
            city=nearest.city,
            district=nearest.district,
            latitude=nearest.latitude,
            longitude=nearest.longitude,
        ),
        distance_km=distance_km,
    )


def find_nearby_neighborhoods(
    db: Session, latitude: float, longitude: float, radius_km: float, limit: int
) -> list[NearbyNeighborhoodResponse]:
    neighborhoods = get_all_neighborhoods(db)

    items: list[NearbyNeighborhoodResponse] = []
    for neighborhood in neighborhoods:
        distance_km = calculate_distance_km(
            latitude, longitude, neighborhood.latitude, neighborhood.longitude
        )
        if distance_km <= radius_km:
            items.append(
                NearbyNeighborhoodResponse(
                    id=neighborhood.id,
                    name=neighborhood.name,
                    city=neighborhood.city,
                    district=neighborhood.district,
                    latitude=neighborhood.latitude,
                    longitude=neighborhood.longitude,
                    distance_km=distance_km,
                )
            )

    items.sort(key=lambda item: item.distance_km)
    return items[:limit]


def get_neighborhood_markers(db: Session) -> list[NeighborhoodMarkerResponse]:
    neighborhoods = get_all_neighborhoods(db)
    return [
        NeighborhoodMarkerResponse(
            id=neighborhood.id,
            name=neighborhood.name,
            city=neighborhood.city,
            district=neighborhood.district,
            latitude=neighborhood.latitude,
            longitude=neighborhood.longitude,
        )
        for neighborhood in neighborhoods
    ]


def get_neighborhood_markers_with_scores(db: Session) -> list[NeighborhoodMarkerWithScoreResponse]:
    neighborhoods = get_all_neighborhoods(db)
    items: list[NeighborhoodMarkerWithScoreResponse] = []

    for neighborhood in neighborhoods:
        latest_record = get_latest_environmental_record(db, neighborhood.id)
        myki_score = None
        myki_category = None

        if latest_record:
            myki_score, myki_category = calculate_myki_from_environmental_data(latest_record)

        items.append(
            NeighborhoodMarkerWithScoreResponse(
                id=neighborhood.id,
                name=neighborhood.name,
                city=neighborhood.city,
                district=neighborhood.district,
                latitude=neighborhood.latitude,
                longitude=neighborhood.longitude,
                myki_score=myki_score,
                myki_category=myki_category,
            )
        )

    return items
