from datetime import datetime

from pydantic import BaseModel


class DashboardLocationResponse(BaseModel):
    neighborhood_id: int
    neighborhood_name: str
    city: str
    district: str
    latitude: float
    longitude: float


class DashboardEnvironmentScoreResponse(BaseModel):
    score: float | None
    category: str | None
    category_key: str | None
    last_updated_text: str
    updated_at: datetime | None


class DashboardMetricValueResponse(BaseModel):
    label: str
    value: float | int | None
    unit: str


class DashboardQuickMetricsResponse(BaseModel):
    air_quality: DashboardMetricValueResponse
    noise: DashboardMetricValueResponse
    green_area: DashboardMetricValueResponse


class DashboardCurrentEnvironmentItem(BaseModel):
    key: str
    title: str
    value: float | int | None
    unit: str
    status: str | None
    status_key: str | None


class DashboardHourlyWeatherItem(BaseModel):
    time: str
    temperature: int
    condition: str


class DashboardNotificationsResponse(BaseModel):
    unread_count: int


class DashboardActiveRouteResponse(BaseModel):
    navigation_session_id: int
    route_name: str
    start_latitude: float
    start_longitude: float
    destination_latitude: float
    destination_longitude: float
    started_at: datetime


class DashboardNavigationResponse(BaseModel):
    has_active_route: bool
    active_route: DashboardActiveRouteResponse | None


class DashboardHomeResponse(BaseModel):
    location: DashboardLocationResponse
    environment_score: DashboardEnvironmentScoreResponse
    quick_metrics: DashboardQuickMetricsResponse
    current_environment: list[DashboardCurrentEnvironmentItem]
    hourly_weather: list[DashboardHourlyWeatherItem]
    notifications: DashboardNotificationsResponse
    navigation: DashboardNavigationResponse
