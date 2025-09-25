from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
from starlette.status import HTTP_404_NOT_FOUND

from app.external.scrapping import get_artist_schedule
from app.features.events.services import EventCRUD, notification_service
from app.features.events.models import EventCategory, EventVisibility

from app.features.events.schemas import (
    BulkEventCreate,
    EventListResponse,
    EventResponse,
    FileUploadResponse,
)
from app.features.events.services import EventService

event_router = APIRouter(prefix="/api/events", tags=["events"])


@event_router.get("/", response_model=EventListResponse)
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    artist_parent_group: int | None = Query(None, description="그룹 ID"),  # 🔹 추가
    artist_id: int | None = Query(None, description="아티스트 id"),
    category: EventCategory | None = Query(None, description="일정 종류"),
    visibility: EventVisibility | None = Query(None, description="공개범위"),
    is_active: bool = Query(True, description="활동여부"),
    start_date: str | None = Query(None, description="YYYY-MM-DD format"),
    end_date: str | None = Query(None, description="YYYY-MM-DD format"),
):
    """이벤트 목록 조회"""
    try:
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

    except ValueError as err:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        ) from err

    events, total = await EventCRUD.get_list(
        skip=skip,
        limit=limit,
        artist_parent_group=artist_parent_group,  # 🔹 EventCRUD에 전달
        artist_id=artist_id,
        category=category,
        visibility=visibility,
        is_active=is_active,
        start_date=start_dt,
        end_date=end_dt,
    )

    return EventListResponse(
        events=events,
        total=total,
        page=skip // limit + 1,
        size=limit,
    )


@event_router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int):
    """이벤트 상세 조회"""
    event = await EventCRUD.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@event_router.post("/", response_model=FileUploadResponse)
async def bulk_create_events(
    bulk_data: BulkEventCreate, background_tasks: BackgroundTasks
):
    """일괄 이벤트 생성"""
    events_data = [event.dict() for event in bulk_data.events]
    created_count, errors = await EventCRUD.bulk_create(events_data)

    # 성공 이벤트 알림
    if created_count > 0:
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


@event_router.post("/file/upload", response_model=FileUploadResponse)
async def upload_events_file(
    file: UploadFile = File(...), background_tasks: BackgroundTasks = None
):
    """파일 업로드"""

    if not file.filename.endswith((".xlsx", ".csv")):
        raise HTTPException(
            status_code=400, detail="Only Excel (.xlsx) and CSV files are supported"
        )

    try:
        result = await EventService.process_upload_file(file)

        if result.successful > 0 and background_tasks:
            recent_events, _ = await EventCRUD.get_list(limit=result.successful)
            background_tasks.add_task(
                notification_service.send_batch_notification,
                recent_events,
                "file_upload",
            )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"File processing error: {str(e)}"
        ) from e


@event_router.post("/file/upload-all", response_model=FileUploadResponse)
async def upload_and_create_bulk_events(
    file: UploadFile = File(...), background_tasks: BackgroundTasks = None
):
    """
    파일 업로드 후 일괄 이벤트 생성
    - Excel(.xlsx) 또는 CSV(.csv) 지원
    - 성공한 이벤트에 대해 알림 전송
    """
    if not file.filename.endswith((".xlsx", ".csv")):
        raise HTTPException(
            status_code=400, detail="Only Excel (.xlsx) and CSV files are supported"
        )

    try:
        # EventService에서 처리 결과 반환
        result = await EventService.process_upload_file(file)

        # 알림 전송
        if getattr(result, "successful", 0) > 0 and background_tasks:
            recent_events, _ = await EventCRUD.get_list(limit=result.successful)
            background_tasks.add_task(
                notification_service.send_batch_notification,
                recent_events,
                "file_upload_bulk",
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"File processing error: {str(e)}"
        ) from e


# ---------------------------
# 특정 이벤트 다운로드
# ---------------------------
@event_router.get("/file/download/{event_id}")
async def download_single_event(event_id: int):
    """
    단일 이벤트 다운로드
    """
    event = await EventCRUD.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Event not found")

    file_stream = await EventService.export_single_event(event)
    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=events_template.xlsx"},
    )


# ---------------------------
# 조건 기반 일괄 이벤트 다운로드
# ---------------------------
@event_router.get("/file/download-all")
async def download_bulk_events(
    artist_id: int | None = Query(None),
    category: EventCategory | None = Query(None),
    start_date: str | None = Query(None, description="YYYY-MM-DD format"),
    end_date: str | None = Query(None, description="YYYY-MM-DD format"),
):
    """
    조건 기반 일괄 이벤트 다운로드
    """
    try:
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
    except ValueError as err:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        ) from err

    file_stream = await EventService.export_to_excel(
        artist_id=artist_id, category=category, start_date=start_dt, end_date=end_dt
    )

    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=events_export.xlsx"},
    )


@event_router.get("/calendar/{year}/{month}")
async def get_calendar_events(year: int, month: int):
    start_date = datetime(year, month, 1)
    end_date = datetime(year + (month // 12), month % 12 + 1, 1)
    events = await EventCRUD.get_events_by_date_range(start_date, end_date)
    return {"year": year, "month": month, "events": events}


@event_router.post("/notifications")
async def trigger_notifications(background_tasks: BackgroundTasks):
    """수동 알림 트리거"""
    try:
        background_tasks.add_task(EventService.trigger_notifications)
        return {"message": "Notification trigger initiated"}
    except Exception as e:
        logger.error(f"Failed to trigger notifications: {str(e)}")

        raise HTTPException(
            status_code=400, detail=f"File processing error: {str(e)}"
        ) from e


@event_router.get("/schedule/{artist_name}/{unit_id}")
async def scrap_events(artist_name: str, unit_id: str):

    try:
        # 함수명 변경
        events = get_artist_schedule(artist_name, unit_id)
        return {"events": events}
    except Exception as e:
        # 더 자세한 에러 정보 반환
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }