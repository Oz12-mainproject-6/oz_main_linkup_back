from pydantic import BaseModel, Field


# ----------------- User / Artist -----------------
class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class ArtistResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# ----------------- Post -----------------
class PostBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)  # 게시글 글자 수 제한 설정


class PostCreate(PostBase):
    artist_id: int


class PostUpdate(PostBase):
    pass


class PostResponse(PostBase):
    id: int
    user: UserResponse
    artist: ArtistResponse
    likes_count: int

    class Config:
        from_attributes = True


# ----------------- Comment -----------------
class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    pass


class CommentUpdate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: int
    post_id: int
    user: UserResponse

    class Config:
        from_attributes = True
