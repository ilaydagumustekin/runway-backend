from sqlalchemy.orm import Session

from app.schemas.neighborhood_detail import (
    NeighborhoodDetailChartSummary,
    NeighborhoodDetailDataSource,
    NeighborhoodDetailEnvironmentalData,
    NeighborhoodDetailMYKI,
    NeighborhoodDetailResponse,
)
from app.services.myki_service import calculate_myki_from_environmental_data
from app.services.statistics_service import (
    build_neighborhood_chart_data,
    get_latest_environmental_record,
    get_neighborhood_or_none,
    list_data_sources,
)


def build_neighborhood_detail_response(
    db: Session, neighborhood_id: int, chart_limit: int = 20
) -> NeighborhoodDetailResponse | None:
    neighborhood = get_neighborhood_or_none(db, neighborhood_id)
    if not neighborhood:
        return None

    latest_record = get_latest_environmental_record(db, neighborhood_id)
    chart_data = build_neighborhood_chart_data(db, neighborhood_id, chart_limit)

    latest_environmental_data = None
    myki = None

    if latest_record:
        latest_environmental_data = NeighborhoodDetailEnvironmentalData.model_validate(latest_record)
        myki_score, myki_category = calculate_myki_from_environmental_data(latest_record)
        myki = NeighborhoodDetailMYKI(score=myki_score, category=myki_category)

    data_sources = [
        NeighborhoodDetailDataSource(name=source.name, type=source.type, status=source.status)
        for source in list_data_sources()
    ]

    return NeighborhoodDetailResponse(
        neighborhood=neighborhood,
        latest_environmental_data=latest_environmental_data,
        myki=myki,
        chart_summary=NeighborhoodDetailChartSummary(
            labels=chart_data.labels,
            aqi=chart_data.aqi,
            noise_level_dba=chart_data.noise_level_dba,
            green_area_ratio=chart_data.green_area_ratio,
            myki_score=chart_data.myki_score,
        ),
        data_sources=data_sources,
    )
