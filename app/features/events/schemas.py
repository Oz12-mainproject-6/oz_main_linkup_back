from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from app.features.companies.router import create_event
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


    events: list[create_event]

    class Config:
        arbitrary_types_allowed = True

