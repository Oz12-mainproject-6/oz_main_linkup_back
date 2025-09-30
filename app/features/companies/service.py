from datetime import date, datetime, timedelta

from fastapi import UploadFile

from app.core.exceptions import NotFoundError, UploadFailedError, ValidationError
from app.core.s3 import s3_handler
from app.features.artists.models import Artist, ArtistType
from app.features.companies.schemas import (
    CompanyDashboardResponse,
    DashboardArtistInfo,
    DashboardEventInfo,
    EventCreateRequest,
    EventResponse,
    EventUpdateRequest,
)
from app.features.events.models import Events
from app.features.images.models import ImageType, SharedImage
from app.features.users.models import Company, User


class CompanyService:
    @staticmethod
    async def get_dashboard(company: Company) -> CompanyDashboardResponse:
        # 소속 아티스트 조회
        artists = await Artist.filter(company=company, is_active=True).all()

        # 최근 1년 이벤트 조회
        one_year_ago = datetime.now() - timedelta(days=365)
        recent_events = (
            await Events.filter(
                artist__company=company, start_time__gte=one_year_ago, is_active=True
            )
            .prefetch_related("artist")
            .order_by("-start_time")
            .limit(10)
        )

        # 아티스트별 이번 년 이벤트 수 계산
        artist_events_count: dict[int, int] = {}
        for event in recent_events:
            artist_id = event.artist.id
            artist_events_count[artist_id] = artist_events_count.get(artist_id, 0) + 1

        # 응답 데이터 구성
        dashboard_artists = []
        for artist in artists:
            dashboard_artists.append(
                DashboardArtistInfo(
                    id=artist.id,
                    stage_name=artist.stage_name,
                    group_name=artist.group_name,
                    artist_type=artist.artist_type,
                    debut_date=artist.debut_date,
                    is_active=artist.is_active,
                    event_count=artist_events_count.get(artist.id, 0),
                )
            )

        dashboard_events = []
        for event in recent_events:
            dashboard_events.append(
                DashboardEventInfo(
                    id=event.id,
                    title=event.title,
                    start_time=event.start_time,
                    end_time=event.end_time,
                    category=event.category,
                    artist_name=event.artist.stage_name
                    or event.artist.group_name
                    or f"Artist {event.artist.id}",
                    artist_stage_name=event.artist.stage_name,
                )
            )

        return CompanyDashboardResponse(
            company_name=company.name,
            artists=dashboard_artists,
            recent_events=dashboard_events,
            total_artists=len(artists),
            total_events=len(recent_events),
        )

    @staticmethod
    async def get_events(
        company: Company,
        artist_id: int | None = None,
        limit: int = 20,
        page: int = 1,
    ) -> list[EventResponse]:
        query = Events.filter(artist__company=company, is_active=True)

        if artist_id:
            # 해당 아티스트가 본인 소속사 것인지 확인
            artist = await Artist.get_or_none(id=artist_id, company=company)
            if not artist:
                raise NotFoundError("해당 아티스트를 찾을 수 없습니다.")
            query = query.filter(artist_id=artist_id)

        # offset 계산
        offset = (page - 1) * limit

        events = (
            await query.prefetch_related("artist")
            .order_by("-start_time")
            .offset(offset)
            .limit(limit)
        )

        return [
            EventResponse(
                id=event.id,
                title=event.title,
                description=event.description,
                start_time=event.start_time,
                end_time=event.end_time,
                location=event.location,
                category=event.category,
                visibility=event.visibility,
                is_active=event.is_active,
                artist_id=event.artist.id,
                artist_name=event.artist.stage_name
                or event.artist.group_name
                or f"Artist {event.artist.id}",
                artist_stage_name=event.artist.stage_name,
                created_at=event.created_at.isoformat(),
                updated_at=event.updated_at.isoformat(),
            )
            for event in events
        ]

    @staticmethod
    async def create_event(
        company: Company, request: EventCreateRequest
    ) -> EventResponse:
        # 해당 아티스트가 본인 소속사 것인지 확인
        artist = await Artist.get_or_none(id=request.artist_id, company=company)
        if not artist:
            raise NotFoundError("해당 아티스트를 찾을 수 없습니다.")

        event = await Events.create(
            artist=artist,
            title=request.title,
            description=request.description,
            start_time=request.start_time,
            end_time=request.end_time,
            location=request.location,
            category=request.category,
            visibility=request.visibility,
        )

        return EventResponse(
            id=event.id,
            title=event.title,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            location=event.location,
            category=event.category,
            visibility=event.visibility,
            is_active=event.is_active,
            artist_id=artist.id,
            artist_name=artist.stage_name or artist.group_name or f"Artist {artist.id}",
            artist_stage_name=artist.stage_name,
            created_at=event.created_at.isoformat(),
            updated_at=event.updated_at.isoformat(),
        )

    @staticmethod
    async def update_event(
        company: Company, event_id: int, request: EventUpdateRequest
    ) -> EventResponse:
        # 이벤트가 본인 소속사 것인지 확인
        event = (
            await Events.filter(id=event_id, artist__company=company, is_active=True)
            .prefetch_related("artist")
            .first()
        )

        if not event:
            raise NotFoundError("해당 이벤트를 찾을 수 없습니다.")

        # 수정할 필드만 업데이트
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(event, field, value)

        await event.save()

        return EventResponse(
            id=event.id,
            title=event.title,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            location=event.location,
            category=event.category,
            visibility=event.visibility,
            is_active=event.is_active,
            artist_id=event.artist.id,
            artist_name=event.artist.stage_name
            or event.artist.group_name
            or f"Artist {event.artist.id}",
            artist_stage_name=event.artist.stage_name,
            created_at=event.created_at.isoformat(),
            updated_at=event.updated_at.isoformat(),
        )

    @staticmethod
    async def delete_event(company: Company, event_id: int) -> dict[str, str]:
        # 이벤트가 본인 소속사 것인지 확인
        event = await Events.filter(
            id=event_id, artist__company=company, is_active=True
        ).first()

        if not event:
            raise NotFoundError("해당 이벤트를 찾을 수 없습니다.")

        # Soft delete
        event.is_active = False
        await event.save()

        return {"message": "이벤트가 삭제되었습니다."}

    @staticmethod
    async def get_artists(
        company: Company,
        is_active: bool | None = True,
        limit: int = 50,
        page: int = 1,
    ) -> list[DashboardArtistInfo]:
        query = Artist.filter(company=company)

        if is_active is not None:
            query = query.filter(is_active=is_active)

        # offset 계산
        offset = (page - 1) * limit

        artists = await query.order_by("-created_at").offset(offset).limit(limit)

        return [
            DashboardArtistInfo(
                id=artist.id,
                stage_name=artist.stage_name,
                group_name=artist.group_name,
                artist_type=artist.artist_type,
                birth_date=artist.birthdate,
                debut_date=artist.debut_date,
                is_active=artist.is_active,
                event_count=0,  # 필요시 별도 계산
            )
            for artist in artists
        ]

    @staticmethod
    async def get_artist_detail(
        company: Company, artist_id: int
    ) -> DashboardArtistInfo:
        # 해당 아티스트가 본인 소속사 것인지 확인
        artist = await Artist.get_or_none(id=artist_id, company=company)
        if not artist:
            raise NotFoundError("해당 아티스트를 찾을 수 없습니다.")

        # 각 타입별 이미지 조회
        face_image = await SharedImage.filter(
            artist=artist, image_type=ImageType.FACE
        ).first()

        torso_image = await SharedImage.filter(
            artist=artist, image_type=ImageType.TORSO
        ).first()

        banner_image = await SharedImage.filter(
            artist=artist, image_type=ImageType.BANNER
        ).first()

        return DashboardArtistInfo(
            id=artist.id,
            stage_name=artist.stage_name,
            group_name=artist.group_name,
            artist_type=artist.artist_type,
            birth_date=artist.birthdate,
            debut_date=artist.debut_date,
            is_active=artist.is_active,
            event_count=0,  # 필요시 별도 계산
            face_url=face_image.url if face_image else None,
            torso_url=torso_image.url if torso_image else None,
            banner_url=banner_image.url if banner_image else None,
        )

    @staticmethod
    async def create_artist_with_images(
        company: Company,
        current_user: User,
        stage_name: str | None = None,
        group_name: str | None = None,
        debut_date: date | None = None,
        birthdate: date | None = None,
        face_image: UploadFile | None = None,
        torso_image: UploadFile | None = None,
        banner_image: UploadFile | None = None,
    ) -> dict[str, str | int | None]:
        # stage_name 또는 group_name 중 하나는 필수
        if not stage_name and not group_name:
            raise ValidationError("stage_name 또는 group_name 중 하나는 필수입니다")
        # artist_type과 parent_group 자동 설정
        parent_group = None

        if group_name and not stage_name:
            # 그룹 (에스파)
            artist_type = ArtistType.GROUP
        elif group_name and stage_name:
            # 그룹 멤버 (카리나)
            artist_type = ArtistType.INDIVIDUAL
            # 같은 group_name을 가진 GROUP 찾기
            parent_group = await Artist.filter(
                group_name=group_name, artist_type=ArtistType.GROUP, is_active=True
            ).first()
        else:
            # 솔로 아티스트 (아이유)
            artist_type = ArtistType.INDIVIDUAL

        # 1. Artist 생성
        artist = await Artist.create(
            company=company,
            stage_name=stage_name,
            group_name=group_name,
            debut_date=debut_date,
            birthdate=birthdate,
            artist_type=artist_type,
            parent_group=parent_group,
        )

        # 2. 이미지 3개 업로드 및 SharedImage 생성 (선택사항)
        try:
            face_url = None
            torso_url = None
            banner_url = None

            # Face 이미지 업로드 (있는 경우에만)
            if face_image:
                face_url = await s3_handler.upload_file(face_image, folder="face")
                if face_url:
                    await SharedImage.create(
                        url=face_url,
                        name=face_image.filename,
                        size=face_image.size,
                        content_type=face_image.content_type,
                        uploaded_by=current_user,
                        artist=artist,
                        image_type=ImageType.FACE,
                    )

            # Torso 이미지 업로드 (있는 경우에만)
            if torso_image:
                torso_url = await s3_handler.upload_file(torso_image, folder="torso")
                if torso_url:
                    await SharedImage.create(
                        url=torso_url,
                        name=torso_image.filename,
                        size=torso_image.size,
                        content_type=torso_image.content_type,
                        uploaded_by=current_user,
                        artist=artist,
                        image_type=ImageType.TORSO,
                    )

            # Banner 이미지 업로드 (있는 경우에만)
            if banner_image:
                banner_url = await s3_handler.upload_file(banner_image, folder="banner")
                if banner_url:
                    await SharedImage.create(
                        url=banner_url,
                        name=banner_image.filename,
                        size=banner_image.size,
                        content_type=banner_image.content_type,
                        uploaded_by=current_user,
                        artist=artist,
                        image_type=ImageType.BANNER,
                    )

        except Exception as e:
            # 이미지 업로드 실패 시 아티스트도 삭제
            await artist.delete()
            raise UploadFailedError(f"이미지 업로드 실패: {str(e)}") from e

        return {
            "message": "아티스트 및 이미지가 성공적으로 생성되었습니다.",
            "artist_id": artist.id,
            "artist_name": artist.stage_name or artist.group_name,
            "face_image_url": face_url,
            "torso_image_url": torso_url,
            "banner_image_url": banner_url,
        }

    @staticmethod
    async def delete_artist(company: Company, artist_id: int) -> dict[str, str]:
        artist = await Artist.get_or_none(id=artist_id, company=company, is_active=True)
        if not artist:
            raise NotFoundError("해당 아티스트를 찾을 수 없습니다.")

        # 관련 이벤트도 함께 비활성화
        await Events.filter(artist=artist, is_active=True).update(is_active=False)

        # 아티스트 비활성화 (soft delete)
        artist.is_active = False
        await artist.save()

        return {"message": "아티스트가 삭제되었습니다. (관련 이벤트도 함께 삭제됨)"}

    @staticmethod
    async def update_artist_with_images_form(
        company: Company,
        current_user: User,
        artist_id: int,
        stage_name: str | None = None,
        group_name: str | None = None,
        debut_date: date | None = None,
        birthdate: date | None = None,
        artist_type: ArtistType | None = None,
        face_image: UploadFile | None = None,
        torso_image: UploadFile | None = None,
        banner_image: UploadFile | None = None,
    ):
        """아티스트 정보와 이미지 업데이트 (Form 방식, POST와 동일한 파라미터)"""

        # 아티스트 조회 및 권한 확인
        artist = await Artist.get_or_none(id=artist_id, company=company)
        if not artist:
            raise NotFoundError("해당 아티스트를 찾을 수 없습니다.")

        # stage_name 또는 group_name 중 하나는 필수 (업데이트 후 기준)
        final_stage_name = stage_name if stage_name is not None else artist.stage_name
        final_group_name = group_name if group_name is not None else artist.group_name

        if not final_stage_name and not final_group_name:
            raise ValidationError("stage_name 또는 group_name 중 하나는 필수입니다")

        # 아티스트 정보 업데이트 (None이 아닌 값만)
        if stage_name is not None:
            artist.stage_name = stage_name
        if group_name is not None:
            artist.group_name = group_name
        if debut_date is not None:
            artist.debut_date = debut_date
        if birthdate is not None:
            artist.birthdate = birthdate
        if artist_type is not None:
            artist.artist_type = artist_type

        await artist.save()

        # 이미지 업데이트 헬퍼 함수 (파일 업로드 방식)
        async def update_image(
            image_type: ImageType, new_image: UploadFile | None, folder: str
        ):
            if new_image and new_image.filename:
                # 기존 이미지 삭제
                existing_image = await SharedImage.filter(
                    artist=artist, image_type=image_type
                ).first()
                if existing_image:
                    # S3에서도 삭제
                    s3_handler.delete_file(existing_image.url)
                    await existing_image.delete()

                # 새 이미지 S3 업로드
                image_url = await s3_handler.upload_file(new_image, folder=folder)
                if image_url:
                    # 새 이미지 생성
                    await SharedImage.create(
                        url=image_url,
                        name=new_image.filename,
                        size=new_image.size,
                        content_type=new_image.content_type,
                        image_type=image_type,
                        uploaded_by=current_user,
                        artist=artist,
                    )

        # 각 이미지 타입별 업데이트
        await update_image(ImageType.FACE, face_image, "face")
        await update_image(ImageType.TORSO, torso_image, "torso")
        await update_image(ImageType.BANNER, banner_image, "banner")
