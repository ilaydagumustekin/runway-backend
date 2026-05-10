from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.environmental_data import EnvironmentalData
from app.models.neighborhood import Neighborhood
from app.models.user import User
from app.services.auth_service import hash_password


def test_vlm_batch_analyze_persists_green_area_ratio(monkeypatch):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    email = f"vlm-admin-{uuid4()}@example.com"
    password = "strongpass123"

    def fake_analysis(neighborhood: Neighborhood) -> dict:
        return {
            "neighborhood_id": neighborhood.id,
            "status": "success",
            "analysis": {
                "green_percentage": 42.5,
                "confidence": 0.9,
                "detected_areas": ["parks"],
            },
        }

    monkeypatch.setattr("app.routes.vlm_analysis.analyze_neighborhood_green_area", fake_analysis)

    try:
        admin = User(
            full_name="VLM Admin",
            email=email,
            hashed_password=hash_password(password),
            role="admin",
        )
        neighborhood = Neighborhood(
            name=f"VLM Test Neighborhood {uuid4()}",
            city="Isparta",
            district="Merkez",
            latitude=37.78,
            longitude=30.55,
        )
        db.add_all([admin, neighborhood])
        db.flush()
        db.add(
            EnvironmentalData(
                neighborhood_id=neighborhood.id,
                pm25=10.0,
                pm10=20.0,
                no2=15.0,
                o3=25.0,
                aqi=50.0,
                green_area_ratio=10.0,
                noise_level_dba=55.0,
            )
        )
        db.commit()

        with TestClient(app) as client:
            login_response = client.post(
                "/auth/login-json",
                json={"email": email, "password": password},
            )
            assert login_response.status_code == 200

            token = login_response.json()["access_token"]
            response = client.post(
                f"/admin/vlm/batch-analyze?neighborhood_id={neighborhood.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        assert response.json()["persisted_count"] == 1

        record = db.scalar(
            select(EnvironmentalData).where(EnvironmentalData.neighborhood_id == neighborhood.id)
        )
        assert record is not None
        db.refresh(record)
        assert record.green_area_ratio == 42.5
    finally:
        db.close()
