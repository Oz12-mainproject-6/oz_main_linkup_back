from fastapi import APIRouter, Depends, HTTPException, Query
from tortoise.exceptions import DoesNotExist

from app.features.artists.models import Artist, ArtistType
from app.features.images.models import ImageType, SharedImage
from app.features.notifications.models import Subscription
from app.features.users.dependencies import get_current_fan_user
from app.features.users.models import User

from .schemas import SubscriptionCreate, SubscriptionOut, SubscriptionWithImageOut

subscriptions_router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@subscriptions_router.post("/")
async def create_subscription(
    request: SubscriptionCreate, current_user: User = Depends(get_current_fan_user)
):
    """팬 → 아티스트 구독"""

    # 아티스트 존재 여부 확인
    artist = await Artist.get_or_none(id=request.artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail="아티스트를 찾을 수 없습니다.")

    # 기존 구독 확인 (활성/비활성 모두)
    existing_subscription = await Subscription.filter(
        user=current_user, artist=artist
    ).first()

    if existing_subscription:
        if existing_subscription.is_active:
            raise HTTPException(status_code=400, detail="이미 구독 중입니다.")
        else:
            # 비활성화된 구독이 있으면 다시 활성화
            existing_subscription.is_active = True
            await existing_subscription.save()
            return {"detail": "구독이 재활성화되었습니다."}
    else:
        # 새로운 구독 생성
        await Subscription.create(user=current_user, artist=artist)
    return {"detail": "구독이 완료되었습니다."}


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

    # 기본 쿼리
    query = Subscription.filter(user=current_user, is_active=True)

    # 아티스트 이름 필터링
    if group_name:
        query = query.filter(artist__group_name__icontains=group_name)
    if stage_name:
        query = query.filter(artist__stage_name__icontains=stage_name)

    if include_image:
        # face 이미지 URL 포함한 응답
        subscriptions = await query.prefetch_related("artist")

        result = []
        for sub in subscriptions:
            # 아티스트 FACE 이미지 조회
            face_image = await SharedImage.filter(
                artist=sub.artist, image_type=ImageType.FACE
            ).first()

            result.append(
                SubscriptionWithImageOut(
                    id=sub.id,
                    artist_id=sub.artist.id,
                    group_name=sub.artist.group_name,
                    stage_name=sub.artist.stage_name
                    if sub.artist.artist_type != ArtistType.GROUP
                    else None,
                    artist_image_url=face_image.url if face_image else None,
                    is_active=sub.is_active,
                )
            )

        return result
    else:
        # 기본 응답 (이미지 없음)
        subscriptions = await query.prefetch_related("artist")
        result = []
        for sub in subscriptions:
            result.append(
                SubscriptionOut(
                    id=sub.id,
                    artist_id=sub.artist.id,
                    group_name=sub.artist.group_name,
                    stage_name=sub.artist.stage_name
                    if sub.artist.artist_type != ArtistType.GROUP
                    else None,
                    is_active=sub.is_active,
                )
            )
        return result


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
