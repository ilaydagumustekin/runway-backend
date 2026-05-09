"""
Model eğitim pipeline'ı.
Veritabanındaki ölçümleri alıp ML modelini eğitir ve kaydeder.
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.external_air_quality import ExternalAirQuality
from app.services.ml.air_quality_model import predictor, _MODEL_AVAILABLE

logger = logging.getLogger(__name__)

def train_model_from_db(db: Session) -> dict:
    if not _MODEL_AVAILABLE:
        return {"status": "error", "message": "ML libraries missing"}
        
    records = db.scalars(select(ExternalAirQuality)).all()
    
    if len(records) < 50:
        # Eğer gerçek veri yoksa mock veri uretip eğitelim
        import random
        from datetime import datetime, timedelta
        
        logger.info("Yetersiz gercek veri, mock egitim verisi uretiliyor.")
        now = datetime.utcnow()
        data = []
        base_aqi = 50.0
        for i in range(1000):
            t = now - timedelta(hours=i*6)
            base_aqi = max(10, min(300, base_aqi + random.uniform(-15, 15)))
            # Zamana bagli bir patern ekleyelim (gunduz daha yuksek)
            if 8 <= t.hour <= 18:
                base_aqi += 10
                
            data.append({
                "station_id": "mock_station",
                "measured_at": t,
                "aqi": base_aqi
            })
    else:
        data = [
            {
                "station_id": r.station_id or "default",
                "measured_at": r.measured_at,
                "aqi": r.aqi or 50.0
            }
            for r in records
        ]
        
    success = predictor.train(data)
    
    if success:
        return {"status": "success", "metrics": predictor.metrics}
    else:
        return {"status": "error", "message": "Failed to train model"}
