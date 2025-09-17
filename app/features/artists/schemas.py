from datetime import date

from pydantic import BaseModel

from app.features.artists.models import ArtistRole, ArtistType


class ArtistResponse(BaseModel):
    """아티스트 응답 스키마"""

    id: int
    real_name: str
    stage_name: str | None = None
    birthdate: date | None = None
    gender: str | None = None
    role: ArtistRole | None = None
    mbti: str | None = None
    height: str | None = None
    nickname: str | None = None
    debut_date: date | None = None
    artist_type: ArtistType
    member_count: int | None = None
    is_active: bool
    profile_image: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ArtistListResponse(BaseModel):
    """아티스트 리스트 응답 스키마 (간단 정보만)"""

    id: int
    name: str  # 표시용 이름 (stage_name 우선, 없으면 real_name)
    profile_image: str | None = None  # 프로필 이미지 URL


class ArtistSubscriptionInfo(BaseModel):
    """구독 아티스트 정보 스키마"""

    id: int
    real_name: str
    stage_name: str | None = None
    artist_type: ArtistType
    is_subscribed: bool
    subscription_date: str | None = None
