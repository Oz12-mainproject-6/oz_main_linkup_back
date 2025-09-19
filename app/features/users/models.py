import secrets
from datetime import UTC, datetime, timedelta
from enum import Enum

from tortoise import fields

from app.core.mixins import TimestampMixin

class UserType(str, Enum):
    """사용자 타입"""

    FAN = "fan"
    COMPANY = "company"


class User(TimestampMixin):
    """사용자 모델 (일반 유저 + 소속사 계정)"""

    id = fields.BigIntField(pk=True, description="사용자 ID")
    email = fields.CharField(max_length=200, unique=True, description="이메일")
    password = fields.CharField(max_length=200, description="비밀번호")
    phone_number = fields.CharField(max_length=20, null=True, description="전화번호")
    nickname = fields.CharField(max_length=50, null=True, description="별명")

    # 사용자 타입 구분
    user_type = fields.CharEnumField(
        UserType,
        default=UserType.FAN,
        description="사용자 타입",
    )

    # 알림 설정
    push_notification_enabled = fields.BooleanField(
        default=True, description="푸시 알림 활성화"
    )
    in_app_notification_enabled = fields.BooleanField(
        default=True, description="앱 내 알림 활성화"
    )

    # 소셜 로그인
    oauth_provider = fields.CharField(
        max_length=50, null=True, description="소셜 로그인 제공자"
    )
    oauth_id = fields.CharField(max_length=200, null=True, description="소셜 로그인 ID")

    # 이메일 인증
    is_email_verified = fields.BooleanField(
        default=False, description="이메일 인증 여부"
    )

    # 기타
    last_login_at = fields.DatetimeField(null=True, description="마지막 로그인 시간")
    deleted_at = fields.DatetimeField(null=True, description="삭제 시간")

    class Meta:
        table = "user"
        unique_together = [("oauth_provider", "oauth_id")]


class Company(TimestampMixin):
    """소속사 모델"""

    id = fields.BigIntField(pk=True, description="소속사 ID")
    user = fields.OneToOneField(
        "models.User",
        related_name="company_profile",
        description="소속사 계정",
    )
    name = fields.CharField(max_length=200, description="소속사명")
    business_number = fields.CharField(
        max_length=50, null=True, description="사업자등록번호"
    )
    contact_email = fields.CharField(
        max_length=200, null=True, description="담당자 이메일"
    )
    contact_phone = fields.CharField(
        max_length=20, null=True, description="담당자 전화번호"
    )
    address = fields.TextField(null=True, description="주소")
    description = fields.TextField(null=True, description="소속사 소개")

    class Meta:
        table = "company"


class EmailVerification(TimestampMixin):
    """이메일 인증 모델"""

    id = fields.BigIntField(pk=True, description="인증 ID")
    email = fields.CharField(max_length=200, description="인증할 이메일")
    code = fields.CharField(max_length=6, description="인증 코드")
    expires_at = fields.DatetimeField(description="만료 시간")
    is_used = fields.BooleanField(default=False, description="사용 여부")

    class Meta:
        table = "email_verification"

    @classmethod
    async def create_verification_code(cls, email: str) -> "EmailVerification":
        """이메일 인증 코드 생성"""
        # 기존 미사용 인증 코드 삭제
        await cls.filter(email=email, is_used=False).delete()

        # 6자리 랜덤 숫자 생성
        code = f"{secrets.randbelow(1000000):06d}"

        # 5분 후 만료
        expires_at = datetime.now(UTC) + timedelta(minutes=5)

        return await cls.create(email=email, code=code, expires_at=expires_at)

    async def is_valid(self) -> bool:
        """인증 코드 유효성 검사"""
        if self.is_used:
            return False
        if datetime.now(UTC) > self.expires_at:
            return False
        return True

    async def mark_as_used(self):
        """인증 코드를 사용됨으로 표시"""
        self.is_used = True
        await self.save()