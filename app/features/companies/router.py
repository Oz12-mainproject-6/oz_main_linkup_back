from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
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
    artist_type: ArtistType = Form(...),
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
        artist_type,
        face_image,
        torso_image,
        banner_image,
    )


# @companies_router.put("/artists/{artist_id}")
# async def update_artist(
#     artist_id: int,
#     request: ArtistUpdateRequest,
#     user_company: tuple[User, Company] = Depends(get_current_company_user),
# ):
#     """아티스트 수정"""
#     current_user, company = user_company
#     return await CompanyService.update_artist(company, artist_id, request)


@companies_router.put("/artists/{artist_id}")
async def update_artist_with_images(
    artist_id: int,
    stage_name: str = Form(None),
    group_name: str = Form(None),
    debut_date: date = Form(None),
    birthdate: date = Form(None),
    artist_type: ArtistType = Form(None),
    face_image_url: str = Form(None),
    torso_image_url: str = Form(None),
    banner_image_url: str = Form(None),
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """아티스트 정보와 이미지 업데이트 (POST와 동일한 Form 방식)"""
    current_user, company = user_company
    await CompanyService.update_artist_with_images_form(
        company,
        current_user,
        artist_id,
        stage_name,
        group_name,
        debut_date,
        birthdate,
        artist_type,
        face_image_url,
        torso_image_url,
        banner_image_url,
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
