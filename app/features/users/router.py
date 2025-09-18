import os
from datetime import UTC, datetime
from urllib.parse import unquote

import httpx
from fastapi import APIRouter, HTTPException, Response, status

from app.features.users.auth import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.features.users.email_service import email_service
from app.features.users.models import EmailVerification, User, UserType
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
async def login(request: LoginRequest, response: Response):
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

    # 쿠키에 토큰 설정 (개발 환경에서만)
    if os.getenv("ENVIRONMENT") == "development":
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=1800,  # 30분
            samesite="lax",
        )

    # 마지막 로그인 시간 업데이트
    user.last_login_at = datetime.now(UTC)
    await user.save()

    return TokenResponse(access_token=access_token)


@auth_router.post("/social-login", response_model=TokenResponse)
async def social_login(request: SocialLoginRequest):
    """소셜 로그인 (구글, 카카오)"""
    try:
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
            # 이메일로도 확인 (기존 계정과 연동) - 이메일이 있는 경우에만
            if user_info.get("email"):
                existing_user = await User.filter(email=user_info["email"]).first()
                if existing_user:
                    # 기존 계정에 소셜 정보 연동
                    existing_user.oauth_provider = user_info["provider"]
                    existing_user.oauth_id = user_info["oauth_id"]
                    await existing_user.save()
                    user = existing_user
                else:
                    # 새 사용자 생성 (이메일 있음)
                    user = await User.create(
                        email=user_info.get("email"),
                        password="",  # 소셜 로그인은 비밀번호 없음
                        nickname=user_info.get("name"),
                        user_type=request.user_type,
                        oauth_provider=user_info["provider"],
                        oauth_id=user_info["oauth_id"],
                        is_email_verified=True,  # 소셜 로그인은 이메일 인증된 것으로 처리
                    )
            else:
                # 이메일 없이 새 사용자 생성
                # 임시 이메일 생성: oauth_provider + oauth_id + @temp.linkup.com
                temp_email = (
                    f"{user_info['provider']}_{user_info['oauth_id']}@temp.linkup.com"
                )
                user = await User.create(
                    email=temp_email,
                    password="",  # 소셜 로그인은 비밀번호 없음
                    nickname=user_info.get("name", "사용자"),
                    user_type=request.user_type,
                    oauth_provider=user_info["provider"],
                    oauth_id=user_info["oauth_id"],
                    is_email_verified=False,  # 실제 이메일이 없으므로 인증되지 않음
                )

        # 마지막 로그인 시간 업데이트
        user.last_login_at = datetime.now(UTC)
        await user.save()

        # JWT 토큰 생성 - user_type 값 안전하게 처리
        user_type_value = (
            user.user_type.value
            if hasattr(user.user_type, "value")
            else str(user.user_type)
        )
        # 임시 이메일인 경우 JWT에서 제외하거나 null로 처리
        email_for_jwt = (
            user.email if not user.email.endswith("@temp.linkup.com") else None
        )
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": email_for_jwt,
                "user_type": user_type_value,
            }
        )

        return TokenResponse(access_token=access_token)

    except HTTPException:
        # HTTPException은 그대로 재발생
        raise
    except Exception as e:
        # 다른 모든 예외는 500 에러로 처리하고 로그에 기록
        print(f"Social login error: {type(e).__name__}: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="소셜 로그인 처리 중 오류가 발생했습니다.",
        ) from e


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


@auth_router.get("/kakao/login")
async def kakao_login(user_type: str = "fan"):
    """카카오 로그인 시작 - 카카오 로그인 페이지로 리다이렉트"""
    kakao_client_id = os.getenv("KAKAO_CLIENT_ID")
    redirect_uri = "http://localhost:8000/api/auth/kakao/callback"

    auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={kakao_client_id}&redirect_uri={redirect_uri}&response_type=code&scope=profile_nickname,account_email&state={user_type}"

    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=auth_url)


@auth_router.get("/google/login")
async def google_login(user_type: str = "fan"):
    """구글 로그인 시작 - 구글 로그인 페이지로 리다이렉트"""
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = "http://localhost:8000/api/auth/google/callback"

    auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={google_client_id}&redirect_uri={redirect_uri}&scope=openid email profile&response_type=code&access_type=offline&state={user_type}"

    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=auth_url)


