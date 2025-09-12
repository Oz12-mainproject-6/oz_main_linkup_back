from tortoise import fields
from app.core.mixins import TimestampMixin


class Posts(TimestampMixin):
    """게시글 모델"""
    
    id = fields.BigIntField(pk=True, description="게시글 ID")
    user = fields.ForeignKeyField("app.features.users.models.User", related_name="posts", description="작성자")
    content = fields.TextField(null=True, description="게시글 내용")
    created_by = fields.CharField(max_length=100, description="작성자")
    updated_by = fields.CharField(max_length=100, null=True, description="수정자")
    
    class Meta:
        table = "posts"


class Comments(TimestampMixin):
    """댓글 모델"""
    
    id = fields.BigIntField(pk=True, description="댓글 ID")
    post = fields.ForeignKeyField("app.features.posts.models.Posts", related_name="comments", description="게시글")
    user = fields.ForeignKeyField("app.features.users.models.User", related_name="comments", description="작성자")
    content = fields.CharField(max_length=200, description="댓글 내용")
    created_by = fields.CharField(max_length=100, description="작성자")
    updated_by = fields.CharField(max_length=100, null=True, description="수정자")
    
    class Meta:
        table = "comments"


class Likes(TimestampMixin):
    """좋아요 모델"""
    
    id = fields.BigIntField(pk=True, description="좋아요 ID")
    user = fields.ForeignKeyField("app.features.users.models.User", related_name="likes", description="사용자")
    post = fields.ForeignKeyField("app.features.posts.models.Posts", related_name="likes", description="게시글")
    updated_at = fields.DatetimeField(auto_now=True, description="좋아요 시간")
    
    class Meta:
        table = "likes"
        unique_together = [("user", "post")]  # 같은 사용자가 같은 게시글에 중복 좋아요 방지