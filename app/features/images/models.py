from tortoise import fields
from app.core.mixins import TimestampMixin


class Images(TimestampMixin):
    """이미지 모델 - S3 URL 저장"""
    
    id = fields.BigIntField(pk=True, description="이미지 ID")
    url = fields.TextField(description="S3 이미지 URL")
    name = fields.CharField(max_length=255, null=True, description="파일명")
    size = fields.BigIntField(null=True, description="파일 크기 (bytes)")
    content_type = fields.CharField(max_length=100, null=True, description="MIME 타입")
    
    # 이미지와 연관된 엔티티 정보
    entity_type = fields.CharField(max_length=50, description="연관 엔티티 타입 (artist, user, event 등)")
    entity_id = fields.BigIntField(description="연관 엔티티 ID")
    
    class Meta:
        table = "images"