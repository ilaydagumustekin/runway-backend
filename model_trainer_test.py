"""Eğitim verisinin `environmental_data` kaynaklı olması ve eşik davranışı."""
from datetime import datetime, timedelta

import pytest

pytest.importorskip("sklearn")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.environmental_data import EnvironmentalData
from app.models.neighborhood import Neighborhood
from app.services.ml import air_quality_model as aq_mod
from app.services.ml.model_trainer import MIN_TRAINING_RECORDS, train_model_from_db


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_train_insufficient_environmental_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(aq_mod, "MODEL_DIR", str(tmp_path / "ml_saved"))
    db = _session()
    db.add(Neighborhood(id=1, name="A", city="C", district="D", latitude=1.0, longitude=2.0))
    for i in range(MIN_TRAINING_RECORDS - 1):
        db.add(
            EnvironmentalData(
                neighborhood_id=1,
                aqi=50.0 + i * 0.1,
                created_at=datetime(2024, 1, 1, tzinfo=None) + timedelta(hours=i),
            )
        )
    db.commit()

    result = train_model_from_db(db)
    assert result["status"] == "insufficient_data"
    assert result["source"] == "environmental_data"
    db.close()


def test_train_success_writes_joblib(tmp_path, monkeypatch):
    monkeypatch.setattr(aq_mod, "MODEL_DIR", str(tmp_path / "ml_saved"))
    db = _session()
    db.add(Neighborhood(id=1, name="A", city="C", district="D", latitude=1.0, longitude=2.0))
    for i in range(MIN_TRAINING_RECORDS + 10):
        db.add(
            EnvironmentalData(
                neighborhood_id=1,
                aqi=40.0 + (i % 20) * 2.5,
                created_at=datetime(2024, 1, 1, tzinfo=None) + timedelta(hours=i),
            )
        )
    db.commit()

    result = train_model_from_db(db)
    assert result["status"] == "success"
    assert "metrics" in result
    assert (tmp_path / "ml_saved" / "rf_model.joblib").is_file()
    db.close()
