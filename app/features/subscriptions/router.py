from fastapi import APIRouter, Depends, Query

from app.features.users.dependencies import get_current_fan_user
from app.features.users.models import User

from .schemas import SubscriptionCreate
from .service import SubscriptionService

subscriptions_router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@subscriptions_router.post("/")
async def create_subscription(
    request: SubscriptionCreate, current_user: User = Depends(get_current_fan_user)
):
    """팬 → 아티스트 구독"""
    return await SubscriptionService.create_subscription(
        request.artist_id, current_user
    )


@subscriptions_router.get("/")
async def list_subscriptions(
    include_image: bool = Query(
        False, description="아티스트 face 이미지 URL 포함 여부"
    ),
    group_name: str | None = Query(None, description="그룹명으로 필터링"),
    stage_name: str | None = Query(None, description="활동명으로 필터링"),
    current_user: User = Depends(get_current_fan_user),
):
    """내 구독 목록 조회"""
    return await SubscriptionService.get_subscriptions(
        current_user, include_image, group_name, stage_name
    )


@subscriptions_router.delete("/{artist_id}")
async def cancel_subscription(
    artist_id: int, current_user: User = Depends(get_current_fan_user)
):
    """구독 취소"""
    return await SubscriptionService.cancel_subscription(artist_id, current_user)
