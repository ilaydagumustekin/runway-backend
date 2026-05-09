import logging
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.neighborhood import Neighborhood
from app.models.environmental_data import EnvironmentalData
from app.services.validation.tuik_data_manager import get_reference_value
from app.services.validation.validation_engine import validate_metric

logger = logging.getLogger(__name__)

def validate_neighborhood_data(db: Session, neighborhood: Neighborhood) -> dict:
    """
    Mahallenin çevresel verilerini TÜİK referans verileriyle doğrular.
    """
    stmt = select(EnvironmentalData).where(
        EnvironmentalData.neighborhood_id == neighborhood.id
    ).order_by(EnvironmentalData.created_at.desc()).limit(1)
    
    env_data = db.scalars(stmt).first()
    
    if not env_data:
        return {
            "neighborhood_id": neighborhood.id,
            "error": "Cevresel veri bulunamadi."
        }
        
    # Varsayılan şehir ve ilçe
    city = neighborhood.city or "Isparta"
    district = neighborhood.district or "Merkez"
    
    # Referans değerleri al
    ref_aqi = get_reference_value(db, city, district, "avg_aqi")
    ref_green = get_reference_value(db, city, district, "green_area_ratio")
    ref_noise = get_reference_value(db, city, district, "noise_level_dba")
    
    # Karşılaştırma yap
    val_aqi = validate_metric("Hava Kalitesi (AQI)", env_data.aqi, ref_aqi, tolerance_percent=25.0)
    val_green = validate_metric("Yesil Alan Orani", env_data.green_area_ratio, ref_green, tolerance_percent=20.0)
    val_noise = validate_metric("Gürültü (dBA)", env_data.noise_level_dba, ref_noise, tolerance_percent=15.0)
    
    validations = [val_aqi, val_green, val_noise]
    
    # Genel doğruluk hesapla
    valid_count = sum(1 for v in validations if v["is_valid"])
    total_with_ref = sum(1 for v in validations if v["reference_value"] is not None)
    
    accuracy = (valid_count / total_with_ref * 100) if total_with_ref > 0 else None
    
    return {
        "neighborhood_id": neighborhood.id,
        "city": city,
        "district": district,
        "overall_accuracy": accuracy,
        "validations": validations
    }
