import uuid
from typing import Optional
from datetime import datetime


def generate_uuid() -> str:
    """UUID 생성"""
    return str(uuid.uuid4())


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """날짜시간 포맷팅"""
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def validate_image_extension(filename: str) -> bool:
    """이미지 파일 확장자 검증"""
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    return any(filename.lower().endswith(ext) for ext in allowed_extensions)