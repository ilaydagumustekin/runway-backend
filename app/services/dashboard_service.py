from datetime import datetime, timezone

from sqlalchemy import asc, or_, select
from sqlalchemy.orm import Session

from app.models.environmental_data import EnvironmentalData
from app.models.navigation_session import NavigationSession
from app.models.neighborhood import Neighborhood
from app.models.notification import Notification
from app.models.user import User
from app.schemas.dashboard import (
    DashboardActiveRouteResponse,
    DashboardCurrentEnvironmentItem,
    DashboardEnvironmentScoreResponse,
    DashboardHomeResponse,
    DashboardHourlyWeatherItem,
    DashboardLocationResponse,
    DashboardMetricValueResponse,
    DashboardNavigationResponse,
    DashboardNotificationsResponse,
    DashboardQuickMetricsResponse,
)
from app.services.air_quality_fetch_service import fetch_and_persist_air_quality
from app.services.location_service import find_nearest_neighborhood
from app.services.myki_service import calculate_myki_from_environmental_data, get_myki_for_neighborhood
from app.services.statistics_service import get_latest_environmental_record
from app.services.external.weather_service import fetch_current_weather


def _get_fallback_neighborhood(db: Session, current_user: User) -> Neighborhood | None:
    if current_user.preferred_city or current_user.preferred_district:
        stmt = select(Neighborhood)
        if current_user.preferred_city:
            stmt = stmt.where(Neighborhood.city == current_user.preferred_city)
        if current_user.preferred_district:
            stmt = stmt.where(Neighborhood.district == current_user.preferred_district)
        preferred = db.scalar(stmt.order_by(asc(Neighborhood.id)))
        if preferred:
            return preferred

    return db.scalar(select(Neighborhood).order_by(asc(Neighborhood.id)))


def resolve_dashboard_neighborhood(
    db: Session,
    current_user: User,
    neighborhood_id: int | None,
    latitude: float | None,
    longitude: float | None,
) -> Neighborhood | None:
    if neighborhood_id is not None:
        return db.get(Neighborhood, neighborhood_id)

    if latitude is not None and longitude is not None:
        nearest = find_nearest_neighborhood(db, latitude, longitude)
        if nearest:
            return db.get(Neighborhood, nearest.neighborhood.id)

    return _get_fallback_neighborhood(db, current_user)


def _relative_updated_text(updated_at: datetime | None) -> str:
    if updated_at is None:
        return "Henüz veri yok"

    now = datetime.now(timezone.utc)
    updated_utc = updated_at.replace(tzinfo=timezone.utc) if updated_at.tzinfo is None else updated_at
    delta_seconds = max(0, int((now - updated_utc).total_seconds()))

    if delta_seconds < 60:
        return "Az önce"
    if delta_seconds < 3600:
        minutes = delta_seconds // 60
        return f"{minutes} dk önce"
    if delta_seconds < 86400:
        hours = delta_seconds // 3600
        return f"{hours} sa önce"
    days = delta_seconds // 86400
    return f"{days} gün önce"


def _environment_status_aqi(aqi: float) -> tuple[str, str]:
    if aqi <= 50:
        return "İyi", "good"
    if aqi <= 100:
        return "Orta", "medium"
    return "Kötü", "bad"


def _environment_status_noise(noise: float) -> tuple[str, str]:
    if noise <= 55:
        return "İyi", "good"
    if noise <= 70:
        return "Orta", "medium"
    return "Kötü", "bad"


def _environment_status_green(green_area: float) -> tuple[str, str]:
    if green_area >= 30:
        return "İyi", "good"
    if green_area >= 15:
        return "Orta", "medium"
    return "Kötü", "bad"


def _build_hourly_weather(
    lat: float = 37.76, lon: float = 30.55
) -> tuple[list[DashboardHourlyWeatherItem], dict | None]:
    """Open-Meteo API'den gerçek hava durumu çeker. API başarısızsa None döner."""
    weather_data = fetch_current_weather(lat, lon)
    if not weather_data:
        return [], None
    hourly_items = [
        DashboardHourlyWeatherItem(
            time=h["time"],
            temperature=h["temperature"],
            condition=h["condition"],
        )
        for h in weather_data.get("hourly_forecast", [])
    ]
    return hourly_items, weather_data


def _get_chart_summary(db: Session, neighborhood_id: int, limit: int = 5) -> dict[str, list[float] | list[str]]:
    records = db.scalars(
        select(EnvironmentalData)
        .where(EnvironmentalData.neighborhood_id == neighborhood_id)
        .order_by(asc(EnvironmentalData.created_at))
        .limit(limit)
    ).all()

    labels: list[str] = []
    aqi_values: list[float] = []
    noise_values: list[float] = []
    green_values: list[float] = []
    myki_values: list[float] = []

    for record in records:
        myki_score, _ = calculate_myki_from_environmental_data(record)
        labels.append(record.created_at.date().isoformat())
        aqi_values.append(record.aqi)
        noise_values.append(record.noise_level_dba)
        green_values.append(record.green_area_ratio)
        myki_values.append(myki_score)

    return {
        "labels": labels,
        "aqi": aqi_values,
        "noise_level_dba": noise_values,
        "green_area_ratio": green_values,
        "myki_score": myki_values,
    }


