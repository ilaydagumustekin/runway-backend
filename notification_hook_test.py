from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.neighborhood import Neighborhood
from app.models.notification import Notification


def test_environmental_data_create_generates_air_quality_notification():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        neighborhood = Neighborhood(
            name=f"Notification Test Neighborhood {uuid4()}",
            city="Isparta",
            district="Merkez",
            latitude=37.78,
            longitude=30.55,
        )
        db.add(neighborhood)
        db.commit()
        db.refresh(neighborhood)

        with TestClient(app) as client:
            response = client.post(
                "/environmental-data",
                json={
                    "neighborhood_id": neighborhood.id,
                    "pm25": 45.0,
                    "pm10": 70.0,
                    "no2": 30.0,
                    "o3": 20.0,
                    "aqi": 155.0,
                    "green_area_ratio": 20.0,
                    "noise_level_dba": 65.0,
                },
            )

        assert response.status_code == 201

        notification = db.scalar(
            select(Notification).where(
                Notification.neighborhood_id == neighborhood.id,
                Notification.notification_type == "air_quality",
            )
        )
        assert notification is not None
        assert notification.user_id is None
        assert notification.severity == "high"
        assert notification.is_read is False
    finally:
        db.close()
