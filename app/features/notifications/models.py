from tortoise import fields

from app.core.mixins import TimestampMixin


class Notifications(TimestampMixin):
    """알림 모델"""

    id = fields.BigIntField(pk=True, description="알림 ID")
    user = fields.ForeignKeyField(
        "models.User",
        related_name="notifications",
        description="사용자",
    )
    type = fields.CharField(max_length=50, description="알림 타입")
    message = fields.CharField(max_length=200, null=True, description="알림 메시지")
    entity_type = fields.CharField(
        max_length=50, null=True, description="관련 엔티티 타입"
    )
    entity_id = fields.BigIntField(null=True, description="관련 엔티티 ID")
    read_at = fields.DatetimeField(null=True, description="읽은 시간")
    url = fields.CharField(max_length=255, null=True, description="알림 관련 URL")

    class Meta:
        table = "notifications"


class Subscription(TimestampMixin):
    """구독 모델"""

    id = fields.BigIntField(pk=True, description="구독 ID")
    user = fields.ForeignKeyField(
        "models.User",
        related_name="subscriptions",
        description="구독자",
    )
    artist = fields.ForeignKeyField(
        "models.Artist",
        related_name="subscribers",
        description="아티스트",
    )

    class Meta:
        table = "subscription"
        unique_together = [
            ("user", "artist")
        ]  # 같은 사용자가 같은 아티스트를 중복 구독 방지
