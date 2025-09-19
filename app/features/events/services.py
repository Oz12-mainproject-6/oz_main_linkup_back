import io
from typing import BinaryIO

import pandas as pd
from fastapi import HTTPException, UploadFile
from loguru import logger
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from app.features.events.crud import EventCRUD
from app.features.events.models import EventCategory, EventVisibility
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
        _ws_info = wb.create_sheet("Information")
        _info_data = [
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
            ["category", "카테고리"](),
        ]
