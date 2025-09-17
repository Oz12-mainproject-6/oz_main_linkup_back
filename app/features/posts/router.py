from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.features.posts import models, schemas
from app.features.users.dependencies import get_current_user
from app.features.users.models import User

router = APIRouter(prefix="/posts", tags=["Posts"])


# ----------------- Post CRUD -----------------
@router.post("/", response_model=schemas.PostResponse)
async def create_post(post_in: schemas.PostCreate, current_user: User = Depends(get_current_user)):
    post = await models.Post.create(
        user_id=current_user.id,
        artist_id=post_in.artist_id,
        content=post_in.content,
    )
    await post.fetch_related("user", "artist")
    likes_count = await post.likes.all().count()
    return schemas.PostResponse(
        id=post.id,
        user=schemas.UserResponse.from_orm(post.user),
        artist=schemas.ArtistResponse.from_orm(post.artist),
        content=post.content,
        likes_count=likes_count,
    )


@router.get("/{post_id}", response_model=schemas.PostResponse)
async def get_post(post_id: int):
    post = await models.Post.get_or_none(id=post_id).prefetch_related("user", "artist", "likes")
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    likes_count = await post.likes.all().count()
    return schemas.PostResponse(
        id=post.id,
        user=schemas.UserResponse.from_orm(post.user),
        artist=schemas.ArtistResponse.from_orm(post.artist),
        content=post.content,
        likes_count=likes_count,
    )


@router.put("/{post_id}", response_model=schemas.PostResponse)
async def update_post(post_id: int, post_in: schemas.PostUpdate, current_user: User = Depends(get_current_user)):
    post = await models.Post.get_or_none(id=post_id).prefetch_related("user", "artist", "likes")
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    post.content = post_in.content
    await post.save()
    likes_count = await post.likes.all().count()
    return schemas.PostResponse(
        id=post.id,
        user=schemas.UserResponse.from_orm(post.user),
        artist=schemas.ArtistResponse.from_orm(post.artist),
        content=post.content,
        likes_count=likes_count,
    )


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, current_user: User = Depends(get_current_user)):
    post = await models.Post.get_or_none(id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    await post.delete()
    return


# ----------------- Like 토글 -----------------
@router.post("/{post_id}/like", response_model=schemas.PostResponse)
async def toggle_like(post_id: int, current_user: User = Depends(get_current_user)):
    post = await models.Post.get_or_none(id=post_id).prefetch_related("user", "artist", "likes")
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    like = await models.Like.get_or_none(post_id=post.id, user_id=current_user.id)
    if like:
        await like.delete()
    else:
        await models.Like.create(post_id=post.id, user_id=current_user.id)

    likes_count = await post.likes.all().count()
    return schemas.PostResponse(
        id=post.id,
        user=schemas.UserResponse.from_orm(post.user),
        artist=schemas.ArtistResponse.from_orm(post.artist),
        content=post.content,
        likes_count=likes_count,
    )


# ----------------- Comment CRUD -----------------
@router.post("/{post_id}/comments", response_model=schemas.CommentResponse)
async def create_comment(post_id: int, comment_in: schemas.CommentCreate, current_user: User = Depends(get_current_user)):
    post = await models.Post.get_or_none(id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = await models.Comment.create(
        post_id=post.id,
        user_id=current_user.id,
        content=comment_in.content,
    )
    await comment.fetch_related("user")
    return schemas.CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        user=schemas.UserResponse.from_orm(comment.user),
        content=comment.content,
    )


@router.get("/{post_id}/comments", response_model=List[schemas.CommentResponse])
async def get_comments(post_id: int):
    post = await models.Post.get_or_none(id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    comments = await models.Comment.filter(post_id=post.id).prefetch_related("user")
    return [
        schemas.CommentResponse(
            id=c.id,
            post_id=c.post_id,
            user=schemas.UserResponse.from_orm(c.user),
            content=c.content,
        )
        for c in comments
    ]


@router.put("/comments/{comment_id}", response_model=schemas.CommentResponse)
async def update_comment(comment_id: int, comment_in: schemas.CommentUpdate, current_user: User = Depends(get_current_user)):
    comment = await models.Comment.get_or_none(id=comment_id).prefetch_related("user")
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    comment.content = comment_in.content
    await comment.save()
    return schemas.CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        user=schemas.UserResponse.from_orm(comment.user),
        content=comment.content,
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: int, current_user: User = Depends(get_current_user)):
    comment = await models.Comment.get_or_none(id=comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    await comment.delete()
    return
