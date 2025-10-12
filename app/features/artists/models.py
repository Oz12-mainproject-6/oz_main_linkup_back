from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from tortoise import fields

from app.core.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.features.users.models import Company


class ArtistType(str, Enum):
    """아티스트 타입"""

    INDIVIDUAL = "individual"
    GROUP = "group"


class Artist(TimestampMixin):
    """아티스트 모델 (그룹/멤버/솔로 통합)"""

    id = fields.BigIntField(pk=True, description="아티스트 ID")
    company: fields.ForeignKeyRelation["Company"] = fields.ForeignKeyField(
        "models.Company",
        related_name="artists",
        description="소속사",
    )

    # 기본 정보
    stage_name = fields.CharField(
        max_length=200, null=True, description="개인 예명 (개인 아티스트만)"
    )
    group_name = fields.CharField(
        max_length=200, null=True, description="그룹명 (그룹만)"
    )
    birthdate = fields.DateField(null=True, description="생년월일")
    debut_date = fields.DateField(null=True, description="데뷔일")

    # 타입 및 관계
    artist_type = fields.CharEnumField(
        ArtistType,
        description="아티스트 타입",
    )
    parent_group: fields.ForeignKeyRelation["Artist"] = fields.ForeignKeyField(
        "models.Artist",
        related_name="members",
        null=True,
        description="소속 그룹 (멤버인 경우만)",
    )

    # 상태
    is_active = fields.BooleanField(default=True, description="활동 상태")

    class Meta:
        table = "artist"
