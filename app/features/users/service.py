import os
import traceback
from datetime import UTC, datetime
from urllib.parse import unquote

import httpx
from fastapi import HTTPException, Response, status

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
    PasswordChangeRequest,
    SendVerificationEmailRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)


class UserService:
    """사용자 관련 비즈니스 로직을 처리하는 서비스 클래스"""

    @staticmethod
    async def signup(request: SignupRequest) -> UserResponse:
        """회원가입 처리"""
        # 활성 계정 확인
        existing_active_user = await User.filter(
            email=request.email, deleted_at__isnull=True
        ).first()
        if existing_active_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다.",
            )

        # 탈퇴한 계정 확인 (original_email로 찾기)
        existing_deleted_user = await User.filter(
            original_email=request.email, deleted_at__isnull=False
        ).first()
        if existing_deleted_user:
            return await UserService._reactivate_deleted_account(
                existing_deleted_user, request
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

    @staticmethod
    async def login(request: LoginRequest, response: Response) -> TokenResponse:
        """일반 로그인 처리"""
        # 사용자 조회
        user = await User.filter(email=request.email).first()
        if not user or not verify_password(request.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 잘못되었습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 탈퇴한 계정 확인
        if user.deleted_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="탈퇴한 계정입니다. 다시 가입해주세요.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 밴 유저 확인
        if user.user_type == UserType.BAN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="계정이 차단되어 서비스를 이용할 수 없습니다.",
            )

        # JWT 토큰 생성
        access_token = create_access_token(data={"sub": str(user.id)})

        # 마지막 로그인 시간 업데이트
        user.last_login_at = datetime.now(UTC)
        await user.save()

        return TokenResponse(access_token=access_token)

    # @staticmethod
    # async def social_login(request: SocialLoginRequest) -> TokenResponse:
    #     """소셜 로그인 처리"""
    #     try:
    #         # OAuth 제공자에서 사용자 정보 가져오기
    #         user_info = await get_oauth_user_info(
    #             request.provider, request.access_token
    #         )
    #         if not user_info:
    #             raise HTTPException(
    #                 status_code=status.HTTP_401_UNAUTHORIZED,
    #                 detail="소셜 로그인 토큰이 유효하지 않습니다.",
    #             )
    #
    #         # 기존 사용자 확인
    #         user = await User.filter(
    #             oauth_provider=user_info["provider"], oauth_id=user_info["oauth_id"]
    #         ).first()
    #
    #         # 탈퇴한 계정 확인
    #         if user and user.deleted_at:
    #             raise HTTPException(
    #                 status_code=status.HTTP_401_UNAUTHORIZED,
    #                 detail="탈퇴한 계정입니다. 다시 가입해주세요.",
    #             )
    #
    #         if not user:
    #             user = await UserService._create_or_link_social_user(
    #                 user_info, request.user_type
    #             )
    #
    #         # 마지막 로그인 시간 업데이트
    #         user.last_login_at = datetime.now(UTC)
    #         await user.save()
    #
    #         # JWT 토큰 생성
    #         access_token = UserService._create_jwt_token(user)
    #         return TokenResponse(access_token=access_token)
    #
    #     except HTTPException:
    #         raise
    #     except Exception as e:
    #         print(f"Social login error: {type(e).__name__}: {str(e)}")
    #         import traceback
    #
    #         traceback.print_exc()
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail="소셜 로그인 처리 중 오류가 발생했습니다.",
    #         ) from e

    @staticmethod
    async def _create_or_link_social_user(user_info: dict, user_type: UserType) -> User:
        """소셜 로그인 사용자 생성 또는 기존 계정 연동"""
        # 이메일로도 확인 (기존 계정과 연동) - 이메일이 있는 경우에만
        if user_info.get("email"):
            existing_user = await User.filter(email=user_info["email"]).first()
            if existing_user:
                # 기존 계정에 소셜 정보 연동
                existing_user.oauth_provider = user_info["provider"]
                existing_user.oauth_id = user_info["oauth_id"]
                await existing_user.save()
                return existing_user
            else:
                # 새 사용자 생성 (이메일 있음)
                return await User.create(
                    email=user_info.get("email"),
                    password="",  # 소셜 로그인은 비밀번호 없음
                    nickname=user_info.get("name"),
                    user_type=user_type,
                    oauth_provider=user_info["provider"],
                    oauth_id=user_info["oauth_id"],
                    is_email_verified=True,  # 소셜 로그인은 이메일 인증된 것으로 처리
                )
        else:
            # 이메일 없이 새 사용자 생성
            temp_email = (
                f"{user_info['provider']}_{user_info['oauth_id']}@temp.linkup.com"
            )
            return await User.create(
                email=temp_email,
                password="",  # 소셜 로그인은 비밀번호 없음
                nickname=user_info.get("name", "사용자"),
                user_type=user_type,
                oauth_provider=user_info["provider"],
                oauth_id=user_info["oauth_id"],
                is_email_verified=False,  # 실제 이메일이 없으므로 인증되지 않음
            )

    @staticmethod
    def _create_jwt_token(user: User) -> str:
        """JWT 토큰 생성"""
        user_type_value = (
            user.user_type.value
            if hasattr(user.user_type, "value")
            else str(user.user_type)
        )
        # 임시 이메일인 경우 JWT에서 제외하거나 null로 처리
        email_for_jwt = (
            user.email if not user.email.endswith("@temp.linkup.com") else None
        )
        return create_access_token(
            data={
                "sub": str(user.id),
                "email": email_for_jwt,
                "user_type": user_type_value,
            }
        )

    @staticmethod
    async def send_verification_email(
        request: SendVerificationEmailRequest,
    ) -> EmailVerificationResponse:
        """이메일 인증 코드 전송"""
        # 기존 사용자 확인 (활성 계정만)
        existing_user = await User.filter(
            email=request.email, deleted_at__isnull=True
        ).first()
        if existing_user and existing_user.is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 인증된 이메일입니다.",
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

    @staticmethod
    async def verify_email(request: VerifyEmailRequest) -> EmailVerificationResponse:
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

    @staticmethod
    def get_oauth_redirect_url(provider: str, user_type: str = "fan") -> str:
        """OAuth 로그인 리다이렉트 URL 생성"""
        if provider == "kakao":
            client_id = os.getenv("KAKAO_CLIENT_ID")
            redirect_uri = "https://linkup.p-e.kr/api/auth/kakao/callback"
            return f"https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=profile_nickname,account_email&state={user_type}"
        elif provider == "google":
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            redirect_uri = "https://linkup.p-e.kr/api/auth/google/callback"
            return f"https://accounts.google.com/o/oauth2/auth?client_id={client_id}&redirect_uri={redirect_uri}&scope=openid email profile&response_type=code&access_type=offline&state={user_type}"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="지원하지 않는 OAuth 제공자입니다.",
            )

    @staticmethod
    async def handle_oauth_callback(
        provider: str, code: str, user_type: str = "fan"
    ) -> str:
        """OAuth 콜백 처리 및 프론트엔드 리다이렉트 URL 반환"""
        try:
            # URL 디코딩 처리
            code = unquote(code.strip())
            if not code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Authorization code가 필요합니다.",
                )

            # 토큰 요청
            access_token = await UserService._get_oauth_access_token(provider, code)

            # 소셜 로그인 처리
            user_info = await get_oauth_user_info(provider, access_token)
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="소셜 로그인 토큰이 유효하지 않습니다.",
                )

            # 기존 사용자 확인
            user = await User.filter(
                oauth_provider=user_info["provider"], oauth_id=user_info["oauth_id"]
            ).first()

            # 탈퇴한 계정 확인
            if user and user.deleted_at:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="탈퇴한 계정입니다. 다시 가입해주세요.",
                )

            if not user:
                user_type_enum = (
                    UserType.FAN if user_type == "fan" else UserType.COMPANY
                )
                user = await UserService._create_or_link_social_user(
                    user_info, user_type_enum
                )

            # 마지막 로그인 시간 업데이트 및 소셜 토큰 저장
            user.last_login_at = datetime.now(UTC)
            user.oauth_access_token = access_token
            await user.save()

            # JWT 토큰 생성
            jwt_token = UserService._create_jwt_token(user)

            # 프론트엔드 리다이렉트 URL 생성
            frontend_url = os.getenv("FRONTEND_URL")
            return f"{frontend_url}/?access_token={jwt_token}&token_type=Bearer"

        except HTTPException:
            raise
        except Exception as e:
            print(f"{provider.title()} callback error: {type(e).__name__}: {str(e)}")

            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{provider} 로그인 처리 중 오류가 발생했습니다.",
            ) from e

    @staticmethod
    async def _get_oauth_access_token(provider: str, code: str) -> str:
        """OAuth 제공자로부터 액세스 토큰 가져오기"""
        async with httpx.AsyncClient() as client:
            if provider == "kakao":
                token_response = await client.post(
                    "https://kauth.kakao.com/oauth/token",
                    data={
                        "grant_type": "authorization_code",
                        "client_id": os.getenv("KAKAO_CLIENT_ID"),
                        "client_secret": os.getenv("KAKAO_CLIENT_SECRET"),
                        "redirect_uri": "https://linkup.p-e.kr/api/auth/kakao/callback",
                        "code": code,
                    },
                )
            elif provider == "google":
                token_response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "grant_type": "authorization_code",
                        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                        "redirect_uri": "https://linkup.p-e.kr/api/auth/google/callback",
                        "code": code,
                    },
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="지원하지 않는 OAuth 제공자입니다.",
                )

            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="토큰 요청 실패"
                )

            token_data = token_response.json()
            return token_data["access_token"]

    @staticmethod
    async def change_password(user: User, request: PasswordChangeRequest) -> dict:
        """비밀번호 변경"""
        # 소셜 로그인 사용자는 비밀번호 변경 불가
        if user.oauth_provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="소셜 로그인 사용자는 비밀번호를 변경할 수 없습니다.",
            )

        # 현재 비밀번호 확인
        if not verify_password(request.current_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재 비밀번호가 올바르지 않습니다.",
            )

        # 새 비밀번호 확인
        if request.new_password != request.new_password_confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="새 비밀번호와 확인 비밀번호가 일치하지 않습니다.",
            )

        # 새 비밀번호가 현재와 동일한지 확인
        if verify_password(request.new_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="새 비밀번호는 현재 비밀번호와 달라야 합니다.",
            )

        # 비밀번호 해시화 및 저장
        user.password = get_password_hash(request.new_password)
        await user.save()

        return {"message": "비밀번호가 성공적으로 변경되었습니다."}

    @staticmethod
    async def delete_account(user: User, response: Response) -> dict:
        """회원 탈퇴 (soft delete with email masking)"""
        if user.deleted_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 탈퇴한 계정입니다.",
            )

        # 소셜 로그인 사용자인 경우 토큰 폐기
        if user.oauth_provider and user.oauth_access_token:
            await UserService.revoke_social_token(user)

        # 이메일 마스킹 처리
        masked_email = await UserService._mask_email_for_deletion(user.id, user.email)

        user.original_email = user.email  # 원본 이메일 보관
        user.email = masked_email
        user.deleted_at = datetime.now(UTC)
        await user.save()

        return {"message": "회원 탈퇴가 완료되었습니다. 토큰이 무효화되었습니다."}

    @staticmethod
    async def _mask_email_for_deletion(user_id: int, original_email: str) -> str:
        """탈퇴 시 이메일 마스킹 처리"""
        import time

        timestamp = int(time.time())
        return f"deleted_{user_id}_{timestamp}@deleted.linkup.com"

    @staticmethod
    async def _reactivate_deleted_account(
        existing_user: User, request: SignupRequest
    ) -> UserResponse:
        """탈퇴한 계정 재활용 (기존 데이터 유지)"""
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

        # 기존 계정 재활성화 (새 정보로 업데이트)
        existing_user.email = request.email  # 원래 이메일로 복구
        existing_user.original_email = None  # 원본 이메일 초기화 (활성 상태이므로)
        existing_user.password = get_password_hash(request.password)  # 새 비밀번호
        existing_user.nickname = request.nickname  # 새 닉네임
        existing_user.user_type = request.user_type  # 새 사용자 타입
        existing_user.deleted_at = None  # 탈퇴 상태 해제
        existing_user.is_email_verified = True  # 이메일 인증 완료
        existing_user.oauth_provider = None  # 소셜 로그인 정보 초기화
        existing_user.oauth_id = None
        await existing_user.save()

        return UserResponse(
            id=existing_user.id,
            email=existing_user.email,
            nickname=existing_user.nickname,
            user_type=existing_user.user_type,
            oauth_provider=existing_user.oauth_provider,
            is_email_verified=existing_user.is_email_verified,
        )

    @staticmethod
    async def revoke_social_token(user: User) -> dict:
        """소셜 로그인 토큰 폐기"""
        if not user.oauth_provider or not user.oauth_access_token:
            return {"message": "폐기할 소셜 토큰이 없습니다."}

        try:
            async with httpx.AsyncClient() as client:
                if user.oauth_provider == "kakao":
                    # 카카오 토큰 폐기
                    response = await client.post(
                        "https://kapi.kakao.com/v1/user/unlink",
                        headers={
                            "Authorization": f"Bearer {user.oauth_access_token}",
                            "Content-Type": "application/x-www-form-urlencoded",
                        },
                    )
                    
                elif user.oauth_provider == "google":
                    # 구글 토큰 폐기
                    response = await client.post(
                        f"https://oauth2.googleapis.com/revoke?token={user.oauth_access_token}",
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )

                # 토큰 폐기 성공 여부와 관계없이 DB에서 토큰 제거
                user.oauth_access_token = None
                await user.save()

                if response.status_code == 200:
                    return {"message": f"{user.oauth_provider} 토큰이 성공적으로 폐기되었습니다."}
                else:
                    return {"message": f"{user.oauth_provider} 토큰 폐기 요청을 보냈지만 응답이 예상과 다릅니다. DB에서는 제거되었습니다."}

        except Exception as e:
            # 오류가 발생해도 DB에서는 토큰 제거
            user.oauth_access_token = None
            await user.save()
            print(f"소셜 토큰 폐기 오류: {str(e)}")
            return {"message": f"토큰 폐기 중 오류가 발생했지만 DB에서는 제거되었습니다."}
