from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.features.posts.models import Comment, Like, Post
from app.features.images.models import ImageType, SharedImage
from app.features.superuser.dependencies import get_superuser
from app.features.superuser.schemas import (
    BanUserRequest,
    BanUserResponse,
    CommentSummaryResponse,
    PostSummaryResponse,
    UserDetailResponse,
    UserListResponse,
)
from app.features.users.models import User, UserType

superuser_router = APIRouter(prefix="/api/superuser", tags=["Superuser"])


@superuser_router.get("/users", response_model=UserListResponse)
async def get_users(
    user_type: UserType | None = Query(None, description="필터링할 사용자 타입"),
    limit: int = Query(20, ge=1, le=100, description="조회할 사용자 수"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    current_user: User = Depends(get_superuser),
):
    """모든 사용자 조회 (슈퍼유저만 접근 가능)"""
    offset = (page - 1) * limit

    query = User.all()

    if user_type:
        query = query.filter(user_type=user_type)

    total = await query.count()

    users = await query.offset(offset).limit(limit).order_by("-created_at")

    user_list = [
        UserDetailResponse(
            id=user.id,
            email=user.email,
            nickname=user.nickname,
            user_type=user.user_type,
            oauth_provider=user.oauth_provider,
            is_email_verified=user.is_email_verified,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            deleted_at=user.deleted_at,
        )
        for user in users
    ]

    has_next = (offset + limit) < total

    return UserListResponse(
        users=user_list,
        total=total,
        page=page,
        limit=limit,
        has_next=has_next,
    )


@superuser_router.get("/posts", response_model=list[PostSummaryResponse])
async def get_all_posts(
    limit: int = Query(20, ge=1, le=100, description="조회할 포스트 수"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    current_user: User = Depends(get_superuser),
):
    """전체 포스트 조회 (모든 사용자 기준)"""
    offset = (page - 1) * limit

    posts = (
        await Post.all()
        .prefetch_related("user", "artist")
        .order_by("-created_at")
        .offset(offset)
        .limit(limit)
    )

    post_responses = []
    for post in posts:
        likes_count = await Like.filter(post=post).count()
        artist_name = (
            post.artist.stage_name or post.artist.group_name if post.artist else None
        )
        
        # 포스트에 첨부된 이미지들 조회 (ImageType.POST)
        post_images = await SharedImage.filter(
            post=post, image_type=ImageType.POST
        ).values_list("url", flat=True)
        
        post_responses.append(
            PostSummaryResponse(
                id=post.id,
                content=post.content,
                artist_name=artist_name,
                likes_count=likes_count,
                created_at=post.created_at,
                user_nickname=post.user.nickname,
                user_id=post.user.id,
                post_images=list(post_images) if post_images else None,
            )
        )

    return post_responses


@superuser_router.get("/comments", response_model=list[CommentSummaryResponse])
async def get_all_comments(
    limit: int = Query(20, ge=1, le=100, description="조회할 댓글 수"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    current_user: User = Depends(get_superuser),
):
    """전체 댓글 조회 (모든 사용자 기준)"""
    offset = (page - 1) * limit

    comments = (
        await Comment.all()
        .prefetch_related("user")
        .order_by("-created_at")
        .offset(offset)
        .limit(limit)
    )

    comment_responses = [
        CommentSummaryResponse(
            id=comment.id,
            content=comment.content,
            post_id=comment.post_id,
            created_at=comment.created_at,
            user_nickname=comment.user.nickname,
            user_id=comment.user.id,
        )
        for comment in comments
    ]

    return comment_responses


@superuser_router.post("/users/ban", response_model=BanUserResponse)
async def ban_user(
    ban_request: BanUserRequest,
    current_user: User = Depends(get_superuser),
):
    """사용자 차단 (BAN 타입으로 변경)"""
    user = await User.get_or_none(id=ban_request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    if user.user_type == UserType.BAN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 차단된 사용자입니다.",
        )

    # 원래 타입을 저장하고 BAN으로 변경
    user.original_user_type = user.user_type
    user.user_type = UserType.BAN
    await user.save()

    return BanUserResponse(
        user_id=user.id,
        message="사용자가 성공적으로 차단되었습니다.",
        banned_at=datetime.now(),
    )


@superuser_router.post("/users/{user_id}/unban")
async def unban_user(
    user_id: int,
    current_user: User = Depends(get_superuser),
):
    """사용자 차단 해제 (원래 타입으로 복원)"""
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    if user.user_type != UserType.BAN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="차단되지 않은 사용자입니다.",
        )

    # 원래 타입으로 복원 (기본값: FAN)
    original_type = user.original_user_type or UserType.FAN
    user.user_type = original_type
    user.original_user_type = None
    await user.save()

    return {
        "user_id": user.id,
        "message": f"사용자 차단이 해제되었습니다. 복원된 타입: {original_type}",
        "unbanned_at": datetime.now(),
        "restored_user_type": original_type,
    }
