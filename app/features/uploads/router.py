from fastapi import APIRouter, Depends, File, UploadFile

from app.core.s3 import S3Folders, s3_handler
from app.features.artists.models import Artist
from app.features.images.models import ImageType, SharedImage
from app.features.users.dependencies import get_current_company_user, get_current_user
from app.features.users.models import User
from app.core.exceptions import ArtistNotFoundError, UploadFailedError

uploads_router = APIRouter(prefix="/api/uploads", tags=["Uploads"])


# 타입별 이미지 업로드 엔드포인트
@uploads_router.post("/face")
async def upload_face_image(
    artist_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_company_user),
):
    """얼굴 이미지 업로드 (소속사 계정만 가능)"""
    # 아티스트 존재 확인
    artist = await Artist.get_or_none(id=artist_id)
    if not artist:
        raise ArtistNotFoundError()

    # S3 업로드
    file_url = await s3_handler.upload_file(file, folder=S3Folders.FACE)
    if not file_url:
        raise UploadFailedError()

    # SharedImage 모델에 저장
    shared_image = await SharedImage.create(
        url=file_url,
        name=file.filename,
        size=file.size,
        content_type=file.content_type,
        uploaded_by=current_user,
        artist=artist,
        image_type=ImageType.FACE,
    )

    return {
        "message": "얼굴 이미지 업로드 성공",
        "file_url": file_url,
        "image_id": shared_image.id,
        "artist_name": artist.stage_name or artist.group_name,
    }


@uploads_router.post("/torso")
async def upload_torso_image(
    artist_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_company_user),
):
    """상반신 이미지 업로드 (소속사 계정만 가능)"""
    # 아티스트 존재 확인
    artist = await Artist.get_or_none(id=artist_id)
    if not artist:
        raise ArtistNotFoundError()

    # S3 업로드
    file_url = await s3_handler.upload_file(file, folder=S3Folders.TORSO)
    if not file_url:
        raise UploadFailedError()

    # SharedImage 모델에 저장
    shared_image = await SharedImage.create(
        url=file_url,
        name=file.filename,
        size=file.size,
        content_type=file.content_type,
        uploaded_by=current_user,
        artist=artist,
        image_type=ImageType.TORSO,
    )

    return {
        "message": "상반신 이미지 업로드 성공",
        "file_url": file_url,
        "image_id": shared_image.id,
        "artist_name": artist.stage_name or artist.group_name,
    }


@uploads_router.post("/banner")
async def upload_banner_image(
    artist_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_company_user),
):
    """배너 이미지 업로드 (소속사 계정만 가능)"""
    # 아티스트 존재 확인
    artist = await Artist.get_or_none(id=artist_id)
    if not artist:
        raise ArtistNotFoundError()

    # S3 업로드
    file_url = await s3_handler.upload_file(file, folder=S3Folders.BANNER)
    if not file_url:
        raise UploadFailedError()

    # SharedImage 모델에 저장
    shared_image = await SharedImage.create(
        url=file_url,
        name=file.filename,
        size=file.size,
        content_type=file.content_type,
        uploaded_by=current_user,
        artist=artist,
        image_type=ImageType.BANNER,
    )

    return {
        "message": "배너 이미지 업로드 성공",
        "file_url": file_url,
        "image_id": shared_image.id,
        "artist_name": artist.stage_name or artist.group_name,
    }


@uploads_router.post("/post")
async def upload_post_image(
    file: UploadFile = File(...), current_user: User = Depends(get_current_user)
):
    """포스트 이미지 업로드"""
    file_url = await s3_handler.upload_file(file, folder=S3Folders.POST)
    if not file_url:
        raise UploadFailedError()
    return {"message": "포스트 이미지 업로드 성공", "file_url": file_url}
