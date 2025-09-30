from pydantic import BaseModel, Field

from app.core.schemas import BaseQueryParams
from app.features.notifications.models import SubscriptionType


class SubscriptionCreate(BaseModel):
    artist_id: int


class SubscriptionOut(BaseModel):
    id: int
    artist_id: int
    group_name: str | None = None
    stage_name: str | None = None
    is_active: bool
    subscription_type: SubscriptionType

    class Config:
        from_attributes = True


class SubscriptionWithImageOut(BaseModel):
    id: int
    artist_id: int
    group_name: str | None = None
    stage_name: str | None = None
    artist_image_url: str | None = None
    is_active: bool
    subscription_type: SubscriptionType

    class Config:
        from_attributes = True


class SubscriptionsQueryParams(BaseQueryParams):
    """구독 목록 조회 쿼리 파라미터"""
    
    include_image: bool = Field(False, description="아티스트 face 이미지 URL 포함 여부")
    group_name: str | None = Field(None, description="그룹명으로 필터링")
    stage_name: str | None = Field(None, description="활동명으로 필터링")
