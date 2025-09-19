from enum import Enum

from tortoise import fields

from app.core.mixins import TimestampMixin


class ArtistType(str, Enum):
    """아티스트 타입"""

    INDIVIDUAL = "individual"
    GROUP = "group"


class ArtistRole(str, Enum):
    """아티스트 역할"""

    LEADER = "leader"
    MAIN_VOCAL = "main_vocal"
    LEAD_VOCAL = "lead_vocal"
    SUB_VOCAL = "sub_vocal"
    MAIN_RAPPER = "main_rapper"
    LEAD_RAPPER = "lead_rapper"
    SUB_RAPPER = "sub_rapper"
    MAIN_DANCER = "main_dancer"
    LEAD_DANCER = "lead_dancer"
    SUB_DANCER = "sub_dancer"
    VISUAL = "visual"
    MAKNAE = "maknae"
    SOLO = "solo"


class Artist(TimestampMixin):
    """아티스트 모델 (그룹/멤버/솔로 통합)"""

    id = fields.BigIntField(pk=True, description="아티스트 ID")
    company = fields.ForeignKeyField(
        "models.Company",
        related_name="artists",
        description="소속사",
    )

    # 기본 정보
    real_name = fields.CharField(max_length=200, description="실명")
    stage_name = fields.CharField(max_length=200, null=True, description="예명/그룹명")
    birthdate = fields.DateField(null=True, description="생년월일")
    gender = fields.CharField(max_length=200, null=True, description="성별")
    role = fields.CharEnumField(
        ArtistRole,
        null=True,
        description="역할",
    )
    mbti = fields.CharField(max_length=4, null=True, description="MBTI")
    height = fields.CharField(max_length=255, null=True, description="키")
    nickname = fields.CharField(max_length=200, null=True, description="별명")
    email = fields.CharField(max_length=200, null=True, unique=True, description="이메일")
    debut_date = fields.DateField(null=True, description="데뷔일")

    # 타입 및 관계
    artist_type = fields.CharEnumField(
        ArtistType,
        description="아티스트 타입",
    )
    parent_group = fields.ForeignKeyField(
        "models.Artist",
        related_name="members",
        null=True,
        description="소속 그룹 (멤버인 경우만)",
    )

    # 그룹 전용 필드
    member_count = fields.IntField(null=True, description="멤버 수 (그룹인 경우)")

    # 상태
    is_active = fields.BooleanField(default=True, description="활동 상태")

    class Meta:
        table = "artist"
