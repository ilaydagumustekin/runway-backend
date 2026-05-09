from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from app.services.auth_service import (
    authenticate_user,
    blacklist_token,
    create_access_token,
    get_current_active_user,
    get_user_by_email,
    hash_password,
    oauth2_scheme,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    existing_user = get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered.")

    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email.strip().lower(),
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenResponse:
    # Swagger Authorize sends username/password as form-data.
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    access_token = create_access_token(subject=user.email)
    return TokenResponse(access_token=access_token)


@router.post("/login-json", response_model=TokenResponse)
def login_user_json(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    access_token = create_access_token(subject=user.email)
    return TokenResponse(access_token=access_token)


@router.post("/logout")
def logout_user(token: str = Depends(oauth2_scheme)) -> dict[str, str]:
    """Mevcut token'ı sunucu tarafında geçersiz kılar (blacklist)."""
    blacklist_token(token)
    return {"message": "Logout successful. Token has been invalidated."}
