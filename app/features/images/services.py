from fastapi import HTTPException, UploadFile

from app.core.s3 import s3_handler
from app.features.images.models import SharedImage
from app.shared.utils import validate_image_extension


class ImageService:
    """이미지 서비스"""

    @staticmethod
    async def upload_image(
        file: UploadFile, entity_type: str, entity_id: int
    ) -> SharedImage:
        """이미지 업로드 및 DB 저장"""

        # 파일 확장자 검증
        if not file.filename or not validate_image_extension(file.filename):
            raise HTTPException(
                status_code=400, detail="지원하지 않는 이미지 형식입니다."
            )

        # S3에 파일 업로드
        file_url = await s3_handler.upload_file(file, folder=entity_type)
        if not file_url:
            raise HTTPException(status_code=500, detail="이미지 업로드에 실패했습니다.")

        # DB에 이미지 정보 저장
        image = await SharedImage.create(
            url=file_url,
            name=file.filename,
            size=file.size,
            content_type=file.content_type,
            entity_type=entity_type,
            entity_id=entity_id,
        )

        return image

    @staticmethod
    async def get_images_by_entity(
        entity_type: str, entity_id: int
    ) -> list[SharedImage]:
        """특정 엔티티의 이미지 목록 조회"""
        return await SharedImage.filter(
            entity_type=entity_type, entity_id=entity_id
        ).all()

    @staticmethod
    async def delete_image(image_id: int) -> bool:
        """이미지 삭제"""
        image = await SharedImage.get_or_none(id=image_id)
        if not image:
            return False

        # S3에서 파일 삭제
        s3_handler.delete_file(image.url)

        # DB에서 삭제
        await image.delete()
        return True
