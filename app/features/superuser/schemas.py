from datetime import datetime

from pydantic import BaseModel

from app.features.users.models import UserType


class UserDetailResponse(BaseModel):
    id: int
    email: str
    nickname: str | None
    user_type: UserType
    oauth_provider: str | None
    is_email_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class PostSummaryResponse(BaseModel):
    id: int
    content: str
    artist_name: str | None
    likes_count: int
    created_at: datetime
    user_nickname: str | None
    user_id: int


class CommentSummaryResponse(BaseModel):
    id: int
    content: str
    post_id: int
    created_at: datetime
    user_nickname: str | None
    user_id: int


class UserListResponse(BaseModel):
    users: list[UserDetailResponse]
    total: int
    page: int
    limit: int
    has_next: bool


class BanUserRequest(BaseModel):
    user_id: int
    reason: str | None = None


class BanUserResponse(BaseModel):
    user_id: int
    message: str
    banned_at: datetime
