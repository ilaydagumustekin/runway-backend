from datetime import datetime, timedelta
import logging

from app.services.ml.air_quality_model import predictor

logger = logging.getLogger(__name__)

def predict_air_quality_for_next_hours(neighborhood_id: int, hours: int = 24) -> dict:
    """
    Belirli bir mahalle için hava kalitesi tahminlerini döndürür.
    Makine öğrenmesi tabanlı modeli (Random Forest / Gradient Boosting) kullanır.
    """
    now = datetime.utcnow()
    points = []
    
    # Model için seed: current aqi
    current_aqi = 50.0 + (neighborhood_id * 5) % 100
    
    # Model eğitimi yoksa tetikle (sadece prototype amacli)
    if not predictor.is_trained:
        from app.database import SessionLocal
        from app.services.ml.model_trainer import train_model_from_db
        try:
            with SessionLocal() as db:
                train_model_from_db(db)
        except Exception as e:
            logger.warning(f"Failed to auto-train model: {e}")

    horizon_steps = list(range(6, min(max(hours, 24), 72) + 6, 6))
    predictions = predictor.predict(current_aqi=current_aqi, hours_ahead=horizon_steps)
    
    for h in horizon_steps:
        forecast_time = now + timedelta(hours=h)
        pred_val = predictions.get(h, current_aqi)
        
        points.append({
            "timestamp": forecast_time.isoformat(),
            "predicted_aqi": round(pred_val, 1),
            "predicted_pm25": round(pred_val * 0.3, 1),  # Rough estimation
        })
        
    return {
        "neighborhood_id": neighborhood_id,
        "horizon_hours": hours,
        "source": "ml-model-ensemble" if predictor.is_trained else "fallback-model",
        "forecast": points,
    }
