from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
)
from fastapi.responses import StreamingResponse

from app.core.exceptions import (
    FileProcessingError,
    InternalServerError,
    ValidationError,
)
from app.features.artists.models import ArtistType
from app.features.companies.dependencies import get_current_company_user
from app.features.companies.schemas import (
    CompanyDashboardResponse,
    DashboardArtistInfo,
    EventCreateRequest,
    EventResponse,
    EventUpdateRequest,
)
from app.features.companies.service import CompanyService
from app.features.events.services import EventCRUD, EventService, notification_service
from app.features.users.models import Company, User

companies_router = APIRouter(prefix="/api/companies", tags=["companies"])


@companies_router.get("/dashboard", response_model=CompanyDashboardResponse)
async def get_company_dashboard(
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """소속사 대시보드 - 소속 아티스트와 최근 이벤트"""
    current_user, company = user_company
    return await CompanyService.get_dashboard(company)


@companies_router.get("/events", response_model=list[EventResponse])
async def get_company_events(
    user_company: tuple[User, Company] = Depends(get_current_company_user),
    artist_id: int | None = Query(None, description="특정 아티스트 이벤트 필터"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """소속사 이벤트 목록 조회"""
    current_user, company = user_company
    return await CompanyService.get_events(company, artist_id, limit, offset)


@companies_router.post("/events", response_model=EventResponse)
async def create_event(
    request: EventCreateRequest,
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """이벤트 생성"""
    current_user, company = user_company
    return await CompanyService.create_event(company, request)


@companies_router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    request: EventUpdateRequest,
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """이벤트 수정"""
    current_user, company = user_company
    return await CompanyService.update_event(company, event_id, request)


@companies_router.delete("/events/{event_id}")
async def delete_event(
    event_id: int,
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """이벤트 삭제 (soft delete)"""
    current_user, company = user_company
    return await CompanyService.delete_event(company, event_id)


# Artist 관리 엔드포인트
@companies_router.get("/artists", response_model=list[DashboardArtistInfo])
async def get_company_artists(
    user_company: tuple[User, Company] = Depends(get_current_company_user),
    is_active: bool | None = Query(True, description="활동 상태 필터 (기본값: True)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """소속사 아티스트 목록 조회"""
    current_user, company = user_company
    return await CompanyService.get_artists(company, is_active, limit, offset)


@companies_router.get("/artists/upload-template")
async def download_artist_events_template(
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """
    아티스트용 이벤트 업로드 템플릿 다운로드
    - 간소화된 필드만 포함: title, description, start_time, end_time, location
    """
    current_user, company = user_company

    try:
        file_stream = await EventService.generate_artist_template()
        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=artist_events_template.xlsx"
            },
        )
    except Exception as e:
        raise InternalServerError(f"Template generation error: {str(e)}") from e


@companies_router.get("/artists/{artist_id}", response_model=DashboardArtistInfo)
async def get_artist_detail(
    artist_id: int,
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """특정 아티스트 상세 조회 (이미지 포함)"""
    current_user, company = user_company
    return await CompanyService.get_artist_detail(company, artist_id)


@companies_router.post("/artists")
async def create_artist_with_images(
    stage_name: str = Form(None),
    group_name: str = Form(None),
    debut_date: date = Form(None),
    birthdate: date = Form(None),
    face_image: UploadFile = File(None),
    torso_image: UploadFile = File(None),
    banner_image: UploadFile = File(None),
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """아티스트 + 이미지 3개 통합 생성"""
    current_user, company = user_company
    return await CompanyService.create_artist_with_images(
        company,
        current_user,
        stage_name,
        group_name,
        debut_date,
        birthdate,
        face_image,
        torso_image,
        banner_image,
    )


@companies_router.put("/artists/{artist_id}")
async def update_artist_with_images(
    artist_id: int,
    stage_name: str = Form(None),
    group_name: str = Form(None),
    debut_date: date = Form(None),
    birthdate: date = Form(None),
    artist_type: ArtistType | None = Form(...),
    face_image: UploadFile = File(None),
    torso_image: UploadFile = File(None),
    banner_image: UploadFile = File(None),
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """아티스트 정보와 이미지 업데이트 (POST와 동일한 Form 방식)"""
    current_user, company = user_company

    # POST와 똑같이 직접 전달 (복잡한 process_file 로직 제거)
    await CompanyService.update_artist_with_images_form(
        company,
        current_user,
        artist_id,
        stage_name,
        group_name,
        debut_date,
        birthdate,
        artist_type,
        face_image,
        torso_image,
        banner_image,
    )
    return {
        "message": "아티스트 정보가 성공적으로 업데이트되었습니다.",
        "artist_id": artist_id,
    }


@companies_router.delete("/artists/{artist_id}")
async def delete_artist(
    artist_id: int,
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """아티스트 삭제 (soft delete)"""
    current_user, company = user_company
    return await CompanyService.delete_artist(company, artist_id)


@companies_router.post("/artists/{artist_id}/upload-all", response_model=None)
async def upload_artist_events_file(
    artist_id: int,
    file: UploadFile = File(...),
    background_tasks=None,
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """
    특정 아티스트의 이벤트 파일 업로드 및 일괄 생성
    - Excel(.xlsx) 또는 CSV(.csv) 지원
    - title, description, start_time, end_time, location 필드만 처리
    - artist_id를 통해 artist-events 연결
    """
    current_user, company = user_company

    # 파일 확장자 검증
    if not file.filename.endswith((".xlsx", ".csv")):
        raise ValidationError("Only Excel (.xlsx) and CSV files are supported")

    try:
        # EventService에서 파일 처리 (artist_id 포함)
        result = await EventService.process_upload_file_for_artist(file, artist_id)

        # 알림 전송
        if getattr(result, "successful", 0) > 0 and background_tasks:
            recent_events, _ = await EventCRUD.get_list(
                artist_id=artist_id, limit=result.successful
            )
            background_tasks.add_task(
                notification_service.send_batch_notification,
                recent_events,
                "artist_file_upload",
            )

        return result

    except Exception as e:
        raise FileProcessingError(f"File processing error: {str(e)}") from e
