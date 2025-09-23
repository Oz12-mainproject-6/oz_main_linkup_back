from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse

from app.features.users.dependencies import get_current_user
from app.features.users.models import User
from app.features.users.schemas import (
    EmailVerificationResponse,
    LoginRequest,
    PasswordChangeRequest,
    SendVerificationEmailRequest,
    SignupRequest,
    SocialLoginRequest,
    TokenResponse,
    UserMeResponse,
    UserMeUpdateRequest,
    UserResponse,
    VerifyEmailRequest,
)
from app.features.users.service import UserService

auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])


@auth_router.post("/signup", response_model=UserResponse)
async def signup(request: SignupRequest):
    """회원가입"""
    return await UserService.signup(request)


@auth_router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, response: Response):
    """일반 로그인"""
    return await UserService.login(request, response)


@auth_router.post("/social-login", response_model=TokenResponse)
async def social_login(request: SocialLoginRequest):
    """소셜 로그인 (구글, 카카오)"""
    return await UserService.social_login(request)


@auth_router.post("/send-verification-email", response_model=EmailVerificationResponse)
async def send_verification_email(request: SendVerificationEmailRequest):
    """이메일 인증 코드 전송"""
    return await UserService.send_verification_email(request)


@auth_router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(request: VerifyEmailRequest):
    """이메일 인증 코드 확인"""
    return await UserService.verify_email(request)


@auth_router.get("/kakao/login")
async def kakao_login(user_type: str = "fan"):
    """카카오 로그인 시작 - 카카오 로그인 페이지로 리다이렉트"""
    auth_url = UserService.get_oauth_redirect_url("kakao", user_type)
    return RedirectResponse(url=auth_url)


@auth_router.get("/google/login")
async def google_login(user_type: str = "fan"):
    """구글 로그인 시작 - 구글 로그인 페이지로 리다이렉트"""
    auth_url = UserService.get_oauth_redirect_url("google", user_type)
    return RedirectResponse(url=auth_url)


@auth_router.get("/kakao/callback")
async def kakao_callback(code: str, user_type: str = "fan"):
    """카카오 OAuth 콜백 처리"""
    redirect_url = await UserService.handle_oauth_callback("kakao", code, user_type)
    return RedirectResponse(url=redirect_url)


@auth_router.get("/google/callback")
async def google_callback(code: str, user_type: str = "fan"):
    """구글 OAuth 콜백 처리"""
    redirect_url = await UserService.handle_oauth_callback("google", code, user_type)
    return RedirectResponse(url=redirect_url)


@auth_router.post("/logout")
async def logout():
    return {"message": "로그아웃되었습니다."}


@auth_router.get("/me", response_model=UserMeResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """내 프로필 조회"""
    return current_user


@auth_router.put("/me", response_model=UserMeResponse)
async def update_my_profile(
    request: UserMeUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    """내 프로필 수정"""
    return await UserService.update_profile(current_user, request)


@auth_router.put("/me/password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
):
    """비밀번호 변경"""
    return await UserService.change_password(current_user, request)


@auth_router.delete("/me", status_code=204)
async def delete_my_account(
    current_user: User = Depends(get_current_user), response: Response = None
):
    """회원 탈퇴 (soft delete)"""
    return await UserService.delete_account(current_user, response)
