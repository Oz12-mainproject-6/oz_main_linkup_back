from tortoise import fields
from app.core.mixins import TimestampMixin
from app.features.users.models import User


class Artist(TimestampMixin):

    id = fields.BigIntField(pk=True, description="아티스트 ID")
    name = fields.CharField(max_length=200, unique=True, description="아티스트 이름")
    description = fields.TextField(null=True, description="아티스트 소개")

    class Meta:
        table = "artists"


class Subscription(TimestampMixin):
    """팬 → 아티스트 구독"""

    id = fields.BigIntField(pk=True, description="구독 ID")

    # 구독한 팬 (User, user_type=FAN)
    user = fields.ForeignKeyField(
        "models.User", related_name="subscriptions", description="팬 유저"
    )

    # 구독 대상 (Artist)
    artist = fields.ForeignKeyField(
        "models.Artist", related_name="subscribers", description="구독한 아티스트"
    )

    is_active = fields.BooleanField(default=True, description="구독 상태")

    class Meta:
        table = "subscription"
        unique_together = ("user", "artist")  # 중복 방지
