from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.features.artists.models import Artist
from app.features.companies.dependencies import get_current_company_user
from app.features.companies.schemas import (
    ArtistCreateRequest,
    ArtistUpdateRequest,
    CompanyDashboardResponse,
    DashboardArtistInfo,
    DashboardEventInfo,
    EventCreateRequest,
    EventResponse,
    EventUpdateRequest,
)
from app.features.events.models import Events
from app.features.users.models import Company, User

companies_router = APIRouter(prefix="/api/companies", tags=["companies"])


@companies_router.get("/dashboard", response_model=CompanyDashboardResponse)
async def get_company_dashboard(
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """소속사 대시보드 - 소속 아티스트와 최근 이벤트"""
    current_user, company = user_company

    # 소속 아티스트 조회
    artists = await Artist.filter(company=company, is_active=True).all()

    # 최근 30일 이벤트 조회
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_events = (
        await Events.filter(
            artist__company=company, start_time__gte=thirty_days_ago, is_active=True
        )
        .prefetch_related("artist")
        .order_by("-start_time")
        .limit(10)
    )

    # 아티스트별 이번 달 이벤트 수 계산
    artist_events_count = {}
    for event in recent_events:
        artist_id = event.artist_id
        artist_events_count[artist_id] = artist_events_count.get(artist_id, 0) + 1

    # 응답 데이터 구성
    dashboard_artists = []
    for artist in artists:
        dashboard_artists.append(
            DashboardArtistInfo(
                id=artist.id,
                real_name=artist.real_name,
                stage_name=artist.stage_name,
                artist_type=artist.artist_type,
                debut_date=artist.debut_date,
                is_active=artist.is_active,
                event_count=artist_events_count.get(artist.id, 0),
            )
        )

    dashboard_events = []
    for event in recent_events:
        dashboard_events.append(
            DashboardEventInfo(
                id=event.id,
                title=event.title,
                start_time=event.start_time,
                end_time=event.end_time,
                category=event.category,
                artist_name=event.artist.real_name,
                artist_stage_name=event.artist.stage_name,
            )
        )

    return CompanyDashboardResponse(
        company_name=company.name,
        artists=dashboard_artists,
        recent_events=dashboard_events,
        total_artists=len(artists),
        total_events=len(recent_events),
    )


@companies_router.get("/events", response_model=list[EventResponse])
async def get_company_events(
    user_company: tuple[User, Company] = Depends(get_current_company_user),
    artist_id: int | None = Query(None, description="특정 아티스트 이벤트 필터"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """소속사 이벤트 목록 조회"""
    current_user, company = user_company

    query = Events.filter(artist__company=company, is_active=True)

    if artist_id:
        # 해당 아티스트가 본인 소속사 것인지 확인
        artist = await Artist.get_or_none(id=artist_id, company=company)
        if not artist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 아티스트를 찾을 수 없습니다.",
            )
        query = query.filter(artist_id=artist_id)

    events = (
        await query.prefetch_related("artist")
        .order_by("-start_time")
        .offset(offset)
        .limit(limit)
    )

    return [
        EventResponse(
            id=event.id,
            title=event.title,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            location=event.location,
            category=event.category,
            visibility=event.visibility,
            is_active=event.is_active,
            artist_id=event.artist.id,
            artist_name=event.artist.real_name,
            artist_stage_name=event.artist.stage_name,
            created_at=event.created_at.isoformat(),
            updated_at=event.updated_at.isoformat(),
        )
        for event in events
    ]


@companies_router.post("/events", response_model=EventResponse)
async def create_event(
    request: EventCreateRequest,
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """이벤트 생성"""
    current_user, company = user_company

    # 해당 아티스트가 본인 소속사 것인지 확인
    artist = await Artist.get_or_none(id=request.artist_id, company=company)
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 아티스트를 찾을 수 없습니다.",
        )

    event = await Events.create(
        artist=artist,
        title=request.title,
        description=request.description,
        start_time=request.start_time,
        end_time=request.end_time,
        location=request.location,
        category=request.category,
        visibility=request.visibility,
    )

    return EventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        start_time=event.start_time,
        end_time=event.end_time,
        location=event.location,
        category=event.category,
        visibility=event.visibility,
        is_active=event.is_active,
        artist_id=artist.id,
        artist_name=artist.real_name,
        artist_stage_name=artist.stage_name,
        created_at=event.created_at.isoformat(),
        updated_at=event.updated_at.isoformat(),
    )


@companies_router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    request: EventUpdateRequest,
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """이벤트 수정"""
    current_user, company = user_company

    # 이벤트가 본인 소속사 것인지 확인
    event = (
        await Events.filter(id=event_id, artist__company=company, is_active=True)
        .prefetch_related("artist")
        .first()
    )

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 이벤트를 찾을 수 없습니다.",
        )

    # 수정할 필드만 업데이트
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)

    await event.save()

    return EventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        start_time=event.start_time,
        end_time=event.end_time,
        location=event.location,
        category=event.category,
        visibility=event.visibility,
        is_active=event.is_active,
        artist_id=event.artist.id,
        artist_name=event.artist.real_name,
        artist_stage_name=event.artist.stage_name,
        created_at=event.created_at.isoformat(),
        updated_at=event.updated_at.isoformat(),
    )


