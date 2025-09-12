from tortoise import fields
from app.core.mixins import TimestampMixin


class User(TimestampMixin):
    """사용자 모델"""
    
    id = fields.BigIntField(pk=True, description="사용자 ID")
    email = fields.CharField(max_length=200, unique=True, description="이메일")
    password = fields.CharField(max_length=200, description="비밀번호")
    phone_number = fields.CharField(max_length=20, null=True, description="전화번호")
    nickname = fields.CharField(max_length=50, null=True, description="별명")
    role = fields.CharField(max_length=20, default="user", description="역할 (admin, user, super_admin)")
    oauth_provider = fields.CharField(max_length=50, null=True, description="소셜 로그인 제공자")
    oauth_id = fields.CharField(max_length=200, null=True, description="소셜 로그인 ID")
    last_login_at = fields.DatetimeField(null=True, description="마지막 로그인 시간")
    deleted_at = fields.DatetimeField(null=True, description="삭제 시간")
    
    class Meta:
        table = "user"
        unique_together = [("oauth_provider", "oauth_id")]  # 소셜 로그인 중복 방지