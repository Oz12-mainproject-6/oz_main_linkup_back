from tortoise import fields
from app.core.mixins import TimestampMixin


class Events(TimestampMixin):
    """이벤트 모델"""
    
    id = fields.BigIntField(pk=True, description="이벤트 ID")
    artist = fields.ForeignKeyField("app.features.artists.models.Artist", related_name="events", description="아티스트 ID")
    title = fields.CharField(max_length=200, description="이벤트 제목")
    description = fields.TextField(null=True, description="이벤트 설명")
    start_time = fields.DatetimeField(description="시작 시간")
    end_time = fields.DatetimeField(null=True, description="종료 시간")
    category = fields.CharField(max_length=50, description="카테고리")
    location = fields.CharField(max_length=200, null=True, description="위치")
    recurrence = fields.CharField(max_length=50, null=True, description="반복 주기")
    visibility = fields.CharField(max_length=20, default="public", description="공개 여부")
    priority = fields.CharField(max_length=20, default="normal", description="우선순위")
    
    class Meta:
        table = "events"