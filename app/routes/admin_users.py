from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import get_user_by_email, hash_password

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


@router.post("/create-admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_admin_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    if not settings.seed_demo_data:
        raise HTTPException(
            status_code=403,
            detail="Admin user creation endpoint is disabled outside demo/development mode.",
        )

    existing_user = get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered.")

    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email.strip().lower(),
        hashed_password=hash_password(payload.password),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
