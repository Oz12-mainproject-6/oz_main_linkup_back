from datetime import date

from pydantic import BaseModel

from app.features.artists.models import ArtistType


class ArtistResponse(BaseModel):
    """아티스트 응답 스키마"""

    id: int
    stage_name: str | None = None
    group_name: str | None = None
    birthdate: date | None = None
    debut_date: date | None = None
    artist_type: ArtistType
    is_active: bool
    profile_image: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ArtistListResponse(BaseModel):
    """아티스트 리스트 응답 스키마 (간단 정보만)"""

    id: int
    name: str  # 표시용 이름 (stage_name 또는 group_name)
    profile_image: str | None = None  # 프로필 이미지 URL (호환성을 위해 유지)
    face_url: str | None = None  # Face 이미지 URL
    torso_url: str | None = None  # Torso 이미지 URL
    banner_url: str | None = None  # Banner 이미지 URL


class ArtistSubscriptionInfo(BaseModel):
    """구독 아티스트 정보 스키마"""

    id: int
    stage_name: str | None = None
    group_name: str | None = None
    artist_type: ArtistType
    is_subscribed: bool
    subscription_date: str | None = None


class ArtistListPaginationResponse(BaseModel):
    """아티스트 리스트 페이지네이션 응답 스키마"""

    artists: list[ArtistListResponse]
    total: int
    page: int
    limit: int
    has_next: bool
