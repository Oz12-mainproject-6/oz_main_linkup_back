from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
)

from app.features.posts import schemas
from app.features.posts.schemas import PostsQueryParams
from app.features.posts.service import PostService
from app.features.users.dependencies import get_current_user
from app.features.users.models import User

posts_router = APIRouter(prefix="/api/posts", tags=["Posts"])


# ----------------- Post CRUD -----------------
@posts_router.post("/")
async def create_post(
    artist_id: int = Form(...),
    post_content: str = Form(...),
    post_image: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
):
    """포스트 생성"""
    return await PostService.create_post(
        artist_id, post_content, post_image, current_user
    )


@posts_router.get("/", response_model=list[schemas.PostResponse])
async def get_posts(params: PostsQueryParams = Depends()):
    """포스트 목록 조회"""
    return await PostService.get_posts(
        params.limit, params.offset, params.artist_id, params.is_active
    )


@posts_router.get("/{post_id}", response_model=schemas.PostDetailResponse)
async def get_post(post_id: int):
    """포스트 상세 조회 (댓글 포함)"""
    return await PostService.get_post_detail(post_id)


@posts_router.put("/{post_id}", response_model=schemas.PostResponse)
async def update_post(
    post_id: int,
    post_content: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    """포스트 수정"""
    return await PostService.update_post(post_id, post_content, current_user)


@posts_router.delete("/{post_id}")
async def delete_post(post_id: int, current_user: User = Depends(get_current_user)):
    """포스트 삭제"""
    await PostService.delete_post(post_id, current_user)


# ----------------- Like 기능 -----------------
@posts_router.post("/{post_id}/like")
async def toggle_like(post_id: int, current_user: User = Depends(get_current_user)):
    """좋아요 토글"""
    return await PostService.toggle_like(post_id, current_user)


@posts_router.get("/{post_id}/likes", response_model=list[schemas.LikeResponse])
async def get_post_likes(post_id: int):
    """포스트 좋아요 목록 조회"""
    return await PostService.get_post_likes(post_id)


# ----------------- Comment CRUD -----------------
@posts_router.post("/{post_id}/comments", response_model=schemas.CommentResponse)
async def create_comment(
    post_id: int,
    request: schemas.CommentCreate,
    current_user: User = Depends(get_current_user),
):
    """댓글 생성"""
    return await PostService.create_comment(
        post_id, request.comment_content, current_user
    )


@posts_router.get("/{post_id}/comments", response_model=list[schemas.CommentResponse])
async def get_comments(post_id: int):
    """포스트 댓글 목록 조회"""
    return await PostService.get_comments(post_id)


@posts_router.put("/comments/{comment_id}", response_model=schemas.CommentResponse)
async def update_comment(
    comment_id: int,
    request: schemas.CommentUpdate,
    current_user: User = Depends(get_current_user),
):
    """댓글 수정"""
    return await PostService.update_comment(
        comment_id, request.comment_content, current_user
    )


@posts_router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int, current_user: User = Depends(get_current_user)
):
    """댓글 삭제"""
    await PostService.delete_comment(comment_id, current_user)
