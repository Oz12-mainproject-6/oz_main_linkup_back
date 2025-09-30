from datetime import datetime

from pydantic import BaseModel, Field

from app.core.schemas import BaseQueryParams


# ----------------- User / Artist -----------------
class UserResponse(BaseModel):
    id: int
    nickname: str

    class Config:
        from_attributes = True


class ArtistResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# ----------------- Post -----------------
"""
class PostCreate(BaseModel):
    artist_id: int
    post_content: str = Field(..., min_length=1, max_length=1000)


class PostUpdate(BaseModel):
    post_content: str = Field(..., min_length=1, max_length=1000)
"""


class PostResponse(BaseModel):
    id: int
    content: str
    image_url: str | None = None  # 이미지 URL 필드 추가
    user: UserResponse
    artist: ArtistResponse
    likes_count: int
    comments_count: int = 0  # 댓글 수 필드 추가
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ----------------- Comment -----------------
class CommentCreate(BaseModel):
    comment_content: str

    class Config:
        from_attributes = True


class CommentUpdate(BaseModel):
    comment_content: str

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    id: int
    content: str
    user: UserResponse
    post_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ----------------- Like -----------------
class LikeResponse(BaseModel):
    id: int
    user: UserResponse
    post_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ----------------- Post with Comments -----------------
class PostDetailResponse(PostResponse):
    comments: list[CommentResponse] = []

    class Config:
        from_attributes = True


# ----------------- Query Parameters -----------------
class PostsQueryParams(BaseQueryParams):
    """포스트 목록 조회 쿼리 파라미터"""
    
    artist_id: int | None = Field(None, description="특정 아티스트의 포스트만 조회")
    is_active: bool | None = Field(None, description="구독 중인 아티스트만 조회 (true: 구독 중만, null: 전체)")
