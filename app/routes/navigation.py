from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.navigation_session import NavigationSession
from app.models.route_history import RouteHistory
from app.models.user import User
from app.schemas.navigation import NavigationSessionResponse, NavigationStartRequest
from app.services.auth_service import get_current_active_user

router = APIRouter(prefix="/navigation", tags=["Navigation"])


def get_user_active_navigation_session(db: Session, user_id: int) -> NavigationSession | None:
    return db.scalar(
        select(NavigationSession).where(
            NavigationSession.user_id == user_id, NavigationSession.status == "active"
        )
    )


@router.post("/start", response_model=NavigationSessionResponse, status_code=status.HTTP_201_CREATED)
def start_navigation(
    payload: NavigationStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NavigationSession:
    active_session = get_user_active_navigation_session(db, current_user.id)
    if active_session:
        raise HTTPException(
            status_code=400, detail="User already has an active navigation session."
        )

    route_history = None
    if payload.route_history_id is not None:
        route_history = db.scalar(
            select(RouteHistory).where(
                RouteHistory.id == payload.route_history_id,
                RouteHistory.user_id == current_user.id,
            )
        )
        if not route_history:
            raise HTTPException(status_code=404, detail="Route history not found.")

    session = NavigationSession(
        user_id=current_user.id,
        route_history_id=route_history.id if route_history else None,
        route_name=route_history.route_name if route_history else str(payload.route_name),
        start_latitude=route_history.start_latitude if route_history else float(payload.start_latitude),
        start_longitude=route_history.start_longitude if route_history else float(payload.start_longitude),
        destination_latitude=(
            route_history.destination_latitude
            if route_history
            else float(payload.destination_latitude)
        ),
        destination_longitude=(
            route_history.destination_longitude
            if route_history
            else float(payload.destination_longitude)
        ),
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/current", response_model=NavigationSessionResponse)
def get_current_navigation(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> NavigationSession:
    session = get_user_active_navigation_session(db, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Active navigation session not found.")
    return session


def _update_navigation_status(
    navigation_session_id: int,
    new_status: str,
    db: Session,
    current_user: User,
) -> NavigationSession:
    session = db.scalar(
        select(NavigationSession).where(
            NavigationSession.id == navigation_session_id,
            NavigationSession.user_id == current_user.id,
        )
    )
    if not session:
        raise HTTPException(status_code=404, detail="Navigation session not found.")

    session.status = new_status
    session.ended_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session


@router.patch("/{navigation_session_id}/complete", response_model=NavigationSessionResponse)
def complete_navigation(
    navigation_session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NavigationSession:
    return _update_navigation_status(navigation_session_id, "completed", db, current_user)


@router.patch("/{navigation_session_id}/cancel", response_model=NavigationSessionResponse)
def cancel_navigation(
    navigation_session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NavigationSession:
    return _update_navigation_status(navigation_session_id, "cancelled", db, current_user)


@router.get("/history", response_model=list[NavigationSessionResponse])
def list_navigation_history(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> list[NavigationSession]:
    sessions = db.scalars(
        select(NavigationSession)
        .where(NavigationSession.user_id == current_user.id)
        .order_by(desc(NavigationSession.started_at))
    ).all()
    return list(sessions)
