import csv
from io import StringIO
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

def import_tuik_csv_data(db: Session, csv_content: bytes) -> dict[str, int]:
    """
    TUIK referans verilerini CSV'den import eder.

    Beklenen kolonlar: city,district,indicator_type,value,year
    Opsiyonel kolon: source_url
    """
    text = csv_content.decode("utf-8-sig")
    reader = csv.DictReader(StringIO(text))
    required_columns = {"city", "district", "indicator_type", "value", "year"}
    missing_columns = required_columns.difference(reader.fieldnames or [])
    if missing_columns:
        raise ValueError(f"Eksik CSV kolonlari: {', '.join(sorted(missing_columns))}")

    imported_count = 0
    updated_count = 0

    for row in reader:
        city = (row.get("city") or "").strip()
        district = (row.get("district") or "").strip()
        indicator_type = (row.get("indicator_type") or "").strip()
        if not city or not district or not indicator_type:
            continue

        value = float(row["value"])
        year = int(row["year"])
        source_url = (row.get("source_url") or "").strip() or None

        existing = db.scalars(
            select(TuikReferenceData).where(
                TuikReferenceData.city == city,
                TuikReferenceData.district == district,
                TuikReferenceData.indicator_type == indicator_type,
                TuikReferenceData.year == year,
            )
        ).first()

        if existing:
            existing.value = value
            existing.source_url = source_url
            updated_count += 1
        else:
            db.add(
                TuikReferenceData(
                    city=city,
                    district=district,
                    indicator_type=indicator_type,
                    value=value,
                    year=year,
                    source_url=source_url,
                )
            )
            imported_count += 1

    db.commit()
    logger.info("TUIK CSV import tamamlandi: %s yeni, %s guncel", imported_count, updated_count)
    return {"imported_count": imported_count, "updated_count": updated_count}
