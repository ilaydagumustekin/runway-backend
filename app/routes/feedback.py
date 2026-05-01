from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.feedback import Feedback
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackResponse, FeedbackStatusUpdate
from app.services.auth_service import get_current_active_user

feedback_router = APIRouter(prefix="/feedback", tags=["Feedback"])
admin_feedback_router = APIRouter(prefix="/admin/feedback", tags=["Admin Feedback"])


def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


@feedback_router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Feedback:
    feedback = Feedback(user_id=current_user.id, status="new", **payload.model_dump())
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@feedback_router.get("/my", response_model=list[FeedbackResponse])
def list_my_feedback(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> list[Feedback]:
    feedback_items = db.scalars(
        select(Feedback)
        .where(Feedback.user_id == current_user.id)
        .order_by(desc(Feedback.created_at))
    ).all()
    return list(feedback_items)


@admin_feedback_router.get("", response_model=list[FeedbackResponse])
def list_all_feedback(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)
) -> list[Feedback]:
    feedback_items = db.scalars(select(Feedback).order_by(desc(Feedback.created_at))).all()
    return list(feedback_items)


@admin_feedback_router.patch("/{feedback_id}/status", response_model=FeedbackResponse)
def update_feedback_status(
    feedback_id: int,
    payload: FeedbackStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Feedback:
    feedback = db.get(Feedback, feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found.")

    feedback.status = payload.status.strip()
    db.commit()
    db.refresh(feedback)
    return feedback
