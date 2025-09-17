from fastapi import Depends, HTTPException, status

from app.features.users.dependencies import get_current_user
from app.features.users.models import Company, User, UserType


async def get_current_company_user(
    current_user: User = Depends(get_current_user),
) -> tuple[User, Company]:
    """현재 사용자가 소속사 계정인지 확인하고 Company 정보 반환"""

    if current_user.user_type != UserType.COMPANY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="소속사 계정만 접근 가능합니다.",
        )

    company = await Company.get_or_none(user=current_user)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="소속사 정보를 찾을 수 없습니다.",
        )

    return current_user, company
