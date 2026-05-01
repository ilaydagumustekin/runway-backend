from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FavoriteNeighborhood(Base):
    __tablename__ = "favorite_neighborhoods"
    __table_args__ = (
        UniqueConstraint("user_id", "neighborhood_id", name="uq_user_neighborhood_favorite"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    neighborhood_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("neighborhoods.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="favorite_neighborhoods")
    neighborhood = relationship("Neighborhood", back_populates="favorite_entries")
