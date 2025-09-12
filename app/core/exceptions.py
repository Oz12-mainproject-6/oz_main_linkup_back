from fastapi import HTTPException
from typing import Optional


class BaseAPIException(HTTPException):
    """기본 API 예외 클래스"""
    
    def __init__(self, detail: str, status_code: int = 400, headers: Optional[dict] = None):
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