from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ExternalAirQuality(Base):
    __tablename__ = "external_air_quality"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # openaq, waqi vs
    station_id: Mapped[str] = mapped_column(String(100), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    pm25: Mapped[float] = mapped_column(Float, nullable=True)
    pm10: Mapped[float] = mapped_column(Float, nullable=True)
    no2: Mapped[float] = mapped_column(Float, nullable=True)
    o3: Mapped[float] = mapped_column(Float, nullable=True)
    aqi: Mapped[float] = mapped_column(Float, nullable=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
