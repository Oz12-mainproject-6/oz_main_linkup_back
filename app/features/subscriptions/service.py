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
from app.features.users.models import User

from .schemas import SubscriptionOut, SubscriptionWithImageOut


class SubscriptionService:
    """구독 관련 비즈니스 로직"""

    @staticmethod
    async def validate_artist_exists(artist_id: int) -> Artist:
        """아티스트 존재 확인"""
        artist = await Artist.get_or_none(id=artist_id)
        if not artist:
            raise ArtistNotFoundError()
        return artist

    @staticmethod
    async def get_existing_subscription(
        user: User, artist: Artist
    ) -> Subscription | None:
        """기존 구독 확인 (활성/비활성 모두)"""
        return await Subscription.filter(user=user, artist=artist).first()

    @staticmethod
    async def handle_existing_subscription(
        existing_subscription: Subscription, user: User, artist: Artist
    ) -> tuple[bool, str]:
        """기존 구독 처리 (업그레이드, 재활성화 등)"""
        if existing_subscription.is_active:
            # 상속 구독을 직접 구독으로 업그레이드
            if existing_subscription.subscription_type == SubscriptionType.INHERITED:
                existing_subscription.subscription_type = SubscriptionType.DIRECT
                await existing_subscription.save()
                return True, "상속 구독이 직접 구독으로 변경되었습니다."
            else:
                raise DuplicateSubscriptionError()
        else:
            # 비활성화된 구독이 있으면 다시 활성화 (직접 구독으로)
            existing_subscription.is_active = True
            existing_subscription.subscription_type = SubscriptionType.DIRECT
            await existing_subscription.save()
            return True, "구독이 재활성화되었습니다."

    @staticmethod
    async def create_new_subscription(user: User, artist: Artist):
        """새로운 구독 생성"""
        await Subscription.create(
            user=user, artist=artist, subscription_type=SubscriptionType.DIRECT
        )

    @staticmethod
    async def get_group_members(artist: Artist) -> list[Artist]:
        """그룹 멤버들 조회"""
        if artist.artist_type != ArtistType.GROUP:
            return []

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

        return group_members

    @staticmethod
    async def handle_member_subscription(user: User, member: Artist):
        """멤버 구독 처리 (상속 구독)"""
        existing_member_sub = await Subscription.filter(
            user=user, artist=member
        ).first()

        if not existing_member_sub:
            # 상속 구독 생성
            await Subscription.create(
                user=user,
                artist=member,
                subscription_type=SubscriptionType.INHERITED,
            )
        elif not existing_member_sub.is_active:
            # 비활성 구독이 있으면 상속으로 활성화 (DIRECT였으면 유지)
            existing_member_sub.is_active = True
            if existing_member_sub.subscription_type != SubscriptionType.DIRECT:
                existing_member_sub.subscription_type = SubscriptionType.INHERITED
            await existing_member_sub.save()
        # 이미 활성화된 구독이 있다면 (DIRECT든 INHERITED든) 건드리지 않음

    @staticmethod
    async def create_subscription(artist_id: int, user: User) -> dict:
        """구독 생성 (전체 로직)"""
        # 아티스트 존재 여부 확인
        artist = await SubscriptionService.validate_artist_exists(artist_id)

        # 기존 구독 확인
        existing_subscription = await SubscriptionService.get_existing_subscription(
            user, artist
        )

        is_resubscription = False
        if existing_subscription:
            (
                is_resubscription,
                message,
            ) = await SubscriptionService.handle_existing_subscription(
                existing_subscription, user, artist
            )
            if message != "구독이 재활성화되었습니다.":
                return {"detail": message}
        else:
            # 새로운 구독 생성
            await SubscriptionService.create_new_subscription(user, artist)

        # 그룹을 구독한 경우, 해당 그룹의 멤버들도 자동 구독
        group_members = await SubscriptionService.get_group_members(artist)
        for member in group_members:
            await SubscriptionService.handle_member_subscription(user, member)

        # 구독 완료 메시지 결정
        if is_resubscription:
            return {"detail": "구독이 재활성화되었습니다."}
        else:
            return {"detail": "구독이 완료되었습니다."}

    @staticmethod
    async def build_subscription_response(
        subscription: Subscription, include_image: bool = False
    ):
        """구독 응답 객체 생성"""
        if include_image:
            # 아티스트 FACE 이미지 조회
            face_image = await SharedImage.filter(
                artist=subscription.artist, image_type=ImageType.FACE
            ).first()

            return SubscriptionWithImageOut(
                id=subscription.id,
                artist_id=subscription.artist.id,
                group_name=subscription.artist.group_name,
                stage_name=subscription.artist.stage_name,
                artist_image_url=face_image.url if face_image else None,
                is_active=subscription.is_active,
                subscription_type=subscription.subscription_type,
            )
        else:
            return SubscriptionOut(
                id=subscription.id,
                artist_id=subscription.artist.id,
                group_name=subscription.artist.group_name,
                stage_name=subscription.artist.stage_name,
                is_active=subscription.is_active,
                subscription_type=subscription.subscription_type,
            )

    @staticmethod
    async def get_subscriptions(
        user: User,
        include_image: bool = False,
        group_name: str | None = None,
        stage_name: str | None = None,
    ):
        """구독 목록 조회"""
        # 기본 쿼리
        query = Subscription.filter(user=user, is_active=True)

        # 아티스트 이름 필터링
        if group_name:
            query = query.filter(artist__group_name__icontains=group_name)
        if stage_name:
            query = query.filter(artist__stage_name__icontains=stage_name)

        subscriptions = await query.prefetch_related("artist")

        result = []
        for sub in subscriptions:
            response = await SubscriptionService.build_subscription_response(
                sub, include_image
            )
            result.append(response)

        return result

    @staticmethod
    async def get_inherited_subscriptions_to_cancel(
        user: User, artist: Artist
    ) -> list[Subscription]:
        """취소할 상속 구독들 조회"""
        # parent_group 관계를 사용하여 멤버들의 상속 구독 취소 (더 정확함)
        inherited_subscriptions = await Subscription.filter(
            user=user,
            subscription_type=SubscriptionType.INHERITED,
            is_active=True,
            artist__parent_group=artist,
            artist__artist_type=ArtistType.INDIVIDUAL,
        )

        # parent_group이 설정되지 않은 경우 group_name으로 fallback
        if not inherited_subscriptions and artist.group_name:
            inherited_subscriptions = await Subscription.filter(
                user=user,
                subscription_type=SubscriptionType.INHERITED,
                is_active=True,
                artist__group_name=artist.group_name,
                artist__artist_type=ArtistType.INDIVIDUAL,
            )

        return inherited_subscriptions

    @staticmethod
    async def cancel_subscription(artist_id: int, user: User) -> dict:
        """구독 취소"""
        try:
            sub = await Subscription.get(artist_id=artist_id, user=user, is_active=True)
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
                inherited_subscriptions = (
                    await SubscriptionService.get_inherited_subscriptions_to_cancel(
                        user, artist
                    )
                )

                for inherited_sub in inherited_subscriptions:
                    inherited_sub.is_active = False
                    await inherited_sub.save()

            return {"detail": "구독 취소 완료"}
        except DoesNotExist:
            raise NotFoundError("구독 정보가 없습니다.") from None
