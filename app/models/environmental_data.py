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
    pm25: Mapped[float] = mapped_column(Float, nullable=False)
    pm10: Mapped[float] = mapped_column(Float, nullable=False)
    no2: Mapped[float] = mapped_column(Float, nullable=False)
    o3: Mapped[float] = mapped_column(Float, nullable=False)
    aqi: Mapped[float] = mapped_column(Float, nullable=False)
    green_area_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    noise_level_dba: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
