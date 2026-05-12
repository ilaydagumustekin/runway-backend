"""
Model eğitim pipeline'ı.
Yalnızca gerçek `external_air_quality` ölçümlerinden eğitir.
Yetersiz veriyse mock üretmez; status='insufficient_data' döner.
"""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.external_air_quality import ExternalAirQuality
from app.services.ml.air_quality_model import _MODEL_AVAILABLE, predictor

logger = logging.getLogger(__name__)

MIN_TRAINING_RECORDS = 50


def train_model_from_db(db: Session) -> dict:
    if not _MODEL_AVAILABLE:
        return {"status": "error", "message": "ML libraries missing"}

    records = db.scalars(select(ExternalAirQuality)).all()

    if len(records) < MIN_TRAINING_RECORDS:
        logger.info(
            "Eğitim için yetersiz gerçek veri (%d/%d).",
            len(records), MIN_TRAINING_RECORDS,
        )
        return {
            "status": "insufficient_data",
            "available_records": len(records),
            "required": MIN_TRAINING_RECORDS,
        }

    data = [
        {
            "station_id": r.station_id or "unknown",
            "measured_at": r.measured_at,
            "aqi": r.aqi,
        }
        for r in records
        if r.aqi is not None and r.measured_at is not None
    ]

    if len(data) < MIN_TRAINING_RECORDS:
        return {
            "status": "insufficient_data",
            "available_records": len(data),
            "required": MIN_TRAINING_RECORDS,
        }

    success = predictor.train(data)

    if success:
        return {"status": "success", "metrics": predictor.metrics}
    return {"status": "error", "message": "Failed to train model"}
