from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.neighborhood import Neighborhood


def seed_neighborhoods_if_enabled(db: Session) -> None:
    seed_data = [
        {
            "name": "Çünür",
            "city": "Isparta",
            "district": "Merkez",
            "latitude": 37.7952,
            "longitude": 30.5485,
            "boundary_data": None,
        },
        {
            "name": "Bahçelievler",
            "city": "Isparta",
            "district": "Merkez",
            "latitude": 37.7678,
            "longitude": 30.5566,
            "boundary_data": None,
        },
        {
            "name": "Davraz",
            "city": "Isparta",
            "district": "Merkez",
            "latitude": 37.7845,
            "longitude": 30.5745,
            "boundary_data": None,
        },
        {
            "name": "Fatih",
            "city": "Isparta",
            "district": "Merkez",
            "latitude": 37.7725,
            "longitude": 30.5438,
            "boundary_data": None,
        },
        {
            "name": "Modernevler",
            "city": "Isparta",
            "district": "Merkez",
            "latitude": 37.7665,
            "longitude": 30.5508,
            "boundary_data": None,
        },
        {
            "name": "Anadolu",
            "city": "Isparta",
            "district": "Merkez",
            "latitude": 37.7834,
            "longitude": 30.5532,
            "boundary_data": None,
        },
    ]

    existing_rows = db.scalars(select(Neighborhood)).all()
    existing_by_key = {
        (row.city, row.district, row.name): row
        for row in existing_rows
    }

    to_insert: list[Neighborhood] = []
    should_commit = False

    for item in seed_data:
        key = (item["city"], item["district"], item["name"])
        existing = existing_by_key.get(key)
        if existing:
            if (
                existing.latitude != item["latitude"]
                or existing.longitude != item["longitude"]
                or existing.boundary_data != item["boundary_data"]
            ):
                existing.latitude = item["latitude"]
                existing.longitude = item["longitude"]
                existing.boundary_data = item["boundary_data"]
                should_commit = True
        else:
            to_insert.append(Neighborhood(**item))
            should_commit = True

    if to_insert:
        db.add_all(to_insert)

    if should_commit:
        db.commit()
