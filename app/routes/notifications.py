from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.neighborhood import Neighborhood
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationCreate, NotificationResponse, NotificationUpdate
from app.services.auth_service import get_current_active_user

notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])
admin_notifications_router = APIRouter(prefix="/admin/notifications", tags=["Admin Notifications"])


def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


@notifications_router.get("", response_model=list[NotificationResponse])
def list_notifications(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> list[Notification]:
    notifications = db.scalars(
        select(Notification)
        .where(or_(Notification.user_id == current_user.id, Notification.user_id.is_(None)))
        .order_by(desc(Notification.created_at))
    ).all()
    return list(notifications)


@notifications_router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: int,
    payload: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Notification:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            or_(Notification.user_id == current_user.id, Notification.user_id.is_(None)),
        )
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found.")

    notification.is_read = payload.is_read
    db.commit()
    db.refresh(notification)
    return notification


@admin_notifications_router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Notification:
    if payload.user_id is not None and not db.get(User, payload.user_id):
        raise HTTPException(status_code=404, detail="User not found.")

    if payload.neighborhood_id is not None and not db.get(Neighborhood, payload.neighborhood_id):
        raise HTTPException(status_code=404, detail="Neighborhood not found.")

    notification = Notification(**payload.model_dump(), is_read=False)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@admin_notifications_router.get("", response_model=list[NotificationResponse])
def list_all_notifications(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)
) -> list[Notification]:
    notifications = db.scalars(select(Notification).order_by(desc(Notification.created_at))).all()
    return list(notifications)


@admin_notifications_router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> dict[str, str]:
    notification = db.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found.")

    db.delete(notification)
    db.commit()
    return {"message": "Notification deleted successfully."}
