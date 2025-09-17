from fastapi import APIRouter, Depends, HTTPException
from tortoise.exceptions import DoesNotExist

from app.features.artists.models import Artist
from app.features.users.dependencies import get_current_fan_user
from app.features.users.models import User

from .models import Subscription
from .schemas import SubscriptionCreate, SubscriptionOut

subscriptions_router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@subscriptions_router.post("/", response_model=SubscriptionOut)
async def create_subscription(
    request: SubscriptionCreate, current_user: User = Depends(get_current_fan_user)
):
    """팬 → 아티스트 구독"""

    # 아티스트 존재 여부 확인
    artist = await Artist.get_or_none(id=request.artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail="아티스트를 찾을 수 없습니다.")

    # 이미 구독 여부 확인
    exists = await Subscription.filter(
        user=current_user, artist=artist, is_active=True
    ).exists()
    if exists:
        raise HTTPException(status_code=400, detail="이미 구독 중입니다.")

    subscription = await Subscription.create(user=current_user, artist=artist)
    return subscription


@subscriptions_router.get("/", response_model=list[SubscriptionOut])
async def list_subscriptions(current_user: User = Depends(get_current_fan_user)):
    """내 구독 목록 조회"""
    subscriptions = await Subscription.filter(user=current_user, is_active=True)
    return subscriptions


@subscriptions_router.delete("/{subscription_id}", response_model=dict)
async def cancel_subscription(
    subscription_id: int, current_user: User = Depends(get_current_fan_user)
):
    """구독 취소"""
    try:
        sub = await Subscription.get(id=subscription_id, user=current_user)
        sub.is_active = False
        await sub.save()
        return {"detail": "구독 취소 완료"}
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="구독 정보가 없습니다.") from None
