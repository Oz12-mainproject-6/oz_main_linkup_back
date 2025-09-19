from datetime import datetime, timedelta

from tortoise.exceptions import DoesNotExist

from app.features.artists.models import Artist
from app.features.events.models import EventCategory, Events, EventVisibility


class EventCRUD:
    """이벤트 CRUD 클래스 (조회, 일괄 생성, 알림 관련만 남김)"""

    @staticmethod
    async def get_list(
        skip: int = 0,
        limit: int = 100,
        artist_parent_group: int | None = None,  # 🔹 Artist의 parent_group ID로 필터링
        artist_id: int | None = None,
        category: EventCategory | None = None,
        visibility: EventVisibility | None = None,
        is_active: bool = True,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[list[Events], int]:
        """이벤트 목록 조회"""
        query = Events.filter(is_active=is_active)

        # 🔹 artist_parent_group 필터 (Artist의 parent_group을 통해 필터링)
        if artist_parent_group is not None:
            query = query.filter(artist__parent_group=artist_parent_group)
        if artist_id:
            query = query.filter(artist_id=artist_id)
        if category:
            query = query.filter(category=category)
        if visibility:
            query = query.filter(visibility=visibility)
        if start_date:
            query = query.filter(start_time__gte=start_date)
        if end_date:
            query = query.filter(start_time__lte=end_date)

        total = await query.count()
        events = (
            await query.select_related("artist")  # 🔹 Artist만 join
            .offset(skip)
            .limit(limit)
            .order_by("-start_time")
        )

        return events, total

    @staticmethod
    async def get_by_id(event_id: int) -> Events | None:
        """이벤트 상세 조회"""
        try:
            return await Events.get(id=event_id).select_related("artist")
        except DoesNotExist:
            return None

    @staticmethod
    async def bulk_create(events_data: list[dict]) -> tuple[int, list[str]]:
        """일괄 이벤트 생성 - 트랜잭션 처리"""
        from tortoise.transactions import in_transaction

        created_count = 0
        errors = []

        try:
            async with in_transaction() as connection:
                for i, event_data in enumerate(events_data):
                    try:
                        # Artist 존재 확인
                        await Artist.get(
                            id=event_data["artist_id"], using_db=connection
                        )

                        await Events.create(**event_data, using_db=connection)
                        created_count += 1
                    except DoesNotExist:
                        errors.append(f"Row {i + 1}: Artist not found")
                    except Exception as e:
                        errors.append(f"Row {i + 1}: {str(e)}")
        except Exception as e:
            errors.append(f"Transaction failed: {str(e)}")

        return created_count, errors

    @staticmethod
    async def get_upcoming_events(hours_ahead: int = 1) -> list[Events]:
        """예정된 이벤트 조회 (알림용)"""
        now = datetime.now()
        target_time = now + timedelta(hours=hours_ahead)

        if hours_ahead == 1:
            return await Events.filter(
                start_time__lte=target_time,
                start_time__gt=now,
                one_hour_notification_sent=False,
                is_active=True,
                visibility__in=[
                    EventVisibility.PUBLIC,
                    EventVisibility.SUBSCRIBERS_ONLY,
                ],
            ).select_related("artist")
        else:
            return await Events.filter(
                instant_notification_sent=False,
                is_active=True,
                visibility__in=[
                    EventVisibility.PUBLIC,
                    EventVisibility.SUBSCRIBERS_ONLY,
                ],
            ).select_related("artist")

    @staticmethod
    async def get_events_by_date_range(
        start_date: datetime, end_date: datetime
    ) -> list[Events]:
        """날짜 범위로 이벤트 조회"""
        return (
            await Events.filter(
                start_time__gte=start_date, start_time__lte=end_date, is_active=True
            )
            .select_related("artist")
            .order_by("start_time")
        )

    @staticmethod
    async def mark_notification_sent(event_id: int, notification_type: str) -> bool:
        """알림 발송 상태 업데이트"""
        try:
            event = await Events.get(id=event_id)
            if notification_type == "instant":
                event.instant_notification_sent = True
            elif notification_type == "one_hour":
                event.one_hour_notification_sent = True
            await event.save()
            return True
        except DoesNotExist:
            return False
