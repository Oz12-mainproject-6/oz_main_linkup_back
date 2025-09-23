from pydantic import BaseModel, EmailStr

from app.features.users.models import UserType


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    phone_number: str | None = None
    nickname: str | None = None
    user_type: UserType = UserType.FAN
    verification_code: str  # 이메일 인증 코드 필수


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SocialLoginRequest(BaseModel):
    provider: str  # "google" or "kakao"
    access_token: str
    user_type: UserType = UserType.FAN


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SendVerificationEmailRequest(BaseModel):
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str


class EmailVerificationResponse(BaseModel):
    message: str
    email: str


class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str | None
    user_type: UserType
    oauth_provider: str | None = None
    is_email_verified: bool = False


class UserMeResponse(BaseModel):
    id: int
    email: EmailStr | None
    nickname: str | None
    phone_number: str | None
    user_type: UserType

    class Config:
        from_attributes = True


class UserMeUpdateRequest(BaseModel):
    nickname: str | None = None
    phone_number: str | None = None
