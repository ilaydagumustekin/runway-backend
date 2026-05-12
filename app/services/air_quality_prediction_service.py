from datetime import datetime, timedelta
import logging

from fastapi import HTTPException
from sqlalchemy import desc, select

from app.database import SessionLocal
from app.models.environmental_data import EnvironmentalData
from app.services.ml.air_quality_model import predictor

logger = logging.getLogger(__name__)


def _get_latest_aqi(neighborhood_id: int) -> float:
    """En son `environmental_data` ölçümünden AQI değerini döner.

    Ölçüm yoksa `HTTPException(422)` fırlatır; mock değer döndürmez.
    """
    with SessionLocal() as db:
        latest = db.scalars(
            select(EnvironmentalData)
            .where(EnvironmentalData.neighborhood_id == neighborhood_id)
            .order_by(desc(EnvironmentalData.created_at))
            .limit(1)
        ).first()
        if latest is None or latest.aqi is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "no_measurement",
                    "message": (
                        "Bu mahalle için ölçüm bulunmuyor. Önce "
                        "/integrations/air-quality-fetch/{id} endpoint'ini çağırın."
                    ),
                    "neighborhood_id": neighborhood_id,
                },
            )
        return float(latest.aqi)


def predict_air_quality_for_next_hours(neighborhood_id: int, hours: int = 24) -> dict:
    """
    Belirli bir mahalle için hava kalitesi tahminlerini döndürür.
    Eğitilmiş ML modelini (Random Forest / Gradient Boosting / XGBoost ensemble) kullanır.
    Başlangıç değeri DB'deki son ölçümdür; ölçüm yoksa 422 döner.
    """
    now = datetime.utcnow()
    points: list[dict] = []

    current_aqi = _get_latest_aqi(neighborhood_id)

    # Model eğitilmemişse eğitmeyi dene (yeterli veri varsa eğitir)
    if not predictor.is_trained:
        from app.services.ml.model_trainer import train_model_from_db
        try:
            with SessionLocal() as db:
                train_result = train_model_from_db(db)
                logger.info("Auto-train result: %s", train_result)
        except Exception as e:
            logger.warning(f"Failed to auto-train model: {e}")

    if not predictor.is_trained:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "model_not_trained",
                "message": (
                    "ML modeli henüz eğitilmedi (yeterli external_air_quality "
                    "kaydı yok). Önce /admin/ml/train veya cron ile veri biriktirin."
                ),
            },
        )

    horizon_steps = list(range(6, min(max(hours, 24), 72) + 6, 6))
    predictions = predictor.predict(current_aqi=current_aqi, hours_ahead=horizon_steps)

    for h in horizon_steps:
        forecast_time = now + timedelta(hours=h)
        pred_val = predictions.get(h, current_aqi)
        points.append({
            "timestamp": forecast_time.isoformat(),
            "predicted_aqi": round(pred_val, 1),
            "predicted_pm25": round(pred_val * 0.3, 1),
        })

    return {
        "neighborhood_id": neighborhood_id,
        "horizon_hours": hours,
        "current_aqi": round(current_aqi, 1),
        "current_aqi_source": "measured",
        "source": "ml-model-ensemble",
        "forecast": points,
    }
