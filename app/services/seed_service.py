from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.neighborhood import Neighborhood


def seed_neighborhoods_if_enabled(db: Session) -> None:
    seed_data = [
        {
            "name": "Çünür",
            "city": "Isparta",
            "district": "Merkez",
            "latitude": 37.7897,
            "longitude": 30.5609,
            "boundary_data": None,
        },
        {
            "name": "Bahçelievler",
            "city": "Isparta",
            "district": "Merkez",
            "latitude": 37.7705,
            "longitude": 30.5519,
            "boundary_data": None,
        },
        {
            "name": "Davraz",
            "city": "Isparta",
            "district": "Merkez",
            "latitude": 37.7813,
            "longitude": 30.5376,
            "boundary_data": None,
        },
        {
            "name": "Fatih",
            "city": "Isparta",
            "district": "Merkez",
            "latitude": 37.7644,
            "longitude": 30.5444,
            "boundary_data": None,
        },
        {
            "name": "Modernevler",
            "city": "Isparta",
            "district": "Merkez",
            "latitude": 37.7722,
            "longitude": 30.5586,
            "boundary_data": None,
        },
    ]

    existing = set(
        db.execute(select(Neighborhood.city, Neighborhood.district, Neighborhood.name)).all()
    )
    to_insert = [
        Neighborhood(**item)
        for item in seed_data
        if (item["city"], item["district"], item["name"]) not in existing
    ]

    if to_insert:
        db.add_all(to_insert)
        db.commit()
