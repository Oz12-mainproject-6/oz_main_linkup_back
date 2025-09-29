import traceback
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
from starlette.status import HTTP_404_NOT_FOUND


from app.external.scrapping import get_myloveidol_schedule, fetch_myloveidol_json, parse_myloveidol_events
from app.features.artists.models import Artist
from app.features.events.services import EventCRUD, notification_service
from app.features.events.models import EventCategory, EventVisibility, Events
from app.features.events.schemas import (
    BulkEventCreate,
    EventListResponse,
    EventResponse,
    FileUploadResponse, EventOut,
)
from app.features.events.services import EventCRUD, EventService, notification_service
from app.features.notifications.models import Subscription
from app.features.users.dependencies import get_current_user
from app.features.users.models import User

event_router = APIRouter(prefix="/api/events", tags=["events"])


@event_router.get("/", response_model=EventListResponse)
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    artist_parent_group: int | None = Query(None, description="그룹 ID"),  # 🔹 추가
    artist_id: int | None = Query(None, description="아티스트 id"),
    category: EventCategory | None = Query(None, description="일정 종류"),
    visibility: EventVisibility | None = Query(None, description="공개범위"),
    is_active: bool | None = Query(None, description="구독 중인 아티스트의 이벤트만 조회 (true: 구독 중만, null: 전체)"),
    start_date: str | None = Query(None, description="YYYY-MM-DD format"),
    end_date: str | None = Query(None, description="YYYY-MM-DD format"),
    current_user: User | None = Depends(get_current_user),
):
    """이벤트 목록 조회"""
    try:
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

    except ValueError as err:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        ) from err

    # 구독 중인 아티스트 필터링
    subscribed_artist_ids = None
    if is_active and current_user:
        subscribed_artist_ids = await Subscription.filter(
            user=current_user, is_active=True
        ).values_list("artist_id", flat=True)

    events, total = await EventCRUD.get_list(
        skip=skip,
        limit=limit,
        artist_parent_group=artist_parent_group,  # 🔹 EventCRUD에 전달
        artist_id=artist_id,
        category=category,
        visibility=visibility,
        is_active=True,  # 활성 이벤트만 조회 (기본값)
        start_date=start_dt,
        end_date=end_dt,
        subscribed_artist_ids=subscribed_artist_ids,  # 구독 필터링 추가
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

#author : Juwon
#date : 2025-09-25
#content : 최애돌 사이트를 크롤링 하는 사이트로 변경한 라우터


@event_router.get("/scrape/myloveidol")
async def scrape_myloveidol_events(
    locale: str = Query("ko", description="언어 설정"),
    artist_name: str | None = Query(None, description="솔로: stage_name, 그룹: group_name")
):
    """
    최애돌 JSON API 크롤링 → DB 저장
    """


@event_router.post("/scrape/myloveidol/import")
async def import_myloveidol_events(

        locale: str = Query("ko", description="언어 설정"),
        artist_name: str | None = Query(None, description="솔로: stage_name, 그룹: group_name"),
        background_tasks: BackgroundTasks = None
):
    """MyLoveIdol에서 스케줄을 크롤링해서 DB에 저장"""
    try:
        events = fetch_myloveidol_json(locale=locale)

        # artist_name 필터 적용
        if artist_name:
            events = [e for e in events if e["idol"]["name"] == artist_name]

        # 크롤링
        scraped_events = get_myloveidol_schedule(
            locale=locale,

            artist_name=artist_name
        )

        if not scraped_events:
            return {
                "message": "크롤링된 이벤트가 없습니다.",
                "imported": 0,
                "errors": []
            }

        # DB 저장 형식으로 변환
        result = await EventService.import_scraped_events(scraped_events, "myloveidol")

        # 성공한 이벤트에 대해 알림
        if result.successful > 0 and background_tasks:
            recent_events, _ = await EventCRUD.get_list(limit=result.successful)
            background_tasks.add_task(
                notification_service.send_batch_notification,
                recent_events,
                "scraped_import"
            )

        return result

    except Exception as e:
        logger.error(f"MyLoveIdol import error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Import error: {str(e)}"
        )


@event_router.get("/events/calendar/", response_model=list[EventOut])
async def get_events(artist_name: str | None = Query(None)):
    events, total = await EventCRUD.get_list()
    if artist_name:
        events = [e for e in events if e.artist_name == artist_name]
    return events

        # 더 자세한 에러 정보 반환

        return {"error": str(e), "traceback": traceback.format_exc()}

