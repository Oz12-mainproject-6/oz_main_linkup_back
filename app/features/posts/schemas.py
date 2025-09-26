from datetime import datetime

from pydantic import BaseModel


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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ----------------- Comment -----------------
"""
class CommentCreate(BaseModel):
    comment_content: str = Field(..., min_length=1, max_length=500)


class CommentUpdate(BaseModel):
    comment_content: str = Field(..., min_length=1, max_length=500)
"""


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
