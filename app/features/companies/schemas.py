from datetime import date, datetime

from pydantic import BaseModel, Field

from app.core.schemas import BaseQueryParams
from app.features.artists.models import ArtistType
from app.features.events.models import EventCategory, EventVisibility


class DashboardArtistInfo(BaseModel):
    """대시보드용 아티스트 정보"""

    id: int
    stage_name: str | None = None
    group_name: str | None = None
    artist_type: ArtistType
    birth_date: date | None = None
    debut_date: date | None = None
    is_active: bool
    event_count: int = 0  # 이번 달 이벤트 수
    face_url: str | None = None
    torso_url: str | None = None
    banner_url: str | None = None


class DashboardEventInfo(BaseModel):
    """대시보드용 이벤트 정보"""

    id: int
    title: str
    start_time: datetime
    end_time: datetime | None = None
    category: EventCategory
    artist_name: str
    artist_stage_name: str | None = None


class CompanyDashboardResponse(BaseModel):
    """소속사 대시보드 응답"""

    company_name: str
    artists: list[DashboardArtistInfo]
    recent_events: list[DashboardEventInfo]
    total_artists: int
    total_events: int


class EventCreateRequest(BaseModel):
    """이벤트 생성 요청"""

    artist_id: int
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    location: str | None = None
    category: EventCategory
    visibility: EventVisibility = EventVisibility.PUBLIC


class EventUpdateRequest(BaseModel):
    """이벤트 수정 요청"""

    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    location: str | None = None
    category: EventCategory | None = None
    visibility: EventVisibility | None = None


class EventResponse(BaseModel):
    """이벤트 응답"""

    id: int
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    location: str | None = None
    category: EventCategory
    visibility: EventVisibility
    is_active: bool
    artist_id: int
    artist_name: str
    artist_stage_name: str | None = None
    created_at: str
    updated_at: str


class CompanyEventsQueryParams(BaseQueryParams):
    """회사 이벤트 목록 쿼리 파라미터"""

    artist_id: int | None = Field(None, description="특정 아티스트 이벤트 필터")
    offset: int = Field(0, ge=0, description="오프셋")


class CompanyArtistsQueryParams(BaseQueryParams):
    """회사 아티스트 목록 쿼리 파라미터"""

    is_active: bool | None = Field(True, description="활동 상태 필터 (기본값: True)")
    offset: int = Field(0, ge=0, description="오프셋")

    # 아티스트는 기본 50개로 조정
    limit: int = Field(50, ge=1, le=100, description="조회할 아티스트 수")
