"""
Model eğitim pipeline'ı.

Eğitim verisi: `environmental_data` tablosunda `aqi` dolu kayıtlar (OpenAQ fetch vb.).
Zaman serisi lag özellikleri için tüm ölçümler tek seri (`station_id="global"`) olarak
zaman sırasına göre birleştirilir.

Yetersiz veride mock üretilmez; status='insufficient_data' döner.
Ham AQI satırı eşiği `MIN_TRAINING_RECORDS` (varsayılan 40).
Eğitim başarılıysa modeller `saved_models/*.joblib` altına yazılır.
"""
import logging

from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.models.environmental_data import EnvironmentalData
from app.services.ml.air_quality_model import (
    _IMPORT_ERRORS,
    _MODEL_AVAILABLE,
    _XGB_AVAILABLE,
    predictor,
)

logger = logging.getLogger(__name__)

# Ham satır eşiği; lag/rolling sonrası yeterli satır kalsın (tek global seri).
MIN_TRAINING_RECORDS = 40


def train_model_from_db(db: Session) -> dict:
    if not _MODEL_AVAILABLE:
        return {
            "status": "error",
            "message": "ML libraries missing",
            "import_errors": _IMPORT_ERRORS,
            "hint": (
                "Core ML libs missing. Run: "
                "pip install scikit-learn==1.6.1 joblib pandas numpy==1.26.4 "
                "(and optionally xgboost). "
                "If running on Vercel/Lambda, verify they exist in deployed environment "
                "and that the server has been restarted after install."
            ),
        }

    rows = db.scalars(
        select(EnvironmentalData)
        .where(EnvironmentalData.aqi.isnot(None))
        .order_by(asc(EnvironmentalData.created_at))
    ).all()

    data = [
        {
            "station_id": "global",
            "measured_at": r.created_at,
            "aqi": float(r.aqi),
        }
        for r in rows
        if r.aqi is not None and r.created_at is not None
    ]

    if len(data) < MIN_TRAINING_RECORDS:
        logger.info(
            "Eğitim için yetersiz AQI kaydı (%d/%d).",
            len(data),
            MIN_TRAINING_RECORDS,
        )
        return {
            "status": "insufficient_data",
            "available_records": len(data),
            "required": MIN_TRAINING_RECORDS,
            "source": "environmental_data",
        }

    success = predictor.train(data, min_samples=MIN_TRAINING_RECORDS)

    if success:
        return {
            "status": "success",
            "metrics": predictor.metrics,
            "samples_used": len(data),
            "source": "environmental_data",
            "xgb_available": _XGB_AVAILABLE,
        }
    return {
        "status": "error",
        "message": "Failed to train model (feature matrix too small after preprocessing).",
        "available_records": len(data),
        "source": "environmental_data",
    }
