from tortoise import fields

from app.core.mixins import TimestampMixin


class Post(TimestampMixin):
    """포스트 모델 (팬 포스트)"""

    id = fields.BigIntField(pk=True, description="포스트 ID")
    user = fields.ForeignKeyField(
        "models.User", related_name="posts", description="작성자"
    )
    artist = fields.ForeignKeyField(
        "models.Artist",
        related_name="posts",
        description="관련 아티스트",
    )

    content = fields.TextField(description="게시글 내용")

    class Meta:
        table = "post"


class Comment(TimestampMixin):
    """포스트 댓글"""

    id = fields.BigIntField(pk=True, description="댓글 ID")
    post = fields.ForeignKeyField(
        "models.Post",
        related_name="comments",
        description="포스트",
    )
    user = fields.ForeignKeyField(
        "models.User",
        related_name="comments",
        description="작성자",
    )

    content = fields.CharField(max_length=500, description="댓글 내용")

    class Meta:
        table = "comment"


class Like(TimestampMixin):
    """포스트 좋아요"""

    id = fields.BigIntField(pk=True, description="좋아요 ID")
    post = fields.ForeignKeyField(
        "models.Post",
        related_name="likes",
        description="포스트",
    )
    user = fields.ForeignKeyField(
        "models.User",
        related_name="likes",
        description="사용자",
    )

    class Meta:
        table = "like"
        unique_together = [("post", "user")]
