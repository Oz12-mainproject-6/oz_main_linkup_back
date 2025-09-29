from fastapi import APIRouter, Depends, HTTPException, Query, status
from tortoise import models
from tortoise.functions import Count

from app.features.artists.models import Artist
from app.features.artists.schemas import (
    ArtistListPaginationResponse,
    ArtistListResponse,
    ArtistResponse,
    ArtistSubscriptionInfo,
)
from app.features.images.models import ImageType, SharedImage
from app.features.notifications.models import Subscription
from app.features.users.dependencies import get_current_user
from app.features.users.models import User

idol_router = APIRouter(prefix="/api/idol", tags=["idol"])


@idol_router.get("", response_model=ArtistListPaginationResponse)
async def get_idol_list(
    artist_type: str | None = Query(
        None, description="아티스트 타입 필터 (group/individual)"
    ),
    is_active: bool | None = Query(
        None, description="구독 중인 아티스트만 조회 (true: 구독 중만, null: 전체)"
    ),
    limit: int = Query(20, ge=1, le=100, description="조회할 아티스트 수"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    current_user: User | None = Depends(get_current_user),
):
    """아이돌 리스트 조회 (활성 상태만)"""

    # offset 계산
    offset = (page - 1) * limit

    # 기본 쿼리 (활성 상태만)
    query = Artist.filter(is_active=True)

    # 필터 적용
    if artist_type:
        query = query.filter(artist_type=artist_type)
    
    # 구독 중인 아티스트만 필터링 (로그인된 사용자만)
    if is_active and current_user:
        subscribed_artist_ids = await Subscription.filter(
            user=current_user, is_active=True
        ).values_list("artist_id", flat=True)
        query = query.filter(id__in=subscribed_artist_ids)

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

        artist_list.append(
            ArtistListResponse(
                id=artist.id,
                name=artist.stage_name or artist.group_name or f"Artist {artist.id}",
                profile_image=profile_image_url,
                face_url=face_image.url if face_image else None,
                torso_url=torso_image.url if torso_image else None,
                banner_url=banner_image.url if banner_image else None,
            )
        )

    # 다음 페이지 존재 여부
    has_next = (offset + limit) < total

    return ArtistListPaginationResponse(
        artists=artist_list,
        total=total,
        page=page,
        limit=limit,
        has_next=has_next,
    )


@idol_router.get("/{artist_name}", response_model=ArtistResponse)
async def get_idol_detail(artist_name: str):
    """아이돌 상세 조회 (실명 또는 예명으로 검색, 활성 상태만)"""

    # 예명/그룹명으로 정확 검색 + 부분 검색 (활성 상태만)
    artist = await Artist.filter(
        models.Q(stage_name__iexact=artist_name)
        | models.Q(group_name__iexact=artist_name)
        | models.Q(stage_name__icontains=artist_name)
        | models.Q(group_name__icontains=artist_name),
        is_active=True,
    ).first()

    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"아티스트 '{artist_name}'을 찾을 수 없습니다.",
        )

    # 프로필 이미지 조회 (FACE 타입 우선)
    profile_image_url = None
    face_image = await SharedImage.filter(
        artist=artist, image_type=ImageType.FACE
    ).first()

    if face_image:
        profile_image_url = face_image.url
    else:
        # FACE가 없으면 TORSO 이미지 조회
        torso_image = await SharedImage.filter(
            artist=artist, image_type=ImageType.TORSO
        ).first()
        if torso_image:
            profile_image_url = torso_image.url

    return ArtistResponse(
        id=artist.id,
        stage_name=artist.stage_name,
        group_name=artist.group_name,
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
        profile_image=profile_image_url,
        created_at=artist.created_at.isoformat() if artist.created_at else None,
        updated_at=artist.updated_at.isoformat() if artist.updated_at else None,
    )


@idol_router.get("/{artist_name}/info", response_model=ArtistSubscriptionInfo)
async def get_idol_subscription_info(
    artist_name: str, current_user: User = Depends(get_current_user)
):
    """구독 아티스트 확인 (로그인 필요, 활성 상태만)"""

    # 아티스트 조회 (활성 상태만)
    artist = await Artist.filter(
        models.Q(stage_name__iexact=artist_name)
        | models.Q(group_name__iexact=artist_name)
        | models.Q(stage_name__icontains=artist_name)
        | models.Q(group_name__icontains=artist_name),
        is_active=True,
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
        stage_name=artist.stage_name,
        group_name=artist.group_name,
        artist_type=artist.artist_type,
        is_subscribed=subscription is not None,
        subscription_date=subscription.created_at.isoformat() if subscription else None,
    )
