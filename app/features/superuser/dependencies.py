from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.features.users.auth import verify_token
from app.features.users.models import User, UserType

security = HTTPBearer()


async def get_superuser_bypass_ban(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """슈퍼유저 인증 (밴 체크 없이)"""
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

    # 관리자 권한 체크
    if user.user_type not in [UserType.ADMIN, UserType.COMPANY]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="슈퍼유저만 접근 가능합니다.",
        )

    return user


async def get_superuser(current_user: User = Depends(get_superuser_bypass_ban)) -> User:
    """슈퍼유저만 접근 가능"""
    return current_user
