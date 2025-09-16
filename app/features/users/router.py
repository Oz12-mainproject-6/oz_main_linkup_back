from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from app.features.users.auth import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.features.users.email_service import email_service
from app.features.users.models import EmailVerification, User
from app.features.users.oauth import get_oauth_user_info
from app.features.users.schemas import (
    EmailVerificationResponse,
    LoginRequest,
    SendVerificationEmailRequest,
    SignupRequest,
    SocialLoginRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
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

    # 이메일 인증 코드 확인
    verification = await EmailVerification.filter(
        email=request.email, code=request.verification_code, is_used=False
    ).first()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 인증 코드입니다.",
        )

    if not await verification.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증 코드가 만료되었습니다. 새로운 코드를 요청해주세요.",
        )

    # 인증 코드 사용 처리
    await verification.mark_as_used()

    # 비밀번호 해시화
    hashed_password = get_password_hash(request.password)

    # 사용자 생성 (이메일 인증 완료 상태로)
    user = await User.create(
        email=request.email,
        password=hashed_password,
        phone_number=request.phone_number,
        nickname=request.nickname,
        user_type=request.user_type,
        is_email_verified=True,  # 회원가입 시 이메일 인증 완료
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        user_type=user.user_type,
        oauth_provider=user.oauth_provider,
        is_email_verified=user.is_email_verified,
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


@auth_router.post("/social-login", response_model=TokenResponse)
async def social_login(request: SocialLoginRequest):
    """소셜 로그인 (구글, 카카오)"""
    # OAuth 제공자에서 사용자 정보 가져오기
    user_info = await get_oauth_user_info(request.provider, request.access_token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="소셜 로그인 토큰이 유효하지 않습니다.",
        )

    # 기존 사용자 확인
    user = await User.filter(
        oauth_provider=user_info["provider"], oauth_id=user_info["oauth_id"]
    ).first()

    if not user:
        # 이메일로도 확인 (기존 계정과 연동)
        if user_info.get("email"):
            existing_user = await User.filter(email=user_info["email"]).first()
            if existing_user:
                # 기존 계정에 소셜 정보 연동
                existing_user.oauth_provider = user_info["provider"]
                existing_user.oauth_id = user_info["oauth_id"]
                await existing_user.save()
                user = existing_user
            else:
                # 새 사용자 생성
                user = await User.create(
                    email=user_info.get("email"),
                    password="",  # 소셜 로그인은 비밀번호 없음
                    nickname=user_info.get("name"),
                    user_type=request.user_type,
                    oauth_provider=user_info["provider"],
                    oauth_id=user_info["oauth_id"],
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="소셜 계정에서 이메일 정보를 가져올 수 없습니다.",
            )

    # 마지막 로그인 시간 업데이트
    user.last_login_at = datetime.now(UTC)
    await user.save()

    # JWT 토큰 생성
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "user_type": user.user_type.value,
        }
    )

    return TokenResponse(access_token=access_token)


@auth_router.post("/send-verification-email", response_model=EmailVerificationResponse)
async def send_verification_email(request: SendVerificationEmailRequest):
    """이메일 인증 코드 전송"""
    # 기존 사용자 확인 (선택사항 - 회원가입 전에도 코드 전송 가능)
    existing_user = await User.filter(email=request.email).first()
    if existing_user and existing_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="이미 인증된 이메일입니다."
        )

    # 인증 코드 생성
    verification = await EmailVerification.create_verification_code(request.email)

    # 이메일 전송
    success = await email_service.send_verification_email(
        request.email, verification.code
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="이메일 전송에 실패했습니다. 잠시 후 다시 시도해주세요.",
        )

    return EmailVerificationResponse(
        message="인증 코드가 이메일로 전송되었습니다.", email=request.email
    )


@auth_router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(request: VerifyEmailRequest):
    """이메일 인증 코드 확인"""
    # 인증 코드 조회
    verification = await EmailVerification.filter(
        email=request.email, code=request.code, is_used=False
    ).first()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 인증 코드입니다.",
        )

    # 유효성 검사
    if not await verification.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증 코드가 만료되었습니다. 새로운 코드를 요청해주세요.",
        )

    # 인증 코드 사용 처리
    await verification.mark_as_used()

    # 기존 사용자가 있으면 인증 상태 업데이트
    user = await User.filter(email=request.email).first()
    if user:
        user.is_email_verified = True
        await user.save()

    return EmailVerificationResponse(
        message="이메일 인증이 완료되었습니다.", email=request.email
    )


@auth_router.post("/logout")
async def logout():
    return {"message": "로그아웃되었습니다."}
