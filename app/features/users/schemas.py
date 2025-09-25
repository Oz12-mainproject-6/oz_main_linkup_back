from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.features.users.models import UserType


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: str | None = None
    user_type: UserType = UserType.FAN
    verification_code: str  # 이메일 인증 코드 필수


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# class SocialLoginRequest(BaseModel):
#     provider: str  # "google" or "kakao"
#     access_token: str
#     user_type: UserType = UserType.FAN


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


class UserPostResponse(BaseModel):
    """내 포스트 정보"""

    id: int
    content: str
    artist_id: int
    artist_name: str | None
    likes_count: int
    comments_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserMeResponse(BaseModel):
    id: int
    email: EmailStr | None
    nickname: str | None
    profile_image_url: str | None
    user_type: UserType

    class Config:
        from_attributes = True


class UserMeWithPostsResponse(BaseModel):
    """포스트 포함한 내 프로필 응답"""

    id: int
    email: EmailStr | None
    nickname: str | None
    profile_image_url: str | None
    user_type: UserType
    posts: list[UserPostResponse] = []

    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    new_password_confirm: str
