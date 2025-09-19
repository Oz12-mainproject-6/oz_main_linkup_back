from enum import Enum

from tortoise import fields

from app.core.mixins import TimestampMixin


class EventCategory(str, Enum):
    """이벤트 카테고리"""

    CONCERT = "concert"
    FANMEETING = "fanmeeting"
    SHOWCASE = "showcase"
    FESTIVAL = "festival"
    AWARD_SHOW = "award_show"
    TV_SHOW = "tv_show"
    BROADCAST = "broadcast"
    PHOTOSHOOT = "photoshoot"
    INTERVIEW = "interview"
    RELEASE = "release"
    OTHER = "other"


class EventVisibility(str, Enum):
    """이벤트 공개 설정"""

    PUBLIC = "public"
    PRIVATE = "private"
    SUBSCRIBERS_ONLY = "subscribers_only"


class Events(TimestampMixin):
    """이벤트 모델"""

    id = fields.BigIntField(pk=True, description="이벤트 ID")
    artist = fields.ForeignKeyField(
        "models.Artist",  # ✅ 이렇게 해야 함
        related_name="events",
        description="아티스트",
    )
    parent_group = fields.ForeignKeyField(
        "models.Artist",
        related_name="events",
        description="그룹 아티스트 id",
    )

    title = fields.CharField(max_length=200, description="이벤트 제목")
    description = fields.TextField(null=True, description="이벤트 설명")
    start_time = fields.DatetimeField(description="시작 시간")
    end_time = fields.DatetimeField(null=True, description="종료 시간")
    location = fields.CharField(max_length=200, null=True, description="위치")

    # 이벤트 카테고리
    category = fields.CharEnumField(
        EventCategory,
        description="이벤트 카테고리",
    )

    # 알림 관련 (간단한 정책: 등록 즉시 + 1시간 전)
    instant_notification_sent = fields.BooleanField(
        default=False, description="등록 즉시 알림 발송 여부"
    )
    one_hour_notification_sent = fields.BooleanField(
        default=False, description="1시간 전 알림 발송 여부"
    )

    # 기타
    visibility = fields.CharEnumField(
        EventVisibility,
        default=EventVisibility.PUBLIC,
        description="공개 설정",
    )
    is_active = fields.BooleanField(default=True, description="활성 상태")

    class Meta:
        table = "events"
