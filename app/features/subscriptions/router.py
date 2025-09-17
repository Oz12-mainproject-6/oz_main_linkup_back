from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.exceptions import DoesNotExist

from app.features.users.models import User, UserType
from app.features.users.auth import get_current_user
from .models import Subscription, Artist
from .schemas import SubscriptionCreate, SubscriptionOut

subscriptions_router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@subscriptions_router.post("/", response_model=SubscriptionOut)
async def create_subscription(
    request: SubscriptionCreate, current_user: User = Depends(get_current_user)
):
    """팬 → 아티스트 구독"""
    if current_user.user_type != UserType.FAN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="팬 유저만 아티스트를 구독할 수 있습니다.",
        )

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
async def list_subscriptions(current_user: User = Depends(get_current_user)):
    """내 구독 목록 조회"""
    subscriptions = await Subscription.filter(user=current_user, is_active=True)
    return subscriptions


@subscriptions_router.delete("/{subscription_id}", response_model=dict)
async def cancel_subscription(
    subscription_id: int, current_user: User = Depends(get_current_user)
):
    """구독 취소"""
    try:
        sub = await Subscription.get(id=subscription_id, user=current_user)
        sub.is_active = False
        await sub.save()
        return {"detail": "구독 취소 완료"}
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="구독 정보가 없습니다.")