def _get_unread_notification_count(db: Session, current_user: User) -> int:
    return len(
        db.scalars(
            select(Notification).where(
                or_(Notification.user_id == current_user.id, Notification.user_id.is_(None)),
                Notification.is_read.is_(False),
            )
        ).all()
    )


def _get_active_navigation(db: Session, current_user: User) -> DashboardNavigationResponse:
    active_session = db.scalar(
        select(NavigationSession).where(
            NavigationSession.user_id == current_user.id,
            NavigationSession.status == "active",
        )
    )
    if not active_session:
        return DashboardNavigationResponse(has_active_route=False, active_route=None)

    return DashboardNavigationResponse(
        has_active_route=True,
        active_route=DashboardActiveRouteResponse(
            navigation_session_id=active_session.id,
            route_name=active_session.route_name,
            start_latitude=active_session.start_latitude,
            start_longitude=active_session.start_longitude,
            destination_latitude=active_session.destination_latitude,
            destination_longitude=active_session.destination_longitude,
            started_at=active_session.started_at,
        ),
    )


def build_dashboard_home(
    db: Session,
    current_user: User,
    neighborhood_id: int | None,
    latitude: float | None,
    longitude: float | None,
) -> DashboardHomeResponse | None:
    neighborhood = resolve_dashboard_neighborhood(
        db, current_user, neighborhood_id=neighborhood_id, latitude=latitude, longitude=longitude
    )
    if not neighborhood:
        return None

    fetch_and_persist_air_quality(neighborhood, db)

    latest_record = get_latest_environmental_record(db, neighborhood.id)
    myki_payload = get_myki_for_neighborhood(db, neighborhood.id)

    if latest_record:
        aqi = float(latest_record.aqi) if latest_record.aqi is not None else 0.0
        noise = float(latest_record.noise_level_dba) if latest_record.noise_level_dba is not None else 0.0
        green_area = float(latest_record.green_area_ratio) if latest_record.green_area_ratio is not None else 0.0
    else:
        aqi = noise = green_area = None
    air_status, air_status_key = _environment_status_aqi(aqi) if aqi is not None else (None, None)
    noise_status, noise_status_key = _environment_status_noise(noise) if noise is not None else (None, None)
    green_status, green_status_key = _environment_status_green(green_area) if green_area is not None else (None, None)
    chart_summary = _get_chart_summary(db, neighborhood.id)
    hourly_weather_items, weather_data = _build_hourly_weather(neighborhood.latitude, neighborhood.longitude)
    if weather_data:
        weather_temp = weather_data.get("temperature")
        weather_cond = weather_data.get("condition_text")
        weather_key = weather_data.get("condition_key")
    else:
        weather_temp = None
        weather_cond = None
        weather_key = None

    return DashboardHomeResponse(
        location=DashboardLocationResponse(
            neighborhood_id=neighborhood.id,
            neighborhood_name=neighborhood.name,
            city=neighborhood.city,
            district=neighborhood.district,
            latitude=neighborhood.latitude,
            longitude=neighborhood.longitude,
        ),
        environment_score=DashboardEnvironmentScoreResponse(
            score=round(myki_payload.score, 2) if myki_payload else None,
            category=myki_payload.category if myki_payload else None,
            category_key=myki_payload.category if myki_payload else None,
            last_updated_text=_relative_updated_text(latest_record.created_at if latest_record else None),
            updated_at=latest_record.created_at if latest_record else None,
        ),
        quick_metrics=DashboardQuickMetricsResponse(
            air_quality=DashboardMetricValueResponse(
                label="Hava", value=round(aqi) if aqi is not None else None, unit="AQI"
            ),
            noise=DashboardMetricValueResponse(
                label="Gürültü", value=round(noise) if noise is not None else None, unit="dB"
            ),
            green_area=DashboardMetricValueResponse(
                label="Yeşil", value=round(green_area) if green_area is not None else None, unit="%"
            ),
        ),
        current_environment=[
            DashboardCurrentEnvironmentItem(
                key="air_quality",
                title="Hava Kalitesi",
                value=round(aqi) if aqi is not None else None,
                unit="AQI",
                status=air_status,
                status_key=air_status_key,
            ),
            DashboardCurrentEnvironmentItem(
                key="noise",
                title="Gürültü",
                value=round(noise) if noise is not None else None,
                unit="dB",
                status=noise_status,
                status_key=noise_status_key,
            ),
            DashboardCurrentEnvironmentItem(
                key="green_area",
                title="Yeşil Alan",
                value=round(green_area) if green_area is not None else None,
                unit="%",
                status=green_status,
                status_key=green_status_key,
            ),
            DashboardCurrentEnvironmentItem(
                key="weather",
                title="Hava Durumu",
                value=weather_temp,
                unit="°C",
                status=weather_cond,
                status_key=weather_key,
            ),
        ],
        hourly_weather=hourly_weather_items,
        notifications=DashboardNotificationsResponse(
            unread_count=_get_unread_notification_count(db, current_user)
        ),
        navigation=_get_active_navigation(db, current_user),
    )
