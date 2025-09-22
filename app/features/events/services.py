import io
from datetime import datetime
from typing import BinaryIO

import pandas as pd
from fastapi import HTTPException, UploadFile
from loguru import logger
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from app.features.events.crud import EventCRUD
from app.features.events.models import EventCategory, EventVisibility
from app.features.events.notifications import notification_service
from app.features.events.schemas import FileUploadResponse


class EventService:
    """이벤트 비즈니스 로직 서비스"""

    @staticmethod
    async def process_upload_file(file: UploadFile) -> FileUploadResponse:
        """파일 업로드 처리"""
        try:
            contents = await file.read()

            if file.filename.endswith(".xlsx"):
                df = pd.read_excel(io.BytesIO(contents))
            elif file.filename.endswith(".csv"):
                df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
            else:
                raise ValueError("Unsupported file format")

            # 필수 컬럼 검증
            required_columns = ["artist_id", "title", "start_time", "category"]
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                raise ValueError(f"Missing columns: {', '.join(missing_columns)}")

            # 데이터 변환 및 검증
            events_data = []
            errors = []

            for index, row in df.iterrows():
                try:
                    start_time = pd.to_datetime(row["start_time"])
                    end_time = (
                        pd.to_datetime(row["end_time"])
                        if pd.notna(row.get("end_time"))
                        else None
                    )

                    event_data = {
                        "artist_id": int(row["artist_id"]),
                        "title": str(row["title"]).strip(),
                        "description": str(row.get("description", "")) or None,
                        "start_time": start_time,
                        "end_time": end_time,
                        "location": str(row.get("location", "")) or None,
                        "category": EventCategory(row["category"]),
                        "visibility": EventVisibility(
                            row.get("visibility", EventVisibility.PUBLIC)
                        ),
                    }

                    # 데이터 검증
                    if len(event_data["title"]) > 200:
                        raise ValueError("Title too long (max 200 characters)")
                    if event_data["location"] and len(event_data["location"]) > 200:
                        raise ValueError("Location too long (max 200 characters)")
                    if end_time and start_time >= end_time:
                        raise ValueError("End time must be after start time")

                    events_data.append(event_data)
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")

            # 일괄 생성
            created_count, creation_errors = await EventCRUD.bulk_create(events_data)
            all_errors = errors + creation_errors

            logger.info(
                f"File upload processed: {created_count}/{len(df)} events created"
            )

            return FileUploadResponse(
                message="File processed successfully",
                total_processed=len(df),
                successful=created_count,
                failed=len(df) - created_count,
                errors=all_errors[:10],
            )

        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"File processing error: {str(e)}"
            ) from e

    @staticmethod
    async def generate_template() -> BinaryIO:
        """업로드 템플릿 생성"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Events Template"

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(
            start_color="366092", end_color="366092", fill_type="solid"
        )
        header_alignment = Alignment(horizontal="center", vertical="center")

        headers = [
            "artist_id",
            "title",
            "description",
            "start_time",
            "end_time",
            "location",
            "category",
            "visibility",
        ]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        # 설명 시트 추가
        ws_info = wb.create_sheet("Information")
        info_data = [
            ["Column", "Description", "Required", "Example"],
            ["artist_id", "아티스트 ID (정수)", "Yes", "1"],
            ["title", "이벤트 제목 (최대 200자)", "Yes", "2024 콘서트"],
            ["description", "이벤트 설명", "No", "특별한 콘서트 이벤트"],
            [
                "start_time",
                "시작 시간 (YYYY-MM-DD HH:MM:SS)",
                "Yes",
                "2024-12-25 19:00:00",
            ],
            [
                "end_time",
                "종료 시간 (YYYY-MM-DD HH:MM:SS)",
                "No",
                "2024-12-25 22:00:00",
            ],
            ["location", "위치 (최대 200자)", "No", "올림픽공원"],
            ["category", "카테고리", "Yes", "concert, fanmeeting, showcase, etc."],
            ["visibility", "공개 설정", "No", "public, private, subscribers_only"],
        ]

        for row, data in enumerate(info_data, 1):
            for col, value in enumerate(data, 1):
                cell = ws_info.cell(row=row, column=col, value=value)
                if row == 1:  # 헤더
                    cell.font = header_font
                    cell.fill = header_fill

        # 샘플 데이터 (메인 시트에)
        sample_data = [
            [
                1,
                "Sample Concert",
                "Sample Description",
                "2024-12-25 19:00:00",
                "2024-12-25 22:00:00",
                "Seoul Olympic Park",
                "concert",
                "public",
            ],
            [
                1,
                "Fan Meeting",
                "Meet & Greet Event",
                "2024-12-30 15:00:00",
                "2024-12-30 17:00:00",
                "Coex Hall",
                "fanmeeting",
                "subscribers_only",
            ],
        ]

        for row, data in enumerate(sample_data, 2):
            for col, value in enumerate(data, 1):
                ws.cell(row=row, column=col, value=value)

        # 컬럼 너비 조정
        for sheet in [ws, ws_info]:
            for column in sheet.columns:
                max_length = max(len(str(cell.value or "")) for cell in column)
                sheet.column_dimensions[column[0].column_letter].width = min(
                    max_length + 2, 25
                )

        # 바이트 스트림으로 변환
        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)

        return stream

    @staticmethod
    async def export_to_excel(
        artist_id: int | None = None,
        category: EventCategory | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> BinaryIO:
        """이벤트 데이터 엑셀 내보내기"""
        # 날짜 파싱
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        # 데이터 조회
        events, _ = await EventCRUD.get_list(
            limit=10000,
            artist_id=artist_id,
            category=category,
            start_date=start_dt,
            end_date=end_dt,
        )

        # 데이터 변환
        data = []
        for event in events:
            data.append(
                {
                    "ID": event.id,
                    "Artist ID": event.artist_id,
                    "Title": event.title,
                    "Description": event.description or "",
                    "Start Time": event.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "End Time": event.end_time.strftime("%Y-%m-%d %H:%M:%S")
                    if event.end_time
                    else "",
                    "Location": event.location or "",
                    "Category": event.category.value,
                    "Visibility": event.visibility.value,
                    "Instant Notification Sent": event.instant_notification_sent,
                    "One Hour Notification Sent": event.one_hour_notification_sent,
                    "Is Active": event.is_active,
                    "Created At": event.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "Updated At": event.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        # DataFrame 생성 및 엑셀 변환
        df = pd.DataFrame(data)

        stream = io.BytesIO()
        with pd.ExcelWriter(stream, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Events", index=False)

            # 스타일링
            _ = writer.book  # workbook variable not used
            worksheet = writer.sheets["Events"]

            # 헤더 스타일
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(
                start_color="366092", end_color="366092", fill_type="solid"
            )

            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", vertical="center")

            # 컬럼 너비 조정
            for column in worksheet.columns:
                max_length = max(len(str(cell.value or "")) for cell in column)
                worksheet.column_dimensions[column[0].column_letter].width = min(
                    max_length + 2, 25
                )

        stream.seek(0)
        logger.info(f"Excel export completed: {len(data)} events exported")
        return stream

    @staticmethod
    async def trigger_notifications():
        """알림 트리거 - 더 안전한 처리"""
        try:
            # 데이터베이스 연결 확인
            from tortoise import Tortoise

            if not Tortoise.get_connection("default"):
                logger.warning(
                    "Database connection not available, skipping notifications"
                )
                return

            # 즉시 알림
            instant_events = await EventCRUD.get_upcoming_events(hours_ahead=0)
            instant_success = 0

            for event in instant_events:
                try:
                    await notification_service.send_instant_notification(event)
                    await EventCRUD.mark_notification_sent(event.id, "instant")
                    instant_success += 1
                except Exception as e:
                    logger.error(
                        f"Failed to send instant notification for event {event.id}: {str(e)}"
                    )

            # 1시간 전 알림
            upcoming_events = await EventCRUD.get_upcoming_events(hours_ahead=1)
            upcoming_success = 0

            for event in upcoming_events:
                try:
                    await notification_service.send_upcoming_notification(event)
                    await EventCRUD.mark_notification_sent(event.id, "one_hour")
                    upcoming_success += 1
                except Exception as e:
                    logger.error(
                        f"Failed to send upcoming notification for event {event.id}: {str(e)}"
                    )

            logger.info(
                f"Notifications completed: {instant_success}/{len(instant_events)} instant, {upcoming_success}/{len(upcoming_events)} upcoming"
            )

        except Exception as e:
            logger.error(f"Notification trigger failed: {str(e)}")

    @staticmethod
    async def get_event_statistics():
        """이벤트 통계 조회"""
        # 전체 이벤트 수
        total_events, _ = await EventCRUD.get_list(limit=1)

        # 카테고리별 통계 (추후 구현 예정)
        return {"total_events": len(total_events)}
