from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

from app.features.users.auth import verify_token
from app.features.users.models import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """현재 사용자 조회 (JWT 토큰 기반)"""

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰에서 사용자 정보를 찾을 수 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await User.get_or_none(id=int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    return user


async def get_current_fan_user(current_user: User = Depends(get_current_user)) -> User:
    """팬 유저만 접근 가능"""
    from app.features.users.models import UserType

    if current_user.user_type != UserType.FAN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="팬 유저만 접근 가능합니다.",
        )
    return current_user


async def get_current_company_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """소속사 유저만 접근 가능 (기본 권한 체크만)"""
    from app.features.users.models import UserType

    if current_user.user_type != UserType.COMPANY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="소속사 유저만 접근 가능합니다.",
        )
    return current_user