from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.tuik_reference_data import TuikReferenceData
from app.models.user import User
from app.services.auth_service import hash_password


def test_admin_can_import_tuik_reference_data_from_csv():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    email = f"tuik-admin-{uuid4()}@example.com"
    password = "strongpass123"
    district = f"Merkez-{uuid4()}"
    indicator_type = f"avg_aqi_{uuid4()}"
    source_url = "https://data.tuik.gov.tr/example.csv"

    try:
        admin = User(
            full_name="TUIK Import Admin",
            email=email,
            hashed_password=hash_password(password),
            role="admin",
        )
        db.add(admin)
        db.commit()

        csv_body = (
            "city,district,indicator_type,value,year,source_url\n"
            f"Isparta,{district},{indicator_type},44.5,2024,{source_url}\n"
        )

        with TestClient(app) as client:
            login_response = client.post(
                "/auth/login-json",
                json={"email": email, "password": password},
            )
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]

            import_response = client.post(
                "/validation/admin/import-tuik",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("tuik.csv", csv_body, "text/csv")},
            )

        assert import_response.status_code == 200
        assert import_response.json()["imported_count"] == 1

        record = db.scalar(
            select(TuikReferenceData).where(
                TuikReferenceData.city == "Isparta",
                TuikReferenceData.district == district,
                TuikReferenceData.indicator_type == indicator_type,
                TuikReferenceData.year == 2024,
            )
        )
        assert record is not None
        assert record.value == 44.5
        assert record.source_url == source_url
    finally:
        db.close()
