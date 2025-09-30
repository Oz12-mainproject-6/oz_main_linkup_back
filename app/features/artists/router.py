from fastapi import APIRouter, Depends, Query

from app.features.artists.schemas import (
    ArtistListPaginationResponse,
    ArtistResponse,
    ArtistSubscriptionInfo,
)
from app.features.artists.service import ArtistService
from app.features.users.dependencies import get_current_user
from app.features.users.models import User

idol_router = APIRouter(prefix="/api/idol", tags=["idol"])


@idol_router.get("", response_model=ArtistListPaginationResponse)
async def get_idol_list(
    artist_type: str | None = Query(
        None, description="아티스트 타입 필터 (group/individual)"
    ),
    artist_name: str | None = Query(
        None, description="아티스트 이름 필터 (group_name/stage_name)"
    ),
    limit: int = Query(20, ge=1, le=100, description="조회할 아티스트 수"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
):
    """아이돌 리스트 조회 (활성 상태만)"""
    return await ArtistService.get_artist_list(artist_type, artist_name, limit, page)

@idol_router.get("/subscribed", response_model=ArtistListPaginationResponse)
async def get_subscribed_artists(
    limit: int = Query(20, ge=1, le=100, description="조회할 아티스트 수"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    current_user: User = Depends(get_current_user),
):
    """구독 중인 아티스트 리스트 조회 (로그인 필요)"""
    return await ArtistService.get_subscribed_artists(current_user, limit, page)


@idol_router.get("/{artist_name}/info", response_model=ArtistSubscriptionInfo)
async def get_idol_subscription_info(
    artist_name: str, current_user: User | None = Depends(get_current_user)
):
    """구독 아티스트 확인 (로그인 필요, 활성 상태만)"""
    return await ArtistService.get_artist_subscription_info(artist_name, current_user)
