from fastapi import APIRouter, Depends, HTTPException, Query, status
from tortoise import models

from app.features.artists.models import Artist
from app.features.artists.schemas import (
    ArtistListResponse,
    ArtistResponse,
    ArtistSubscriptionInfo,
)
from app.features.notifications.models import Subscription
from app.features.users.dependencies import get_current_user
from app.features.users.models import User

idol_router = APIRouter(prefix="/api/idol", tags=["idol"])


@idol_router.get("", response_model=list[ArtistListResponse])
async def get_idol_list(
    artist_type: str | None = Query(
        None, description="아티스트 타입 필터 (group/individual)"
    ),
    is_active: bool | None = Query(None, description="활동 상태 필터"),
    limit: int = Query(20, ge=1, le=100, description="조회할 아티스트 수"),
    offset: int = Query(0, ge=0, description="시작 위치"),
):
    """아이돌 리스트 조회"""

    # 기본 쿼리
    query = Artist.all()

    # 필터 적용
    if artist_type:
        query = query.filter(artist_type=artist_type)

    if is_active is not None:
        query = query.filter(is_active=is_active)

    # 정렬 및 페이징
    artists = await query.order_by("-created_at").offset(offset).limit(limit)

    return [
        ArtistListResponse(
            id=artist.id,
            real_name=artist.real_name,
            stage_name=artist.stage_name,
            artist_type=artist.artist_type,
            debut_date=artist.debut_date,
            is_active=artist.is_active,
            member_count=artist.member_count,
        )
        for artist in artists
    ]


@idol_router.get("/{artist_name}", response_model=ArtistResponse)
async def get_idol_detail(artist_name: str):
    """아이돌 상세 조회 (실명 또는 예명으로 검색)"""

    # 예명 또는 실명으로 검색
    artist = await Artist.filter(
        models.Q(stage_name__iexact=artist_name)
        | models.Q(real_name__iexact=artist_name)
    ).first()

    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"아티스트 '{artist_name}'을 찾을 수 없습니다.",
        )

    return ArtistResponse(
        id=artist.id,
        real_name=artist.real_name,
        stage_name=artist.stage_name,
        birthdate=artist.birthdate,
        gender=artist.gender,
        role=artist.role,
        mbti=artist.mbti,
        height=artist.height,
        nickname=artist.nickname,
        debut_date=artist.debut_date,
        artist_type=artist.artist_type,
        member_count=artist.member_count,
        is_active=artist.is_active,
        created_at=artist.created_at.isoformat() if artist.created_at else None,
        updated_at=artist.updated_at.isoformat() if artist.updated_at else None,
    )


@idol_router.get("/{artist_name}/info", response_model=ArtistSubscriptionInfo)
async def get_idol_subscription_info(
    artist_name: str, current_user: User = Depends(get_current_user)
):
    """구독 아티스트 확인 (로그인 필요)"""

    # 아티스트 조회
    artist = await Artist.filter(
        models.Q(stage_name__iexact=artist_name)
        | models.Q(real_name__iexact=artist_name)
    ).first()

    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"아티스트 '{artist_name}'을 찾을 수 없습니다.",
        )

    # 구독 여부 확인
    subscription = await Subscription.filter(user=current_user, artist=artist).first()

    return ArtistSubscriptionInfo(
        id=artist.id,
        real_name=artist.real_name,
        stage_name=artist.stage_name,
        artist_type=artist.artist_type,
        is_subscribed=subscription is not None,
        subscription_date=subscription.created_at.isoformat() if subscription else None,
    )
