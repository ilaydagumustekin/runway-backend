import logging

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.environmental_data import EnvironmentalData
from app.models.neighborhood import Neighborhood
from app.services.external.google_maps_satellite import fetch_satellite_image
from app.services.vlm.green_area_detector import analyze_green_area

logger = logging.getLogger(__name__)


def _persist_green_area_ratio(
    db: Session, neighborhood_id: int, green_ratio: float
) -> int | None:
    """VLM çıktısını yeni bir EnvironmentalData satırı olarak kaydeder.

    Diğer metrikler için son bilinen ölçüm değerlerini kopyalar; yoksa 0 verir.
    """
    if not (0.0 <= green_ratio <= 100.0):
        logger.warning("Skip persist: invalid green_ratio=%s", green_ratio)
        return None

    last = db.scalars(
        select(EnvironmentalData)
        .where(EnvironmentalData.neighborhood_id == neighborhood_id)
        .order_by(desc(EnvironmentalData.created_at))
        .limit(1)
    ).first()

    record = EnvironmentalData(
        neighborhood_id=neighborhood_id,
        pm25=last.pm25 if last else None,
        pm10=last.pm10 if last else None,
        no2=last.no2 if last else None,
        o3=last.o3 if last else None,
        aqi=last.aqi if last else None,
        green_area_ratio=green_ratio,
        noise_level_dba=last.noise_level_dba if last else None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record.id


def analyze_neighborhood_green_area(
    neighborhood: Neighborhood, db: Session | None = None
) -> dict:
    """
    Mahalle koordinatlarına göre uydu görüntüsünü alır ve VLM ile yeşil alan analizi yapar.
    `db` verilirse VLM sonucu environmental_data tablosuna kaydedilir.
    """
    if not neighborhood.latitude or not neighborhood.longitude:
        return {
            "neighborhood_id": neighborhood.id,
            "status": "error",
            "message": "Neighborhood coordinates are missing."
        }

    image_bytes = fetch_satellite_image(neighborhood.latitude, neighborhood.longitude)
    if not image_bytes:
        return {
            "neighborhood_id": neighborhood.id,
            "status": "error",
            "message": "Uydu görüntüsü alınamadı (GOOGLE_MAPS_API_KEY eksik veya istek başarısız).",
        }

    analysis_result = analyze_green_area(image_bytes)
    if isinstance(analysis_result, dict) and analysis_result.get("error"):
        return {
            "neighborhood_id": neighborhood.id,
            "status": "error",
            "message": analysis_result.get("message", "VLM analizi başarısız."),
            "detail": analysis_result,
        }

    persisted_id: int | None = None
    if db is not None and isinstance(analysis_result, dict):
        green_value = analysis_result.get("green_percentage")
        if isinstance(green_value, (int, float)):
            try:
                persisted_id = _persist_green_area_ratio(
                    db, neighborhood.id, float(green_value)
                )
            except Exception as exc:
                logger.error("Failed to persist VLM result: %s", exc)
                db.rollback()

    response: dict = {
        "neighborhood_id": neighborhood.id,
        "status": "success",
        "analysis": analysis_result,
    }
    if persisted_id is not None:
        response["persisted_environmental_data_id"] = persisted_id
    return response
