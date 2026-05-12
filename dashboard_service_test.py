from uuid import uuid4

from app.database import Base, SessionLocal, engine
from app.models.environmental_data import EnvironmentalData
from app.models.neighborhood import Neighborhood
from app.models.user import User
from app.services.auth_service import hash_password
from app.services.dashboard_service import build_dashboard_home


def test_dashboard_home_includes_open_meteo_weather(monkeypatch):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    def fake_weather(lat: float, lon: float) -> dict:
        return {
            "temperature": 21,
            "condition_text": "Az Bulutlu",
            "condition_key": "partly_cloudy",
            "hourly_forecast": [
                {"time": "Şimdi", "temperature": 21, "condition": "partly_cloudy"},
                {"time": "19:00", "temperature": 19, "condition": "cloudy"},
            ],
            "source": "open-meteo",
        }

    monkeypatch.setattr("app.services.dashboard_service.fetch_current_weather", fake_weather)
    monkeypatch.setattr(
        "app.services.dashboard_service.fetch_and_persist_air_quality",
        lambda neighborhood, db=None: {"neighborhood_id": neighborhood.id, "status": "skipped"},
    )

    try:
        user = User(
            full_name="Dashboard Test User",
            email=f"dashboard-{uuid4()}@example.com",
            hashed_password=hash_password("strongpass123"),
        )
        neighborhood = Neighborhood(
            name=f"Dashboard Test Neighborhood {uuid4()}",
            city="Isparta",
            district="Merkez",
            latitude=37.78,
            longitude=30.55,
        )
        db.add_all([user, neighborhood])
        db.flush()

        db.add(
            EnvironmentalData(
                neighborhood_id=neighborhood.id,
                pm25=12.0,
                pm10=22.0,
                no2=18.0,
                o3=31.0,
                aqi=56.0,
                green_area_ratio=47.5,
                noise_level_dba=58.0,
            )
        )
        db.commit()
        db.refresh(user)
        db.refresh(neighborhood)

        dashboard = build_dashboard_home(
            db,
            current_user=user,
            neighborhood_id=neighborhood.id,
            latitude=None,
            longitude=None,
        )

        assert dashboard is not None
        weather_card = next(item for item in dashboard.current_environment if item.key == "weather")
        assert weather_card.value == 21
        assert weather_card.status == "Az Bulutlu"
        assert weather_card.status_key == "partly_cloudy"
        assert [item.time for item in dashboard.hourly_weather] == ["Şimdi", "19:00"]
    finally:
        db.close()
