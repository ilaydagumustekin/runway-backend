from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.models.environmental_data import EnvironmentalData
from app.models.neighborhood import Neighborhood
from app.schemas.data_sources import DataSourceResponse
from app.schemas.statistics import (
    NeighborhoodChartDataResponse,
    NeighborhoodHistoryItem,
    NeighborhoodSummaryResponse,
)
from app.services.myki_service import calculate_myki_from_environmental_data


DATA_SOURCES: list[DataSourceResponse] = [
    DataSourceResponse(
        slug="openaq",
        name="OpenAQ",
        type="air_quality",
        description="Acik hava kalitesi verileri icin kullanilabilecek toplu veri kaynagi.",
        status="planned",
        usage_area="Hava kalitesi verileri",
    ),
    DataSourceResponse(
        slug="waqi",
        name="WAQI",
        type="air_quality",
        description="Dunya capinda hava kalitesi endeksi ve istasyon verileri sunar.",
        status="planned",
        usage_area="Hava kalitesi verileri",
    ),
    DataSourceResponse(
        slug="airnow",
        name="AirNow",
        type="air_quality",
        description="Ozellikle hava kalitesi ve AQI odakli resmi veri saglayicisi.",
        status="planned",
        usage_area="Hava kalitesi verileri",
    ),
    DataSourceResponse(
        slug="mobile-sensor",
        name="Mobil cihaz mikrofon sensoru",
        type="noise",
        description="Mobil cihaz mikrofonu uzerinden kullanici tabanli gurultu olcumleri saglar.",
        status="active",
        usage_area="Gurultu olcumleri",
    ),
    DataSourceResponse(
        slug="google-maps-satellite",
        name="Google Maps Satellite API",
        type="green_area",
        description="Uydu goruntuleri uzerinden yesil alan analizi icin kullanilabilir.",
        status="planned",
        usage_area="Yesil alan analizi",
    ),
    DataSourceResponse(
        slug="vlm",
        name="VLM",
        type="green_area",
        description="Gorsel dil modelleri ile uydu veya sokak goruntulerinden yesil alan cikarimi yapabilir.",
        status="planned",
        usage_area="Yesil alan analizi",
    ),
    DataSourceResponse(
        slug="tuik-cip",
        name="TUIK Cevresel Gostergeler Bilgi Portali",
        type="validation",
        description="Resmi dogrulama ve karsilastirma amacli cevresel gosterge verileri sunar.",
        status="planned",
        usage_area="Resmi dogrulama verileri",
    ),
    DataSourceResponse(
        slug="user-contributed",
        name="Kullanici katkili olcumler",
        type="community",
        description="Mobil uygulama uzerinden gelen kullanici kaynakli cevresel olcumlerdir.",
        status="active",
        usage_area="Mobil uygulama uzerinden gelen cevresel olcumler",
    ),
]


def get_neighborhood_or_none(db: Session, neighborhood_id: int) -> Neighborhood | None:
    return db.get(Neighborhood, neighborhood_id)


def get_latest_environmental_record(db: Session, neighborhood_id: int) -> EnvironmentalData | None:
    return db.scalar(
        select(EnvironmentalData)
        .where(EnvironmentalData.neighborhood_id == neighborhood_id)
        .order_by(desc(EnvironmentalData.created_at))
    )


def build_neighborhood_summary(db: Session, neighborhood_id: int) -> NeighborhoodSummaryResponse | None:
    neighborhood = get_neighborhood_or_none(db, neighborhood_id)
    if not neighborhood:
        return None

    latest_record = get_latest_environmental_record(db, neighborhood_id)
    if not latest_record:
        return None

    myki_score, myki_category = calculate_myki_from_environmental_data(latest_record)
    return NeighborhoodSummaryResponse(
        neighborhood_id=neighborhood.id,
        neighborhood_name=neighborhood.name,
        city=neighborhood.city,
        district=neighborhood.district,
        latest_aqi=latest_record.aqi,
        latest_pm25=latest_record.pm25,
        latest_pm10=latest_record.pm10,
        latest_noise_level_dba=latest_record.noise_level_dba,
        latest_green_area_ratio=latest_record.green_area_ratio,
        myki_score=myki_score,
        myki_category=myki_category,
        updated_at=latest_record.created_at,
    )


def get_neighborhood_history(
    db: Session, neighborhood_id: int, limit: int
) -> list[NeighborhoodHistoryItem]:
    records = db.scalars(
        select(EnvironmentalData)
        .where(EnvironmentalData.neighborhood_id == neighborhood_id)
        .order_by(asc(EnvironmentalData.created_at))
        .limit(limit)
    ).all()
    return [
        NeighborhoodHistoryItem(
            created_at=record.created_at,
            aqi=record.aqi,
            pm25=record.pm25,
            pm10=record.pm10,
            noise_level_dba=record.noise_level_dba,
            green_area_ratio=record.green_area_ratio,
        )
        for record in records
    ]


def build_neighborhood_chart_data(
    db: Session, neighborhood_id: int, limit: int
) -> NeighborhoodChartDataResponse:
    records = db.scalars(
        select(EnvironmentalData)
        .where(EnvironmentalData.neighborhood_id == neighborhood_id)
        .order_by(asc(EnvironmentalData.created_at))
        .limit(limit)
    ).all()

    labels: list[str] = []
    aqi_values: list[float | None] = []
    noise_values: list[float | None] = []
    green_area_values: list[float | None] = []
    myki_values: list[float | None] = []

    for record in records:
        myki_score, _ = calculate_myki_from_environmental_data(record)
        labels.append(record.created_at.date().isoformat())
        aqi_values.append(record.aqi)
        noise_values.append(record.noise_level_dba)
        green_area_values.append(record.green_area_ratio)
        myki_values.append(myki_score)

    return NeighborhoodChartDataResponse(
        neighborhood_id=neighborhood_id,
        labels=labels,
        aqi=aqi_values,
        noise_level_dba=noise_values,
        green_area_ratio=green_area_values,
        myki_score=myki_values,
    )


def list_data_sources() -> list[DataSourceResponse]:
    return DATA_SOURCES


def get_data_source_by_slug(source_name: str) -> DataSourceResponse | None:
    for source in DATA_SOURCES:
        if source.slug == source_name:
            return source
    return None
