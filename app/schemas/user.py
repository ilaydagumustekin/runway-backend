from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    phone_number: str | None = None
    profile_image_url: str | None = None
    preferred_city: str | None = None
    preferred_district: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileResponse(UserResponse):
    pass


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone_number: str | None = Field(default=None, max_length=30)
    profile_image_url: HttpUrl | None = None
    preferred_city: str | None = Field(default=None, max_length=80)
    preferred_district: str | None = Field(default=None, max_length=80)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
