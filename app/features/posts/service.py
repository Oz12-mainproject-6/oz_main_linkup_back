from fastapi import UploadFile

from app.core.exceptions import (
    ArtistNotFoundError,
    CommentNotFoundError,
    ForbiddenError,
    PostNotFoundError,
    UploadFailedError,
)
from app.core.s3 import S3Folders, s3_handler
from app.features.artists.models import Artist
from app.features.notifications.models import Subscription
from app.features.posts import models, schemas
from app.features.users.models import User


class PostService:
    """포스트 관련 비즈니스 로직"""

    @staticmethod
    async def get_likes_count(post: models.Post) -> int:
        """포스트 좋아요 수 조회 (탈퇴한 유저 제외)"""
        return await models.Like.filter(post=post, user__deleted_at__isnull=True).count()

    @staticmethod
    async def get_comments_count(post: models.Post) -> int:
        """포스트 댓글 수 조회 (탈퇴한 유저 제외)"""
        return await models.Comment.filter(post=post, user__deleted_at__isnull=True).count()

    @staticmethod
    async def build_post_response(post: models.Post) -> schemas.PostResponse:
        """포스트 응답 객체 생성"""
        likes_count = await PostService.get_likes_count(post)
        comments_count = await PostService.get_comments_count(post)

        return schemas.PostResponse(
            id=post.id,
            content=post.content,
            image_url=post.image_url,
            user=schemas.UserResponse(id=post.user.id, nickname=post.user.nickname),
            artist=schemas.ArtistResponse(
                id=post.artist.id,
                name=post.artist.stage_name or post.artist.group_name,
            ),
            likes_count=likes_count,
            comments_count=comments_count,
            created_at=post.created_at,
            updated_at=post.updated_at,
        )

    @staticmethod
    async def build_comment_response(
        comment: models.Comment,
    ) -> schemas.CommentResponse:
        """댓글 응답 객체 생성"""
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

    @staticmethod
    async def validate_artist_exists(artist_id: int) -> Artist:
        """아티스트 존재 확인"""
        artist = await Artist.get_or_none(id=artist_id)
        if not artist:
            raise ArtistNotFoundError()
        return artist

    @staticmethod
    async def validate_post_exists(post_id: int) -> models.Post:
        """포스트 존재 확인 (관련 객체 포함)"""
        post = (
            await models.Post.filter(id=post_id)
            .prefetch_related("user", "artist")
            .first()
        )
        if not post:
            raise PostNotFoundError()
        return post

    @staticmethod
    async def validate_comment_exists(comment_id: int) -> models.Comment:
        """댓글 존재 확인 (관련 객체 포함)"""
        comment = (
            await models.Comment.filter(id=comment_id).prefetch_related("user").first()
        )
        if not comment:
            raise CommentNotFoundError()
        return comment

    @staticmethod
    def validate_user_permission(
        obj_user_id: int, current_user: User, action: str = "수정"
    ):
        """사용자 권한 확인"""
        if obj_user_id != current_user.id:
            raise ForbiddenError(f"작성자만 {action}할 수 있습니다")

    @staticmethod
    async def upload_post_image(post_image: UploadFile) -> str | None:
        """포스트 이미지 업로드"""
        if not post_image or not post_image.filename:
            return None

        image_url = await s3_handler.upload_file(post_image, S3Folders.POST)
        if not image_url:
            raise UploadFailedError("이미지 업로드에 실패했습니다")
        return image_url

    @staticmethod
    async def create_post(
        artist_id: int,
        post_content: str,
        post_image: UploadFile | None,
        current_user: User,
    ) -> dict:
        """포스트 생성"""
        artist = await PostService.validate_artist_exists(artist_id)
        image_url = await PostService.upload_post_image(post_image)

        post = await models.Post.create(
            user=current_user,
            artist=artist,
            content=post_content,
            image_url=image_url,
        )

        return {"detail": "포스트가 성공적으로 생성되었습니다.", "post_id": post.id}

    @staticmethod
    async def get_posts(
        limit: int,
        page: int,
        artist_id: int | None = None,
        is_active: bool | None = None,
    ) -> list[schemas.PostResponse]:
        """포스트 목록 조회"""
        # 탈퇴한 유저의 포스트 제외
        query = models.Post.filter(user__deleted_at__isnull=True).prefetch_related("user", "artist")

        if is_active:
            subscribed_artist_ids = await Subscription.filter(
                is_active=True
            ).values_list("artist_id", flat=True)
            query = query.filter(artist_id__in=subscribed_artist_ids)

        if artist_id:
            query = query.filter(artist_id=artist_id)

        # offset 계산
        offset = (page - 1) * limit

        posts = await query.offset(offset).limit(limit).order_by("-created_at")

        result = []
        for post in posts:
            post_response = await PostService.build_post_response(post)
            result.append(post_response)

        return result

    @staticmethod
    async def get_post_detail(post_id: int) -> schemas.PostDetailResponse:
        """포스트 상세 조회 (댓글 포함)"""
        post = await PostService.validate_post_exists(post_id)
        likes_count = await PostService.get_likes_count(post)

        # 탈퇴한 유저의 댓글 제외
        comments = (
            await models.Comment.filter(post=post, user__deleted_at__isnull=True)
            .prefetch_related("user")
            .order_by("created_at")
        )
        comment_responses = [
            await PostService.build_comment_response(comment) for comment in comments
        ]

        return schemas.PostDetailResponse(
            id=post.id,
            content=post.content,
            image_url=post.image_url,
            user=schemas.UserResponse(id=post.user.id, nickname=post.user.nickname),
            artist=schemas.ArtistResponse(
                id=post.artist.id,
                name=post.artist.stage_name or post.artist.group_name,
            ),
            likes_count=likes_count,
            created_at=post.created_at,
            updated_at=post.updated_at,
            comments=comment_responses,
        )

    @staticmethod
    async def update_post(
        post_id: int, post_content: str, current_user: User
    ) -> schemas.PostResponse:
        """포스트 수정"""
        post = await PostService.validate_post_exists(post_id)
        PostService.validate_user_permission(post.user_id, current_user)

        post.content = post_content
        await post.save()

        return await PostService.build_post_response(post)

    @staticmethod
    async def delete_post(post_id: int, current_user: User):
        """포스트 삭제"""
        post = await models.Post.get_or_none(id=post_id)
        if not post:
            raise PostNotFoundError()

        PostService.validate_user_permission(post.user_id, current_user, "삭제")

        if post.image_url:
            s3_handler.delete_file(post.image_url)

        await post.delete()

    @staticmethod
    async def toggle_like(post_id: int, current_user: User) -> dict:
        """좋아요 토글"""
        post = await models.Post.get_or_none(id=post_id)
        if not post:
            raise PostNotFoundError()

        existing_like = await models.Like.get_or_none(post=post, user=current_user)

        if existing_like:
            await existing_like.delete()
            liked = False
        else:
            await models.Like.create(post=post, user=current_user)
            liked = True

        likes_count = await PostService.get_likes_count(post)
        return {"liked": liked, "likes_count": likes_count}

    @staticmethod
    async def get_post_likes(post_id: int) -> list[schemas.LikeResponse]:
        """포스트 좋아요 목록 조회"""
        post = await models.Post.get_or_none(id=post_id)
        if not post:
            raise PostNotFoundError()

        # 탈퇴한 유저의 좋아요 제외
        likes = (
            await models.Like.filter(post=post, user__deleted_at__isnull=True)
            .prefetch_related("user")
            .order_by("-created_at")
        )

        return [
            schemas.LikeResponse(
                id=like.id,
                user=schemas.UserResponse(id=like.user.id, nickname=like.user.nickname),
                post_id=like.post_id,
                created_at=like.created_at,
            )
            for like in likes
        ]

    @staticmethod
    async def create_comment(
        post_id: int, comment_content: str, current_user: User
    ) -> schemas.CommentResponse:
        """댓글 생성"""
        post = await models.Post.get_or_none(id=post_id)
        if not post:
            raise PostNotFoundError()

        comment = await models.Comment.create(
            post=post,
            user=current_user,
            content=comment_content,
        )
        await comment.fetch_related("user")

        return await PostService.build_comment_response(comment)

    @staticmethod
    async def get_comments(post_id: int) -> list[schemas.CommentResponse]:
        """포스트 댓글 목록 조회"""
        post = await models.Post.get_or_none(id=post_id)
        if not post:
            raise PostNotFoundError()

        # 탈퇴한 유저의 댓글 제외
        comments = (
            await models.Comment.filter(post=post, user__deleted_at__isnull=True)
            .prefetch_related("user")
            .order_by("created_at")
        )

        return [
            await PostService.build_comment_response(comment) for comment in comments
        ]

    @staticmethod
    async def update_comment(
        comment_id: int, comment_content: str, current_user: User
    ) -> schemas.CommentResponse:
        """댓글 수정"""
        comment = await PostService.validate_comment_exists(comment_id)
        PostService.validate_user_permission(comment.user_id, current_user)

        comment.content = comment_content
        await comment.save()

        return await PostService.build_comment_response(comment)

    @staticmethod
    async def delete_comment(comment_id: int, current_user: User):
        """댓글 삭제"""
        comment = await models.Comment.get_or_none(id=comment_id)
        if not comment:
            raise CommentNotFoundError()

        PostService.validate_user_permission(comment.user_id, current_user, "삭제")
        await comment.delete()
