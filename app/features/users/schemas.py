from pydantic import BaseModel, EmailStr

from app.features.users.models import UserType


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    phone_number: str | None = None
    nickname: str | None = None
    user_type: UserType = UserType.FAN


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str | None
    user_type: UserType
