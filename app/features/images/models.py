from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from tortoise import fields

from app.core.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.features.artists.models import Artist
    from app.features.events.models import Events
    from app.features.users.models import User


class ImageType(str, Enum):
    """이미지 타입"""

    FACE = "face"
    TORSO = "전체 사진"
    BANNER = "배너 사진"
    POST = "post"


class SharedImage(TimestampMixin):
    """공유 가능한 이미지 풀 (소속사가 업로드, 구독자가 사용)"""

    id = fields.BigIntField(pk=True, description="이미지 ID")

    # S3 정보
    url = fields.TextField(description="S3 이미지 URL")
    name = fields.CharField(max_length=255, null=True, description="원본 파일명")
    size = fields.BigIntField(null=True, description="파일 크기 (bytes)")
    content_type = fields.CharField(max_length=100, null=True, description="MIME 타입")

    # 업로더 정보
    uploaded_by: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User",
        related_name="uploaded_images",
        description="업로드한 사용자 (소속사)",
    )

    # 연관 엔티티 (어떤 아티스트/이벤트와 관련된 이미지인지)
    artist: fields.ForeignKeyRelation["Artist"] = fields.ForeignKeyField(
        "models.Artist",
        related_name="shared_images",
        null=True,
        description="관련 아티스트",
    )
    event: fields.ForeignKeyRelation["Events"] = fields.ForeignKeyField(
        "models.Events",
        related_name="shared_images",
        null=True,
        description="관련 이벤트",
    )

    # 이미지 타입
    image_type = fields.CharEnumField(
        ImageType,
        description="이미지 타입",
    )

    class Meta:
        table = "shared_image"
        indexes = [
            ("image_type",),  # image_type 단일 컬럼 인덱스
            (
                "artist",
                "image_type",
            ),  # artist + image_type 복합 인덱스 (자주 함께 쿼리됨)
        ]
