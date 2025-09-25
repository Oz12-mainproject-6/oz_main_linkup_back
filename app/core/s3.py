import os
import uuid

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile


class S3Handler:
    """AWS S3 파일 업로드 핸들러"""

    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "ap-northeast-2"),
        )
        self.bucket_name = os.getenv("AWS_S3_BUCKET")

    async def upload_file(self, file: UploadFile, folder: str = "images") -> str | None:
        """파일을 S3에 업로드하고 URL 반환"""
        try:
            # 고유한 파일명 생성
            file_extension = (
                file.filename.split(".")[-1]
                if file.filename and "." in file.filename
                else ""
            )
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            s3_key = f"{folder}/{unique_filename}"

            # S3에 파일 업로드
            file_content = await file.read()
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type or "application/octet-stream",
            )

            # 업로드된 파일의 URL 생성
            file_url = f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION', 'ap-northeast-2')}.amazonaws.com/{s3_key}"
            return file_url

        except ClientError as e:
            print(f"S3 업로드 실패: {e}")
            return None

    def delete_file(self, file_url: str) -> bool:
        """S3에서 파일 삭제"""
        try:
            # URL에서 S3 키 추출
            s3_key = file_url.split(f"{self.bucket_name}.s3")[-1].split("/")[-1]
            s3_key = file_url.split(".amazonaws.com/")[-1]

            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True

        except ClientError as e:
            print(f"S3 삭제 실패: {e}")
            return False


s3_handler = S3Handler()


# 이미지 타입별 폴더 상수
class S3Folders:
    FACE = "face"
    TORSO = "torso"
    BANNER = "banner"
    POST = "post"
    PROFILE = "profiles"
