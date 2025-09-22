from pydantic import BaseModel, Field


# ----------------- User / Artist -----------------
class UserResponse(BaseModel):
    user_id: int
    user_nickname: str

    class Config:
        from_attributes = True


class ArtistResponse(BaseModel):
    artist_id: int
    artist_name: str

    class Config:
        from_attributes = True


# ----------------- Post -----------------
class PostBase(BaseModel):
    post_content: str = Field(
        ..., min_length=1, max_length=500
    )  # 게시글 글자 수 제한 설정


class PostCreate(PostBase):
    artist_id: int


class PostUpdate(PostBase):
    pass


class PostResponse(PostBase):
    post_id: int
    user: UserResponse
    artist: ArtistResponse
    likes_count: int

    class Config:
        from_attributes = True


# ----------------- Comment -----------------
class CommentBase(BaseModel):
    comment_content: str


class CommentCreate(CommentBase):
    pass


class CommentUpdate(CommentBase):
    pass


class CommentResponse(CommentBase):
    comment_id: int
    post_id: int
    user: UserResponse

    class Config:
        from_attributes = True
