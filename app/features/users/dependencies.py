from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.features.users.auth import verify_token
from app.features.users.models import User
from app.core.exceptions import (
    UnauthorizedError,
    InvalidTokenError,
    NotFoundError,
    ForbiddenError,
)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """현재 사용자 조회 (JWT 토큰 기반) - 밴 상태 체크 포함"""

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise InvalidTokenError()

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("토큰에서 사용자 정보를 찾을 수 없습니다.")

    user = await User.get_or_none(id=int(user_id))
    if not user:
        raise NotFoundError("사용자를 찾을 수 없습니다.")

    # 밴된 사용자 체크
    from app.features.users.models import UserType

    if user.user_type == UserType.BAN:
        raise ForbiddenError("계정이 차단되어 서비스를 이용할 수 없습니다.")

    return user


async def get_current_fan_user(current_user: User = Depends(get_current_user)) -> User:
    """팬 유저만 접근 가능"""
    from app.features.users.models import UserType

    if current_user.user_type != UserType.FAN:
        raise ForbiddenError("팬 유저만 접근 가능합니다.")
    return current_user


async def get_current_company_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """소속사 유저만 접근 가능 (기본 권한 체크만)"""
    from app.features.users.models import UserType

    if current_user.user_type != UserType.COMPANY:
        raise ForbiddenError("소속사 유저만 접근 가능합니다.")
    return current_user
