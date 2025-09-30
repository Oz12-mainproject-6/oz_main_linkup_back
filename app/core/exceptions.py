from fastapi import HTTPException


class BaseAPIException(HTTPException):
    """기본 API 예외 클래스"""

    def __init__(
        self, detail: str, status_code: int = 400, headers: dict | None = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundError(BaseAPIException):
    """404 Not Found 예외"""

    def __init__(self, detail: str = "리소스를 찾을 수 없습니다"):
        super().__init__(detail=detail, status_code=404)


class ValidationError(BaseAPIException):
    """400 Bad Request 예외"""

    def __init__(self, detail: str = "잘못된 요청입니다"):
        super().__init__(detail=detail, status_code=400)


class UnauthorizedError(BaseAPIException):
    """401 Unauthorized 예외"""

    def __init__(self, detail: str = "인증이 필요합니다"):
        super().__init__(detail=detail, status_code=401)


class ForbiddenError(BaseAPIException):
    """403 Forbidden 예외"""

    def __init__(self, detail: str = "접근 권한이 없습니다"):
        super().__init__(detail=detail, status_code=403)


class ConflictError(BaseAPIException):
    """409 Conflict 예외"""

    def __init__(self, detail: str = "이미 존재하는 리소스입니다"):
        super().__init__(detail=detail, status_code=409)


class InternalServerError(BaseAPIException):
    """500 Internal Server Error 예외"""

    def __init__(self, detail: str = "서버 내부 오류가 발생했습니다"):
        super().__init__(detail=detail, status_code=500)


class FileProcessingError(BaseAPIException):
    """파일 처리 관련 예외"""

    def __init__(self, detail: str = "파일 처리 중 오류가 발생했습니다"):
        super().__init__(detail=detail, status_code=400)


class InvalidTokenError(UnauthorizedError):
    """토큰 관련 예외"""

    def __init__(self, detail: str = "유효하지 않은 토큰입니다"):
        super().__init__(detail=detail)


class DuplicateSubscriptionError(ConflictError):
    """중복 구독 예외"""

    def __init__(self, detail: str = "이미 구독 중입니다"):
        super().__init__(detail=detail)


class ArtistNotFoundError(NotFoundError):
    """아티스트 미발견 예외"""

    def __init__(self, detail: str = "아티스트를 찾을 수 없습니다"):
        super().__init__(detail=detail)


class PostNotFoundError(NotFoundError):
    """포스트 미발견 예외"""

    def __init__(self, detail: str = "게시글을 찾을 수 없습니다"):
        super().__init__(detail=detail)


class CommentNotFoundError(NotFoundError):
    """댓글 미발견 예외"""

    def __init__(self, detail: str = "댓글을 찾을 수 없습니다"):
        super().__init__(detail=detail)


class InvalidFileTypeError(ValidationError):
    """지원하지 않는 파일 형식 예외"""

    def __init__(self, detail: str = "지원하지 않는 파일 형식입니다"):
        super().__init__(detail=detail)


class UploadFailedError(InternalServerError):
    """업로드 실패 예외"""

    def __init__(self, detail: str = "업로드에 실패했습니다"):
        super().__init__(detail=detail)
