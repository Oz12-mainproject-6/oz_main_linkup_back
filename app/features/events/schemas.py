from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from app.core.schemas import BaseQueryParams
from app.features.companies.router import EventCreateRequest
from app.features.events.models import EventCategory, EventVisibility

KST = ZoneInfo("Asia/Seoul")


class EventBase(BaseModel):
    """이벤트 기본 스키마"""

    title: str = Field(..., min_length=1, max_length=200, description="이벤트 제목")
    description: str | None = Field(None, description="이벤트 설명")
    start_time: datetime = Field(..., description="시작 시간")
    end_time: datetime | None = Field(None, description="종료 시간")
    location: str | None = Field(None, max_length=200, description="위치")
    category: EventCategory = Field(..., description="이벤트 카테고리")
    visibility: EventVisibility = Field(EventVisibility.PUBLIC, description="공개 설정")


class EventResponse(EventBase):
    """이벤트 응답 스키마"""

    id: int
    artist_id: int
    instant_notification_sent: bool
    one_hour_notification_sent: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """이벤트 목록 응답 스키마"""

    events: list[EventResponse]
    total: int
    page: int
    size: int


class FileUploadResponse(BaseModel):
    """파일 업로드 응답 스키마"""

    message: str
    total_processed: int
    successful: int
    failed: int
    errors: list[str] = []


class BulkEventCreate(BaseModel):
    """일괄 이벤트 생성 스키마"""

    events: list[EventCreateRequest]

    class Config:
        arbitrary_types_allowed = True


class IdolInfo(BaseModel):
    id: int
    group_id: int | None = None
    name: str
    image_url: str | None = None


class EventOut(BaseModel):
    id: int
    article_id: int | None = None
    category: str | None = None
    allday: bool | None = None
    dtstart: datetime
    extra: str | None = None
    created_at: datetime
    idol: IdolInfo


class EventsQueryParams(BaseQueryParams):
    """이벤트 목록 조회 쿼리 파라미터"""
    
    artist_parent_group: int | None = Field(None, description="그룹 ID")
    artist_id: int | None = Field(None, description="아티스트 ID")
    category: EventCategory | None = Field(None, description="일정 종류")
    visibility: EventVisibility | None = Field(None, description="공개범위")
    start_date: str | None = Field(None, description="YYYY-MM-DD format")
    end_date: str | None = Field(None, description="YYYY-MM-DD format")


class SubscribedEventsQueryParams(BaseQueryParams):
    """구독 이벤트 목록 조회 쿼리 파라미터"""
    
    artist_parent_group: int | None = Field(None, description="그룹 ID")
    artist_id: int | None = Field(None, description="아티스트 ID")
    category: EventCategory | None = Field(None, description="일정 종류")
    visibility: EventVisibility | None = Field(None, description="공개범위")
    start_date: str | None = Field(None, description="YYYY-MM-DD format")
    end_date: str | None = Field(None, description="YYYY-MM-DD format")


class DownloadEventsQueryParams(BaseModel):
    """이벤트 다운로드 쿼리 파라미터"""
    
    artist_id: int | None = Field(None, description="아티스트 ID")
    category: EventCategory | None = Field(None, description="일정 종류")
    start_date: str | None = Field(None, description="YYYY-MM-DD format")
    end_date: str | None = Field(None, description="YYYY-MM-DD format")


class ScrapeEventsQueryParams(BaseModel):
    """이벤트 스크래핑 쿼리 파라미터"""
    
    locale: str = Field("ko", description="언어 설정")
    artist_name: str | None = Field(None, description="솔로: stage_name, 그룹: group_name")


class CalendarEventsQueryParams(BaseModel):
    """캘린더 이벤트 조회 쿼리 파라미터"""
    
    artist_name: str | None = Field(None, description="아티스트 이름")
