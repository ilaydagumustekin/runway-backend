from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NoiseMeasurement(Base):
    __tablename__ = "noise_measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    neighborhood_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("neighborhoods.id"), index=True, nullable=False
    )
    noise_level_dba: Mapped[float] = mapped_column("dba", Float, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
