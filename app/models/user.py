from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    profile_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    preferred_city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    preferred_district: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    favorite_neighborhoods = relationship("FavoriteNeighborhood", back_populates="user")
    route_history_entries = relationship("RouteHistory", back_populates="user")
    feedback_entries = relationship("Feedback", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    navigation_sessions = relationship("NavigationSession", back_populates="user")
