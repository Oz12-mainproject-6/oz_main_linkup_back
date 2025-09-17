from datetime import datetime, timedelta
from typing import Optional, List
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, validator


from app.features.events.models import EventCategory, EventVisibility

KST = ZoneInfo("Asia/Seoul")
class EventBase(BaseModel):
    """이벤트 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=200, description="이벤트 제목")
    description: Optional[str] = Field(None, description="이벤트 설명")
    start_time: datetime = Field(..., description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간")
    location: Optional[str] = Field(None, max_length=200, description="위치")
    category: EventCategory = Field(..., description="이벤트 카테고리")
    visibility: EventVisibility = Field(EventVisibility.PUBLIC, description="공개 설정")


class EventCreate(EventBase):
    artist_id: int = Field(..., description="아티스트 ID")

    @validator("end_time")
    def validate_end_time(cls, v, values):
        if v and "start_time" in values and v <= values["start_time"]:
            raise ValueError("End time must be after start time")
        return v

    @validator("start_time")
    def validate_start_time(cls, v):
        v_kst = v.astimezone(KST)
        now_kst = datetime.now(KST)
        # 현재 시각보다 5분 이상 과거면 에러
        if v_kst < now_kst - timedelta(minutes=5):
            raise ValueError("start_time must be in the future (KST, 5분 허용)")
        return v

class EventUpdate(BaseModel):
    """이벤트 업데이트 스키마"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=200)
    category: Optional[EventCategory] = None
    visibility: Optional[EventVisibility] = None
    is_active: Optional[bool] = None

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if v and 'start_time' in values and values['start_time'] and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v


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
    events: List[EventResponse]
    total: int
    page: int
    size: int


class FileUploadResponse(BaseModel):
    """파일 업로드 응답 스키마"""
    message: str
    total_processed: int
    successful: int
    failed: int
    errors: List[str] = []


class BulkEventCreate(BaseModel):
    """일괄 이벤트 생성 스키마"""
    events: List[EventCreate]