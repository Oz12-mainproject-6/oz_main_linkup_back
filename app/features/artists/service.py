from tortoise import models
from tortoise.functions import Count

from app.core.exceptions import ArtistNotFoundError
from app.features.artists.models import Artist
from app.features.artists.schemas import (
    ArtistListPaginationResponse,
    ArtistListResponse,
    ArtistResponse,
    ArtistSubscriptionInfo,
)
from app.features.images.models import ImageType, SharedImage
from app.features.notifications.models import Subscription
from app.features.users.models import User


class ArtistService:
    @staticmethod
    async def get_artist_list(
        artist_type: str | None = None,
        artist_name: str | None = None,
        artist_id: int | None = None,
        limit: int = 20,
        page: int = 1,
    ) -> ArtistListPaginationResponse:
        """아티스트 리스트 조회 (활성 상태만)"""

        # offset 계산
        offset = (page - 1) * limit

        # 기본 쿼리 (활성 상태만)
        query = Artist.filter(is_active=True)

        # 필터 적용
        if artist_type:
            query = query.filter(artist_type=artist_type)

        if artist_name:
            query = query.filter(
                models.Q(stage_name__icontains=artist_name)
                | models.Q(group_name__icontains=artist_name)
            )

        if artist_id:
            query = query.filter(id=artist_id)

        # 총 개수 조회
        total = await query.count()

        # 인기도 정렬 (구독자 수 기준) + 페이징
        artists = (
            await query.annotate(subscriber_count=Count("subscribers"))
            .order_by("-subscriber_count", "-created_at")
            .offset(offset)
            .limit(limit)
        )

        # 각 아티스트의 모든 이미지 URL 조회
        artist_list = []
        for artist in artists:
            artist_data = await ArtistService._build_artist_response(artist)
            artist_list.append(artist_data)

        # 다음 페이지 존재 여부
        has_next = (offset + limit) < total

        return ArtistListPaginationResponse(
            artists=artist_list,
            total=total,
            page=page,
            limit=limit,
            has_next=has_next,
        )

    @staticmethod
    async def get_subscribed_artists(
        user: User,
        limit: int = 20,
        page: int = 1,
    ) -> ArtistListPaginationResponse:
        """구독 중인 아티스트 리스트 조회"""

        # offset 계산
        offset = (page - 1) * limit

        # 구독 중인 아티스트 ID 조회
        subscribed_artist_ids = await Subscription.filter(
            user=user, is_active=True
        ).values_list("artist_id", flat=True)

        if not subscribed_artist_ids:
            return ArtistListPaginationResponse(
                artists=[], total=0, page=page, limit=limit, has_next=False
            )

        # 구독 중인 아티스트만 필터링 (활성 상태만)
        query = Artist.filter(id__in=subscribed_artist_ids, is_active=True)

        # 총 개수 조회
        total = await query.count()

        # 인기도 정렬 (구독자 수 기준) + 페이징
        artists = (
            await query.annotate(subscriber_count=Count("subscribers"))
            .order_by("-subscriber_count", "-created_at")
            .offset(offset)
            .limit(limit)
        )

        # 각 아티스트의 모든 이미지 URL 조회
        artist_list = []
        for artist in artists:
            artist_data = await ArtistService._build_artist_response(artist)
            artist_list.append(artist_data)

        # 다음 페이지 존재 여부
        has_next = (offset + limit) < total

        return ArtistListPaginationResponse(
            artists=artist_list,
            total=total,
            page=page,
            limit=limit,
            has_next=has_next,
        )

    @staticmethod
    async def get_artist_subscription_info(
        artist_name: str, user: User | None = None
    ) -> ArtistSubscriptionInfo:
        """구독 아티스트 확인"""

        # 아티스트 조회 (활성 상태만)
        artist = await Artist.filter(
            models.Q(stage_name__iexact=artist_name)
            | models.Q(group_name__iexact=artist_name)
            | models.Q(stage_name__icontains=artist_name)
            | models.Q(group_name__icontains=artist_name),
            is_active=True,
        ).first()

        if not artist:
            raise ArtistNotFoundError(f"아티스트 '{artist_name}'을 찾을 수 없습니다.")

        # 구독 여부 확인
        subscription = None
        if user:
            subscription = await Subscription.filter(user=user, artist=artist).first()

        return ArtistSubscriptionInfo(
            id=artist.id,
            stage_name=artist.stage_name,
            group_name=artist.group_name,
            artist_type=artist.artist_type,
            is_subscribed=subscription is not None,
            subscription_date=subscription.created_at.isoformat()
            if subscription
            else None,
        )

    @staticmethod
    async def _build_artist_response(artist: Artist) -> ArtistListResponse:
        """아티스트 응답 데이터 구성"""

        # 모든 이미지 타입 조회
        face_image = await SharedImage.filter(
            artist=artist, image_type=ImageType.FACE
        ).first()
        torso_image = await SharedImage.filter(
            artist=artist, image_type=ImageType.TORSO
        ).first()
        banner_image = await SharedImage.filter(
            artist=artist, image_type=ImageType.BANNER
        ).first()

        # 프로필 이미지는 FACE 우선, 없으면 TORSO 사용 (호환성을 위해)
        profile_image_url = None
        if face_image:
            profile_image_url = face_image.url
        elif torso_image:
            profile_image_url = torso_image.url

        return ArtistListResponse(
            id=artist.id,
            name=artist.stage_name or artist.group_name or f"Artist {artist.id}",
            profile_image=profile_image_url,
            face_url=face_image.url if face_image else None,
            torso_url=torso_image.url if torso_image else None,
            banner_url=banner_image.url if banner_image else None,
        )

    @staticmethod
    async def get_artist_detail(artist_name: str) -> ArtistResponse:
        """아티스트 상세 조회"""

        # 아티스트 조회 (활성 상태만)
        artist = await Artist.filter(
            models.Q(stage_name__iexact=artist_name)
            | models.Q(group_name__iexact=artist_name)
            | models.Q(stage_name__icontains=artist_name)
            | models.Q(group_name__icontains=artist_name),
            is_active=True,
        ).first()

        if not artist:
            raise ArtistNotFoundError(f"아티스트 '{artist_name}'을 찾을 수 없습니다.")

        # 기본 아티스트 데이터 빌드 (이미지 포함)
        artist_data = await ArtistService._build_artist_response(artist)

        return ArtistResponse(
            id=artist_data.id,
            stage_name=artist.stage_name,
            group_name=artist.group_name,
            birthdate=artist.birthdate,
            debut_date=artist.debut_date,
            artist_type=artist.artist_type,
            is_active=artist.is_active,
            profile_image=artist_data.profile_image,
            face_url=artist_data.face_url,
            torso_url=artist_data.torso_url,
            banner_url=artist_data.banner_url,
            created_at=artist.created_at.isoformat() if artist.created_at else None,
            updated_at=artist.updated_at.isoformat() if artist.updated_at else None,
        )
