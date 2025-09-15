from tortoise import fields

from app.core.mixins import TimestampMixin


class FanPost(TimestampMixin):
    """팬 포스트 모델 (구독한 유저만 작성 가능)"""

    id = fields.BigIntField(pk=True, description="팬 포스트 ID")
    user = fields.ForeignKeyField(
        "models.User", related_name="fan_posts", description="작성자"
    )
    artist = fields.ForeignKeyField(
        "models.Artist",
        related_name="fan_posts",
        description="관련 아티스트",
    )

    content = fields.TextField(description="게시글 내용")

    class Meta:
        table = "fan_post"


class FanPostComment(TimestampMixin):
    """팬 포스트 댓글"""

    id = fields.BigIntField(pk=True, description="댓글 ID")
    fan_post = fields.ForeignKeyField(
        "models.FanPost",
        related_name="comments",
        description="팬 포스트",
    )
    user = fields.ForeignKeyField(
        "models.User",
        related_name="fan_post_comments",
        description="작성자",
    )

    content = fields.CharField(max_length=500, description="댓글 내용")

    class Meta:
        table = "fan_post_comment"


class FanPostLike(TimestampMixin):
    """팬 포스트 좋아요"""

    id = fields.BigIntField(pk=True, description="좋아요 ID")
    fan_post = fields.ForeignKeyField(
        "models.FanPost",
        related_name="likes",
        description="팬 포스트",
    )
    user = fields.ForeignKeyField(
        "models.User",
        related_name="fan_post_likes",
        description="사용자",
    )

    class Meta:
        table = "fan_post_like"
        unique_together = [("fan_post", "user")]  # 중복 좋아요 방지


# 기존 Posts, Comments, Likes는 유지 (일반적인 게시글용)
class Posts(TimestampMixin):
    """일반 게시글 모델"""

    id = fields.BigIntField(pk=True, description="게시글 ID")
    user = fields.ForeignKeyField(
        "models.User", related_name="posts", description="작성자"
    )
    content = fields.TextField(null=True, description="게시글 내용")
    created_by = fields.CharField(max_length=100, description="작성자")
    updated_by = fields.CharField(max_length=100, null=True, description="수정자")

    class Meta:
        table = "posts"


class Comments(TimestampMixin):
    """일반 게시글 댓글"""

    id = fields.BigIntField(pk=True, description="댓글 ID")
    post = fields.ForeignKeyField(
        "models.Posts", related_name="comments", description="게시글"
    )
    user = fields.ForeignKeyField(
        "models.User", related_name="comments", description="작성자"
    )
    content = fields.CharField(max_length=200, description="댓글 내용")
    created_by = fields.CharField(max_length=100, description="작성자")
    updated_by = fields.CharField(max_length=100, null=True, description="수정자")

    class Meta:
        table = "comments"


class Likes(TimestampMixin):
    """일반 게시글 좋아요"""

    id = fields.BigIntField(pk=True, description="좋아요 ID")
    user = fields.ForeignKeyField(
        "models.User", related_name="likes", description="사용자"
    )
    post = fields.ForeignKeyField(
        "models.Posts", related_name="likes", description="게시글"
    )
    updated_at = fields.DatetimeField(auto_now=True, description="좋아요 시간")

    class Meta:
        table = "likes"
        unique_together = [("user", "post")]
