from fastapi import APIRouter, Depends

from app.models.user import User
from app.schemas.user import UserResponse
from app.services.auth_service import get_current_active_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user
