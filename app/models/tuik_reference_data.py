from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class TuikReferenceData(Base):
    __tablename__ = "tuik_reference_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    indicator_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. "green_area_per_capita", "avg_aqi"
    value: Mapped[float] = mapped_column(Float, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