@auth_router.get("/kakao/callback")
async def kakao_callback(code: str, user_type: str = "fan"):
    """카카오 OAuth 콜백 처리"""
    try:
        # URL 디코딩 처리
        code = unquote(code.strip())
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code가 필요합니다.",
            )

        # 토큰 요청
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://kauth.kakao.com/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": os.getenv("KAKAO_CLIENT_ID"),
                    "client_secret": os.getenv("KAKAO_CLIENT_SECRET"),
                    "redirect_uri": "http://localhost:8000/api/auth/kakao/callback",
                    "code": code,
                },
            )

            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="토큰 요청 실패"
                )

            token_data = token_response.json()
            access_token = token_data["access_token"]

            # 사용자 정보 요청
            user_response = await client.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="사용자 정보 요청 실패",
                )

        # 소셜 로그인 처리
        user_info = await get_oauth_user_info("kakao", access_token)
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
                    # 새 사용자 생성 (이메일 있음)
                    user = await User.create(
                        email=user_info.get("email"),
                        password="",  # 소셜 로그인은 비밀번호 없음
                        nickname=user_info.get("name"),
                        user_type=UserType.FAN
                        if user_type == "fan"
                        else UserType.COMPANY,
                        oauth_provider=user_info["provider"],
                        oauth_id=user_info["oauth_id"],
                        is_email_verified=True,  # 소셜 로그인은 이메일 인증된 것으로 처리
                    )
            else:
                # 이메일 없이 새 사용자 생성
                temp_email = (
                    f"{user_info['provider']}_{user_info['oauth_id']}@temp.linkup.com"
                )
                user = await User.create(
                    email=temp_email,
                    password="",
                    nickname=user_info.get("name", "카카오 사용자"),
                    user_type=UserType.FAN if user_type == "fan" else UserType.COMPANY,
                    oauth_provider=user_info["provider"],
                    oauth_id=user_info["oauth_id"],
                    is_email_verified=False,
                )

        # 마지막 로그인 시간 업데이트
        user.last_login_at = datetime.now(UTC)
        await user.save()

        # JWT 토큰 생성
        user_type_value = (
            user.user_type.value
            if hasattr(user.user_type, "value")
            else str(user.user_type)
        )
        email_for_jwt = (
            user.email if not user.email.endswith("@temp.linkup.com") else None
        )

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": email_for_jwt,
                "user_type": user_type_value,
            }
        )

        # 성공 페이지로 리다이렉트 (프론트엔드 URL)
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        redirect_url = f"{frontend_url}/auth/success?token={access_token}&user_id={user.id}&email={user.email}&nickname={user.nickname}"

        from fastapi.responses import RedirectResponse

        return RedirectResponse(url=redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Kakao callback error: {type(e).__name__}: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="카카오 로그인 처리 중 오류가 발생했습니다.",
        ) from e


@auth_router.get("/google/callback")
async def google_callback(code: str, user_type: str = "fan"):
    """구글 OAuth 콜백 처리"""
    try:
        # URL 디코딩 처리
        code = unquote(code.strip())
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code가 필요합니다.",
            )

        # 토큰 요청
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "redirect_uri": "http://localhost:8000/api/auth/google/callback",
                    "code": code,
                },
            )

            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="토큰 요청 실패"
                )

            token_data = token_response.json()
            access_token = token_data["access_token"]

        # 소셜 로그인 처리 (카카오와 동일한 로직)
        user_info = await get_oauth_user_info("google", access_token)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="소셜 로그인 토큰이 유효하지 않습니다.",
            )

        # 기존 사용자 확인 및 생성 로직 (카카오와 동일)
        user = await User.filter(
            oauth_provider=user_info["provider"], oauth_id=user_info["oauth_id"]
        ).first()

        if not user:
            if user_info.get("email"):
                existing_user = await User.filter(email=user_info["email"]).first()
                if existing_user:
                    existing_user.oauth_provider = user_info["provider"]
                    existing_user.oauth_id = user_info["oauth_id"]
                    await existing_user.save()
                    user = existing_user
                else:
                    user = await User.create(
                        email=user_info.get("email"),
                        password="",
                        nickname=user_info.get("name"),
                        user_type=UserType.FAN
                        if user_type == "fan"
                        else UserType.COMPANY,
                        oauth_provider=user_info["provider"],
                        oauth_id=user_info["oauth_id"],
                        is_email_verified=True,
                    )
            else:
                temp_email = (
                    f"{user_info['provider']}_{user_info['oauth_id']}@temp.linkup.com"
                )
                user = await User.create(
                    email=temp_email,
                    password="",
                    nickname=user_info.get("name", "구글 사용자"),
                    user_type=UserType.FAN if user_type == "fan" else UserType.COMPANY,
                    oauth_provider=user_info["provider"],
                    oauth_id=user_info["oauth_id"],
                    is_email_verified=False,
                )

        # JWT 토큰 생성 및 응답 (카카오와 동일)
        user.last_login_at = datetime.now(UTC)
        await user.save()

        user_type_value = (
            user.user_type.value
            if hasattr(user.user_type, "value")
            else str(user.user_type)
        )
        email_for_jwt = (
            user.email if not user.email.endswith("@temp.linkup.com") else None
        )

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": email_for_jwt,
                "user_type": user_type_value,
            }
        )

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        redirect_url = f"{frontend_url}/auth/success?token={access_token}&user_id={user.id}&email={user.email}&nickname={user.nickname}"

        from fastapi.responses import RedirectResponse

        return RedirectResponse(url=redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Google callback error: {type(e).__name__}: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="구글 로그인 처리 중 오류가 발생했습니다.",
        ) from e


@auth_router.post("/logout")
async def logout():
    return {"message": "로그아웃되었습니다."}
