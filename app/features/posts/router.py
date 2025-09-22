from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.features.artists.models import Artist
from app.features.posts import models, schemas
from app.features.users.dependencies import get_current_user
from app.features.users.models import User

posts_router = APIRouter(prefix="/api/posts", tags=["Posts"])


# ----------------- Post CRUD -----------------
@posts_router.post("/", response_model=schemas.PostResponse)
async def create_post(
    post_in: schemas.PostCreate, current_user: User = Depends(get_current_user)
):
    """포스트 생성"""
    # 아티스트 존재 확인
    artist = await Artist.get_or_none(id=post_in.artist_id)
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artist not found"
        )

    # 포스트 생성
    post = await models.Post.create(
        user=current_user,
        artist=artist,
        content=post_in.post_content,
    )
    await post.fetch_related("user", "artist")

    # 좋아요 수 계산
    likes_count = await models.Like.filter(post=post).count()

    return schemas.PostResponse(
        id=post.id,
        content=post.content,
        user=schemas.UserResponse(id=post.user.id, nickname=post.user.nickname),
        artist=schemas.ArtistResponse(
            id=post.artist.id, 
            name=post.artist.stage_name or post.artist.group_name
        ),
        likes_count=likes_count,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@posts_router.get("/", response_model=List[schemas.PostResponse])
async def get_posts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    artist_id: int = Query(None, description="특정 아티스트의 포스트만 조회"),
):
    """포스트 목록 조회"""
    query = models.Post.all().prefetch_related("user", "artist")

    if artist_id:
        query = query.filter(artist_id=artist_id)

    posts = await query.offset(offset).limit(limit).order_by("-created_at")

    result = []
    for post in posts:
        likes_count = await models.Like.filter(post=post).count()
        result.append(
            schemas.PostResponse(
                id=post.id,
                content=post.content,
                user=schemas.UserResponse(id=post.user.id, nickname=post.user.nickname),
                artist=schemas.ArtistResponse(
                    id=post.artist.id, 
                    name=post.artist.stage_name or post.artist.group_name
                ),
                likes_count=likes_count,
                created_at=post.created_at,
                updated_at=post.updated_at,
            )
        )

    return result


@posts_router.get("/{post_id}", response_model=schemas.PostDetailResponse)
async def get_post(post_id: int):
    """포스트 상세 조회 (댓글 포함)"""
    post = await models.Post.filter(id=post_id).prefetch_related("user", "artist").first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    # 좋아요 수 계산
    likes_count = await models.Like.filter(post=post).count()

    # 댓글 조회
    comments = await models.Comment.filter(post=post).prefetch_related("user").order_by("created_at")
    comment_responses = [
        schemas.CommentResponse(
            id=comment.id,
            content=comment.content,
            user=schemas.UserResponse(
                id=comment.user.id, nickname=comment.user.nickname
            ),
            post_id=comment.post_id,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )
        for comment in comments
    ]

    return schemas.PostDetailResponse(
        id=post.id,
        content=post.content,
        user=schemas.UserResponse(id=post.user.id, nickname=post.user.nickname),
        artist=schemas.ArtistResponse(
            id=post.artist.id, 
            name=post.artist.stage_name or post.artist.group_name
        ),
        likes_count=likes_count,
        created_at=post.created_at,
        updated_at=post.updated_at,
        comments=comment_responses,
    )


@posts_router.put("/{post_id}", response_model=schemas.PostResponse)
async def update_post(
    post_id: int,
    post_in: schemas.PostUpdate,
    current_user: User = Depends(get_current_user),
):
    """포스트 수정"""
    post = await models.Post.filter(id=post_id).prefetch_related("user", "artist").first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    # 포스트 내용 업데이트
    post.content = post_in.post_content
    await post.save()

    # 좋아요 수 계산
    likes_count = await models.Like.filter(post=post).count()

    return schemas.PostResponse(
        id=post.id,
        content=post.content,
        user=schemas.UserResponse(id=post.user.id, nickname=post.user.nickname),
        artist=schemas.ArtistResponse(
            id=post.artist.id, 
            name=post.artist.stage_name or post.artist.group_name
        ),
        likes_count=likes_count,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@posts_router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, current_user: User = Depends(get_current_user)):
    """포스트 삭제"""
    post = await models.Post.get_or_none(id=post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    await post.delete()


# ----------------- Like 기능 -----------------
@posts_router.post("/{post_id}/like")
async def toggle_like(post_id: int, current_user: User = Depends(get_current_user)):
    """좋아요 토글"""
    post = await models.Post.get_or_none(id=post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    # 기존 좋아요 확인
    existing_like = await models.Like.get_or_none(post=post, user=current_user)

    if existing_like:
        # 좋아요 취소
        await existing_like.delete()
        liked = False
    else:
        # 좋아요 추가
        await models.Like.create(post=post, user=current_user)
        liked = True

    # 총 좋아요 수 계산
    likes_count = await models.Like.filter(post=post).count()

    return {"liked": liked, "likes_count": likes_count}


@posts_router.get("/{post_id}/likes", response_model=List[schemas.LikeResponse])
async def get_post_likes(post_id: int):
    """포스트 좋아요 목록 조회"""
    post = await models.Post.get_or_none(id=post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    likes = await models.Like.filter(post=post).prefetch_related("user").order_by("-created_at")

    return [
        schemas.LikeResponse(
            id=like.id,
            user=schemas.UserResponse(id=like.user.id, nickname=like.user.nickname),
            post_id=like.post_id,
            created_at=like.created_at,
        )
        for like in likes
    ]


# ----------------- Comment CRUD -----------------
@posts_router.post("/{post_id}/comments", response_model=schemas.CommentResponse)
async def create_comment(
    post_id: int,
    comment_in: schemas.CommentCreate,
    current_user: User = Depends(get_current_user),
):
    """댓글 생성"""
    post = await models.Post.get_or_none(id=post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    comment = await models.Comment.create(
        post=post,
        user=current_user,
        content=comment_in.comment_content,
    )
    await comment.fetch_related("user")

    return schemas.CommentResponse(
        id=comment.id,
        content=comment.content,
        user=schemas.UserResponse(
            id=comment.user.id, nickname=comment.user.nickname
        ),
        post_id=comment.post_id,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@posts_router.get("/{post_id}/comments", response_model=List[schemas.CommentResponse])
async def get_comments(post_id: int):
    """포스트 댓글 목록 조회"""
    post = await models.Post.get_or_none(id=post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    comments = await models.Comment.filter(post=post).prefetch_related("user").order_by("created_at")

    return [
        schemas.CommentResponse(
            id=comment.id,
            content=comment.content,
            user=schemas.UserResponse(
                id=comment.user.id, nickname=comment.user.nickname
            ),
            post_id=comment.post_id,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )
        for comment in comments
    ]


@posts_router.put("/comments/{comment_id}", response_model=schemas.CommentResponse)
async def update_comment(
    comment_id: int,
    comment_in: schemas.CommentUpdate,
    current_user: User = Depends(get_current_user),
):
    """댓글 수정"""
    comment = await models.Comment.filter(id=comment_id).prefetch_related("user").first()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    comment.content = comment_in.comment_content
    await comment.save()

    return schemas.CommentResponse(
        id=comment.id,
        content=comment.content,
        user=schemas.UserResponse(
            id=comment.user.id, nickname=comment.user.nickname
        ),
        post_id=comment.post_id,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@posts_router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int, current_user: User = Depends(get_current_user)
):
    """댓글 삭제"""
    comment = await models.Comment.get_or_none(id=comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    await comment.delete()
