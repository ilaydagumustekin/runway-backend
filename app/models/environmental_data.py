from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EnvironmentalData(Base):
    __tablename__ = "environmental_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    neighborhood_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("neighborhoods.id"), index=True, nullable=False
    )
    pm25: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm10: Mapped[float | None] = mapped_column(Float, nullable=True)
    no2: Mapped[float | None] = mapped_column(Float, nullable=True)
    o3: Mapped[float | None] = mapped_column(Float, nullable=True)
    aqi: Mapped[float | None] = mapped_column(Float, nullable=True)
    green_area_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    noise_level_dba: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
