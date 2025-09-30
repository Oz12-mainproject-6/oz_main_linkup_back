from fastapi import APIRouter, Depends, Query
from tortoise.exceptions import DoesNotExist

from app.core.exceptions import (
    ArtistNotFoundError,
    DuplicateSubscriptionError,
    NotFoundError,
    ValidationError,
)
from app.features.artists.models import Artist, ArtistType
from app.features.images.models import ImageType, SharedImage
from app.features.notifications.models import Subscription, SubscriptionType
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
        raise ArtistNotFoundError()

    # 기존 구독 확인 (활성/비활성 모두)
    existing_subscription = await Subscription.filter(
        user=current_user, artist=artist
    ).first()

    if existing_subscription:
        if existing_subscription.is_active:
            # 상속 구독을 직접 구독으로 업그레이드
            if existing_subscription.subscription_type == SubscriptionType.INHERITED:
                existing_subscription.subscription_type = SubscriptionType.DIRECT
                await existing_subscription.save()
                return {"detail": "상속 구독이 직접 구독으로 변경되었습니다."}
            else:
                raise DuplicateSubscriptionError()
        else:
            # 비활성화된 구독이 있으면 다시 활성화 (직접 구독으로)
            existing_subscription.is_active = True
            existing_subscription.subscription_type = SubscriptionType.DIRECT
            await existing_subscription.save()
            return {"detail": "구독이 재활성화되었습니다."}
    else:
        # 새로운 구독 생성 (직접 구독)
        await Subscription.create(
            user=current_user, artist=artist, subscription_type=SubscriptionType.DIRECT
        )

        # 그룹을 구독한 경우, 해당 그룹의 멤버들도 자동 구독
        if artist.artist_type == ArtistType.GROUP:
            # parent_group 관계를 사용하여 멤버들 조회 (더 정확함)
            group_members = await Artist.filter(
                parent_group=artist,
                artist_type=ArtistType.INDIVIDUAL,
                is_active=True,
            )

            # parent_group이 설정되지 않은 경우 group_name으로 fallback
            if not group_members and artist.group_name:
                group_members = await Artist.filter(
                    group_name=artist.group_name,
                    artist_type=ArtistType.INDIVIDUAL,
                    is_active=True,
                )

            # 각 멤버에 대해 상속 구독 생성
            for member in group_members:
                # 이미 구독 중인지 확인
                existing_member_sub = await Subscription.filter(
                    user=current_user, artist=member
                ).first()

                if not existing_member_sub:
                    # 상속 구독 생성
                    await Subscription.create(
                        user=current_user,
                        artist=member,
                        subscription_type=SubscriptionType.INHERITED,
                    )
                elif not existing_member_sub.is_active:
                    # 비활성 구독이 있으면 상속으로 활성화 (DIRECT였으면 유지)
                    existing_member_sub.is_active = True
                    if existing_member_sub.subscription_type != SubscriptionType.DIRECT:
                        existing_member_sub.subscription_type = (
                            SubscriptionType.INHERITED
                        )
                    await existing_member_sub.save()
                # 이미 활성화된 구독이 있다면 (DIRECT든 INHERITED든) 건드리지 않음

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
                    stage_name=sub.artist.stage_name,
                    artist_image_url=face_image.url if face_image else None,
                    is_active=sub.is_active,
                    subscription_type=sub.subscription_type,
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
                    stage_name=sub.artist.stage_name,
                    is_active=sub.is_active,
                    subscription_type=sub.subscription_type,
                )
            )
        return result


@subscriptions_router.delete("/{artist_id}", response_model=dict)
async def cancel_subscription(
    artist_id: int, current_user: User = Depends(get_current_fan_user)
):
    """구독 취소"""
    try:
        sub = await Subscription.get(
            artist_id=artist_id, user=current_user, is_active=True
        )
        artist = await sub.artist

        # INHERITED 구독은 직접 취소 불가
        if sub.subscription_type == SubscriptionType.INHERITED:
            raise ValidationError(
                "상속된 구독은 직접 취소할 수 없습니다. 그룹 구독을 취소해주세요."
            )

        # 구독 취소
        sub.is_active = False
        await sub.save()

        # 그룹 구독을 취소한 경우, 상속된 멤버 구독들도 취소
        if (
            sub.subscription_type == SubscriptionType.DIRECT
            and artist.artist_type == ArtistType.GROUP
        ):
            # parent_group 관계를 사용하여 멤버들의 상속 구독 취소 (더 정확함)
            inherited_subscriptions = await Subscription.filter(
                user=current_user,
                subscription_type=SubscriptionType.INHERITED,
                is_active=True,
                artist__parent_group=artist,
                artist__artist_type=ArtistType.INDIVIDUAL,
            )

            # parent_group이 설정되지 않은 경우 group_name으로 fallback
            if not inherited_subscriptions and artist.group_name:
                inherited_subscriptions = await Subscription.filter(
                    user=current_user,
                    subscription_type=SubscriptionType.INHERITED,
                    is_active=True,
                    artist__group_name=artist.group_name,
                    artist__artist_type=ArtistType.INDIVIDUAL,
                )

            for inherited_sub in inherited_subscriptions:
                inherited_sub.is_active = False
                await inherited_sub.save()

        return {"detail": "구독 취소 완료"}
    except DoesNotExist:
        raise NotFoundError("구독 정보가 없습니다.") from None