@companies_router.delete("/events/{event_id}")
async def delete_event(
    event_id: int,
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """이벤트 삭제 (soft delete)"""
    current_user, company = user_company

    # 이벤트가 본인 소속사 것인지 확인
    event = await Events.filter(
        id=event_id, artist__company=company, is_active=True
    ).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 이벤트를 찾을 수 없습니다.",
        )

    # Soft delete
    event.is_active = False
    await event.save()

    return {"message": "이벤트가 삭제되었습니다."}


# Artist 관리 엔드포인트
@companies_router.get("/artists", response_model=list[DashboardArtistInfo])
async def get_company_artists(
    user_company: tuple[User, Company] = Depends(get_current_company_user),
    is_active: bool | None = Query(None, description="활동 상태 필터"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """소속사 아티스트 목록 조회"""
    current_user, company = user_company

    query = Artist.filter(company=company)

    if is_active is not None:
        query = query.filter(is_active=is_active)

    artists = await query.order_by("-created_at").offset(offset).limit(limit)

    return [
        DashboardArtistInfo(
            id=artist.id,
            real_name=artist.real_name,
            stage_name=artist.stage_name,
            artist_type=artist.artist_type,
            debut_date=artist.debut_date,
            is_active=artist.is_active,
            event_count=0,  # 필요시 별도 계산
        )
        for artist in artists
    ]


@companies_router.post("/artists")
async def create_artist(
    request: ArtistCreateRequest,
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """아티스트 생성"""
    current_user, company = user_company

    # 이메일 중복 체크
    existing_artist = await Artist.filter(email=request.email).first()
    if existing_artist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="이미 등록된 이메일입니다."
        )

    # parent_group 확인 (멤버인 경우)
    parent_group = None
    if request.parent_group_id:
        parent_group = await Artist.get_or_none(
            id=request.parent_group_id, company=company, artist_type="group"
        )
        if not parent_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 그룹을 찾을 수 없습니다.",
            )

    artist = await Artist.create(
        company=company,
        real_name=request.real_name,
        stage_name=request.stage_name,
        birthdate=request.birthdate,
        gender=request.gender,
        role=request.role,
        mbti=request.mbti,
        height=request.height,
        nickname=request.nickname,
        email=request.email,
        debut_date=request.debut_date,
        artist_type=request.artist_type,
        parent_group=parent_group,
        member_count=request.member_count,
    )

    return {"message": "아티스트가 생성되었습니다.", "artist_id": artist.id}


@companies_router.put("/artists/{artist_id}")
async def update_artist(
    artist_id: int,
    request: ArtistUpdateRequest,
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """아티스트 수정"""
    current_user, company = user_company

    artist = await Artist.get_or_none(id=artist_id, company=company)
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 아티스트를 찾을 수 없습니다.",
        )

    # 이메일 중복 체크 (자신 제외)
    if request.email and request.email != artist.email:
        existing_artist = await Artist.filter(email=request.email).first()
        if existing_artist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다.",
            )

    # 수정할 필드만 업데이트
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(artist, field, value)

    await artist.save()

    return {"message": "아티스트 정보가 수정되었습니다."}


@companies_router.delete("/artists/{artist_id}")
async def delete_artist(
    artist_id: int,
    user_company: tuple[User, Company] = Depends(get_current_company_user),
):
    """아티스트 삭제 (soft delete)"""
    current_user, company = user_company

    artist = await Artist.get_or_none(id=artist_id, company=company, is_active=True)
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 아티스트를 찾을 수 없습니다.",
        )

    # 관련 이벤트도 함께 비활성화
    await Events.filter(artist=artist, is_active=True).update(is_active=False)

    # 아티스트 비활성화 (soft delete)
    artist.is_active = False
    await artist.save()

    return {"message": "아티스트가 삭제되었습니다. (관련 이벤트도 함께 삭제됨)"}
