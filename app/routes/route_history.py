from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.route_history import RouteHistory
from app.models.user import User
from app.schemas.route_history import RouteHistoryCreate, RouteHistoryResponse
from app.services.auth_service import get_current_active_user

router = APIRouter(prefix="/route-history", tags=["Route History"])


def _get_user_route_history_or_404(
    db: Session,
    route_history_id: int,
    current_user_id: int,
) -> RouteHistory:
    record = db.scalar(
        select(RouteHistory).where(
            RouteHistory.id == route_history_id,
            RouteHistory.user_id == current_user_id,
        )
    )
    if not record:
        raise HTTPException(status_code=404, detail="Route history not found.")
    return record


@router.post("", response_model=RouteHistoryResponse, status_code=status.HTTP_201_CREATED)
def create_route_history(
    payload: RouteHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RouteHistory:
    record = RouteHistory(user_id=current_user.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[RouteHistoryResponse])
def list_route_history(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> list[RouteHistory]:
    records = db.scalars(
        select(RouteHistory)
        .where(RouteHistory.user_id == current_user.id)
        .order_by(desc(RouteHistory.created_at))
    ).all()
    return list(records)


@router.get("/favorites", response_model=list[RouteHistoryResponse])
def list_favorite_route_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[RouteHistory]:
    records = db.scalars(
        select(RouteHistory)
        .where(
            RouteHistory.user_id == current_user.id,
            RouteHistory.is_favorite.is_(True),
        )
        .order_by(desc(RouteHistory.created_at))
    ).all()
    return list(records)


@router.get("/{route_history_id}", response_model=RouteHistoryResponse)
def get_route_history_item(
    route_history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RouteHistory:
    return _get_user_route_history_or_404(db, route_history_id, current_user.id)


@router.patch("/{route_history_id}/favorite", response_model=RouteHistoryResponse)
def favorite_route_history_item(
    route_history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RouteHistory:
    record = _get_user_route_history_or_404(db, route_history_id, current_user.id)
    record.is_favorite = True
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/{route_history_id}/unfavorite", response_model=RouteHistoryResponse)
def unfavorite_route_history_item(
    route_history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RouteHistory:
    record = _get_user_route_history_or_404(db, route_history_id, current_user.id)
    record.is_favorite = False
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{route_history_id}")
def delete_route_history_item(
    route_history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    record = _get_user_route_history_or_404(db, route_history_id, current_user.id)
    db.delete(record)
    db.commit()
    return {"message": "Route history deleted successfully."}
