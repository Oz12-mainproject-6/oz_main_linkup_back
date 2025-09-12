from tortoise import fields
from app.core.mixins import TimestampMixin


class User(TimestampMixin):
    """사용자 모델 (일반 유저 + 소속사 계정)"""
    
    id = fields.BigIntField(pk=True, description="사용자 ID")
    email = fields.CharField(max_length=200, unique=True, description="이메일")
    password = fields.CharField(max_length=200, description="비밀번호")
    phone_number = fields.CharField(max_length=20, null=True, description="전화번호")
    nickname = fields.CharField(max_length=50, null=True, description="별명")
    
    # 사용자 타입 구분
    user_type = fields.CharField(
        max_length=20, 
        default="fan", 
        description="사용자 타입 (fan: 일반 팬, company: 소속사)"
    )
    
    # 알림 설정
    push_notification_enabled = fields.BooleanField(default=True, description="푸시 알림 활성화")
    in_app_notification_enabled = fields.BooleanField(default=True, description="앱 내 알림 활성화")
    
    # 소셜 로그인
    oauth_provider = fields.CharField(max_length=50, null=True, description="소셜 로그인 제공자")
    oauth_id = fields.CharField(max_length=200, null=True, description="소셜 로그인 ID")
    
    # 기타
    last_login_at = fields.DatetimeField(null=True, description="마지막 로그인 시간")
    deleted_at = fields.DatetimeField(null=True, description="삭제 시간")
    
    class Meta:
        table = "user"
        unique_together = [("oauth_provider", "oauth_id")]


class Company(TimestampMixin):
    """소속사 모델"""
    
    id = fields.BigIntField(pk=True, description="소속사 ID")
    user = fields.OneToOneField("app.features.users.models.User", related_name="company_profile", description="소속사 계정")
    name = fields.CharField(max_length=200, description="소속사명")
    business_number = fields.CharField(max_length=50, null=True, description="사업자등록번호")
    contact_email = fields.CharField(max_length=200, null=True, description="담당자 이메일")
    contact_phone = fields.CharField(max_length=20, null=True, description="담당자 전화번호")
    address = fields.TextField(null=True, description="주소")
    description = fields.TextField(null=True, description="소속사 소개")
    
    class Meta:
        table = "company"