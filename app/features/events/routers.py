from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND

from app.features.events.crud import EventCRUD
from app.features.events.models import EventCategory, EventVisibility
from app.features.events.notifications import notification_service
from app.features.events.schemas import (
    BulkEventCreate,
    EventCreate,
    EventListResponse,
    EventResponse,
    EventUpdate,
    FileUploadResponse,
)
from app.features.events.services import EventService

event_router = APIRouter(prefix="/events", tags=["events"])


@event_router.post("/", response_model=EventResponse, status_code=HTTP_201_CREATED)
async def create_event(event: EventCreate, background_tasks: BackgroundTasks):
    """이벤트 생성"""
    try:
        created_event = await EventCRUD.create(event.dict())

        # 배경 작업으로 즉시 알림 전송
        background_tasks.add_task(
            notification_service.send_instant_notification, created_event
        )

        return created_event
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@event_router.get("/", response_model=EventListResponse)
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    artist_id: int | None = Query(None),
    category: EventCategory | None = Query(None),
    visibility: EventVisibility | None = Query(None),
    is_active: bool = Query(True),
    start_date: str | None = Query(None, description="YYYY-MM-DD format"),
    end_date: str | None = Query(None, description="YYYY-MM-DD format"),
):
    """이벤트 목록 조회"""
    try:
        # 날짜 파싱
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        )

    events, total = await EventCRUD.get_list(
        skip=skip,
        limit=limit,
        artist_id=artist_id,
        category=category,
        visibility=visibility,
        is_active=is_active,
        start_date=start_dt,
        end_date=end_dt,
    )

    return EventListResponse(
        events=events, total=total, page=skip // limit + 1, size=limit
    )


@event_router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int):
    """이벤트 상세 조회"""
    event = await EventCRUD.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@event_router.put("/{event_id}", response_model=EventResponse)
async def update_event(event_id: int, event_update: EventUpdate):
    """이벤트 수정"""
    updated_event = await EventCRUD.update(
        event_id, event_update.dict(exclude_unset=True)
    )
    if not updated_event:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Event not found")
    return updated_event


@event_router.delete("/{event_id}")
async def delete_event(event_id: int):
    """이벤트 삭제"""
    deleted = await EventCRUD.delete(event_id)
    if not deleted:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Event not found")
    return {"message": "Event deleted successfully"}


@event_router.post("/bulk", response_model=FileUploadResponse)
async def bulk_create_events(
    bulk_data: BulkEventCreate, background_tasks: BackgroundTasks
):
    """일괄 이벤트 생성"""
    events_data = [event.dict() for event in bulk_data.events]
    created_count, errors = await EventCRUD.bulk_create(events_data)

    # 성공적으로 생성된 이벤트들에 대해 일괄 알림 전송
    if created_count > 0:
        # 방금 생성된 이벤트들 조회 (마지막 N개)
        recent_events, _ = await EventCRUD.get_list(limit=created_count)
        background_tasks.add_task(
            notification_service.send_batch_notification, recent_events, "bulk_create"
        )

    return FileUploadResponse(
        message=f"Processed {len(events_data)} events",
        total_processed=len(events_data),
        successful=created_count,
        failed=len(events_data) - created_count,
        errors=errors,
    )


@event_router.post("/upload", response_model=FileUploadResponse)
async def upload_events_file(
    file: UploadFile = File(...), background_tasks: BackgroundTasks = None
):
    """파일을 통한 이벤트 일괄 업로드"""
    if not file.filename.endswith((".xlsx", ".csv")):
        raise HTTPException(
            status_code=400, detail="Only Excel (.xlsx) and CSV files are supported"
        )

    try:
        result = await EventService.process_upload_file(file)

        # 업로드 성공 시 알림 전송
        if result.successful > 0 and background_tasks:
            recent_events, _ = await EventCRUD.get_list(limit=result.successful)
            background_tasks.add_task(
                notification_service.send_batch_notification,
                recent_events,
                "file_upload",
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File processing error: {str(e)}")


@event_router.get("/download/template")
async def download_template():
    """이벤트 업로드 템플릿 다운로드"""
    file_stream = await EventService.generate_template()

    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=events_template.xlsx"},
    )


@event_router.get("/download/excel")
async def download_events_excel(
    artist_id: int | None = Query(None),
    category: EventCategory | None = Query(None),
    start_date: str | None = Query(None, description="YYYY-MM-DD format"),
    end_date: str | None = Query(None, description="YYYY-MM-DD format"),
):
    """이벤트 데이터 엑셀 다운로드"""
    file_stream = await EventService.export_to_excel(
        artist_id=artist_id, category=category, start_date=start_date, end_date=end_date
    )

    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=events_export.xlsx"},
    )


@event_router.get("/calendar/{year}/{month}")
async def get_calendar_events(year: int, month: int):
    """월별 캘린더 이벤트 조회"""
    start_date = datetime(year, month, 1)

    # 다음 달의 첫째 날 구하기
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    events = await EventCRUD.get_events_by_date_range(start_date, end_date)

    return {"year": year, "month": month, "events": events}


@event_router.post("/notifications/trigger")
async def trigger_notifications(background_tasks: BackgroundTasks):
    """수동 알림 트리거 (관리자용)"""
    try:
        background_tasks.add_task(EventService.trigger_notifications)
        return {"message": "Notification trigger initiated"}
    except Exception as e:
        logger.error(f"Failed to trigger notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger notifications")
