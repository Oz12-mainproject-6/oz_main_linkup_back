from app.features.artists.models import Artist
from app.features.notifications.models import Subscription


class SubscriptionService:
    """구독 서비스"""

    @staticmethod
    async def subscribe_to_artist(user_id: int, artist_id: int) -> list[Subscription]:
        """아티스트 구독 (그룹인 경우 멤버들도 자동 구독)"""

        artist = await Artist.get(id=artist_id)
        subscriptions = []

        # 메인 아티스트 구독
        subscription, created = await Subscription.get_or_create(
            user_id=user_id, artist_id=artist_id
        )
        subscriptions.append(subscription)

        # 그룹인 경우 멤버들도 자동 구독
        if artist.artist_type == "group":
            members = await Artist.filter(parent_group_id=artist_id).all()

            for member in members:
                member_subscription, created = await Subscription.get_or_create(
                    user_id=user_id, artist_id=member.id
                )
                subscriptions.append(member_subscription)

        return subscriptions

    @staticmethod
    async def unsubscribe_from_artist(user_id: int, artist_id: int) -> bool:
        """아티스트 구독 해제 (그룹인 경우 멤버들도 함께 해제)"""

        artist = await Artist.get(id=artist_id)

        # 메인 아티스트 구독 해제
        await Subscription.filter(user_id=user_id, artist_id=artist_id).delete()

        # 그룹인 경우 멤버들 구독도 해제
        if artist.artist_type == "group":
            members = await Artist.filter(parent_group_id=artist_id).all()
            member_ids = [member.id for member in members]

            await Subscription.filter(
                user_id=user_id, artist_id__in=member_ids
            ).delete()

        return True

    @staticmethod
    async def get_user_subscriptions(user_id: int) -> list[Artist]:
        """사용자의 모든 구독 아티스트 조회 (그룹만, 멤버 제외)"""

        subscriptions = await Subscription.filter(user_id=user_id).prefetch_related(
            "artist"
        )

        # 그룹과 솔로만 반환 (멤버는 그룹 구독에 포함되므로 제외)
        artists = []
        for sub in subscriptions:
            if sub.artist.artist_type in ["group", "solo"]:
                artists.append(sub.artist)

        return artists
