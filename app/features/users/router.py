from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from app.features.users.auth import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.features.users.models import User
from app.features.users.schemas import (
    LoginRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)

auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])


@auth_router.post("/signup", response_model=UserResponse)
async def signup(request: SignupRequest):
    # 이메일 중복 검사
    existing_user = await User.filter(email=request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="이미 등록된 이메일입니다."
        )

    # 비밀번호 해시화
    hashed_password = get_password_hash(request.password)

    # 사용자 생성
    user = await User.create(
        email=request.email,
        password=hashed_password,
        phone_number=request.phone_number,
        nickname=request.nickname,
        user_type=request.user_type,
    )

    return UserResponse(
        id=user.id, email=user.email, nickname=user.nickname, user_type=user.user_type
    )


@auth_router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    # 사용자 조회
    user = await User.filter(email=request.email).first()
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 잘못되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # JWT 토큰 생성
    access_token = create_access_token(data={"sub": str(user.id)})

    # 마지막 로그인 시간 업데이트
    user.last_login_at = datetime.now(UTC)
    await user.save()

    return TokenResponse(access_token=access_token)


@auth_router.post("/logout")
async def logout():
    return {"message": "로그아웃되었습니다."}
