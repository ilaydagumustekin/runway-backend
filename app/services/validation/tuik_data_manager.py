import logging
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.tuik_reference_data import TuikReferenceData

logger = logging.getLogger(__name__)

def get_reference_value(db: Session, city: str, district: str, indicator: str, year: int = 2023) -> float | None:
    """
    TUIK referans tablosundan ilgili indikator değerini döndürür.
    Bulunamazsa None döner.
    """
    stmt = select(TuikReferenceData).where(
        TuikReferenceData.city == city,
        TuikReferenceData.district == district,
        TuikReferenceData.indicator_type == indicator,
        TuikReferenceData.year == year
    ).order_by(TuikReferenceData.created_at.desc()).limit(1)
    
    record = db.scalars(stmt).first()
    if record:
        return record.value
    return None

def import_mock_tuik_data(db: Session):
    """
    TUIK referans tablosuna mock veri ekler. (Gerçekte CSV veya CIP API'den alınmalı)
    """
    mock_data = [
        {"city": "Isparta", "district": "Merkez", "indicator_type": "green_area_ratio", "value": 35.0, "year": 2023},
        {"city": "Isparta", "district": "Merkez", "indicator_type": "avg_aqi", "value": 45.0, "year": 2023},
        {"city": "Isparta", "district": "Merkez", "indicator_type": "noise_level_dba", "value": 55.0, "year": 2023},
    ]
    
    for item in mock_data:
        # Check if exists
        existing = db.scalars(select(TuikReferenceData).where(
            TuikReferenceData.city == item["city"],
            TuikReferenceData.district == item["district"],
            TuikReferenceData.indicator_type == item["indicator_type"]
        )).first()
        
        if not existing:
            new_record = TuikReferenceData(
                city=item["city"],
                district=item["district"],
                indicator_type=item["indicator_type"],
                value=item["value"],
                year=item["year"]
            )
            db.add(new_record)
            
    db.commit()
    logger.info("Mock TUIK verileri import edildi.")
