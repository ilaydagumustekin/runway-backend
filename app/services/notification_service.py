from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_air_quality_alert_if_needed(
    db: Session, user_id: int | None, neighborhood_id: int | None, aqi: float
) -> Notification | None:
    severity: str | None = None

    if aqi >= 200:
        severity = "critical"
    elif aqi >= 150:
        severity = "high"
    elif aqi >= 100:
        severity = "medium"

    if severity is None:
        return None

    notification = Notification(
        user_id=user_id,
        neighborhood_id=neighborhood_id,
        title="Hava Kalitesi Uyarisi",
        message="Secili mahallede hava kalitesi sagliksiz seviyeye yaklasti.",
        notification_type="air_quality",
        severity=severity,
        is_read=False,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
