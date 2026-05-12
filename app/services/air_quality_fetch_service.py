"""
OpenAQ üzerinden mahalleye yakın hava kalitesi ölçümlerini çekip
`environmental_data` tablosuna kaydeden servis.
"""
import logging

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.environmental_data import EnvironmentalData
from app.models.neighborhood import Neighborhood
from app.services.external.openaq_client import fetch_latest_measurements_by_coordinates

logger = logging.getLogger(__name__)


# Basit AQI yaklaşımı: PM2.5 mevcutsa US EPA breakpoint'larıyla yaklaşık değer
_PM25_BREAKPOINTS = [
    (0.0, 12.0, 0, 50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 500.4, 301, 500),
]


def _pm25_to_aqi(pm25: float) -> float:
    for c_lo, c_hi, i_lo, i_hi in _PM25_BREAKPOINTS:
        if c_lo <= pm25 <= c_hi:
            return round(
                (i_hi - i_lo) / (c_hi - c_lo) * (pm25 - c_lo) + i_lo, 1
            )
    return 500.0


def _persist_air_quality(
    db: Session,
    neighborhood_id: int,
    measurements: dict[str, float],
) -> int | None:
    last = db.scalars(
        select(EnvironmentalData)
        .where(EnvironmentalData.neighborhood_id == neighborhood_id)
        .order_by(desc(EnvironmentalData.created_at))
        .limit(1)
    ).first()

    def _pick(metric: str) -> float | None:
        if metric in measurements:
            return float(measurements[metric])
        if last is not None and getattr(last, metric, None) is not None:
            return float(getattr(last, metric))
        return None

    pm25 = _pick("pm25")
    pm10 = _pick("pm10")
    no2 = _pick("no2")
    o3 = _pick("o3")

    # OpenAQ doğrudan AQI vermez; PM2.5'ten hesaplıyoruz
    if pm25 is not None and pm25 > 0:
        aqi: float | None = _pm25_to_aqi(pm25)
    elif last is not None and last.aqi is not None:
        aqi = float(last.aqi)
    else:
        aqi = None

    record = EnvironmentalData(
        neighborhood_id=neighborhood_id,
        pm25=pm25,
        pm10=pm10,
        no2=no2,
        o3=o3,
        aqi=aqi,
        green_area_ratio=last.green_area_ratio if last else None,
        noise_level_dba=last.noise_level_dba if last else None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record.id


def fetch_and_persist_air_quality(
    neighborhood: Neighborhood, db: Session | None = None
) -> dict:
    """OpenAQ'dan ölçüm çekip DB'ye yazar. API key yoksa uyarı döner."""
    if not neighborhood.latitude or not neighborhood.longitude:
        return {
            "neighborhood_id": neighborhood.id,
            "status": "error",
            "message": "Neighborhood coordinates are missing.",
        }

    api_key = settings.openaq_api_key or None
    measurements = fetch_latest_measurements_by_coordinates(
        lat=neighborhood.latitude,
        lon=neighborhood.longitude,
        api_key=api_key,
    )

    if not measurements:
        return {
            "neighborhood_id": neighborhood.id,
            "status": "no_data",
            "message": "OpenAQ yakın bir istasyon bulamadı veya veri dönmedi.",
            "api_key_present": bool(api_key),
        }

    persisted_id: int | None = None
    aqi_computed: float | None = None
    if db is not None:
        try:
            persisted_id = _persist_air_quality(db, neighborhood.id, measurements)
            if persisted_id:
                last = db.get(EnvironmentalData, persisted_id)
                if last:
                    aqi_computed = last.aqi
        except Exception as exc:
            logger.error("Failed to persist OpenAQ result: %s", exc)
            db.rollback()

    response: dict = {
        "neighborhood_id": neighborhood.id,
        "status": "success",
        "measurements": measurements,
    }
    if aqi_computed is not None:
        response["computed_aqi"] = aqi_computed
    if persisted_id is not None:
        response["persisted_environmental_data_id"] = persisted_id
    return response
