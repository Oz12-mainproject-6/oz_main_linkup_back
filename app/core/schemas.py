"""
공통 스키마 클래스들
"""

from pydantic import BaseModel, Field


class BaseQueryParams(BaseModel):
    """기본 쿼리 파라미터 - 페이지네이션"""

    limit: int = Field(20, ge=1, le=100, description="조회할 항목 수")
    page: int = Field(1, ge=1, description="페이지 번호 (1부터 시작)")
