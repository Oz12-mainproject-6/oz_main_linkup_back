from datetime import datetime
from tortoise.models import Model
from tortoise import fields


class TimestampMixin(Model):
    """공통 타임스탬프 필드를 제공하는 Mixin"""
    
    created_at = fields.DatetimeField(auto_now_add=True, description="생성일시")
    updated_at = fields.DatetimeField(auto_now=True, description="수정일시")
    
    class Meta:
        abstract = True