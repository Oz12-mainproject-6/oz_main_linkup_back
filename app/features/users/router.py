from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import RedirectResponse

from app.core.s3 import S3Folders, s3_handler
from app.features.users.dependencies import get_current_user
from app.features.users.models import User
from app.features.users.schemas import (
    EmailVerificationResponse,
    LoginRequest,
    PasswordChangeRequest,
    SendVerificationEmailRequest,
    SignupRequest,
    TokenResponse,
    UserMeResponse,
    UserMeWithPostsResponse,
    UserPostResponse,
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


# @auth_router.post("/social-login", response_model=TokenResponse)
# async def social_login(request: SocialLoginRequest):
#     """소셜 로그인 (구글, 카카오)"""
#     return await UserService.social_login(request)


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
async def logout(current_user: User = Depends(get_current_user)):
    """로그아웃 (소셜 토큰 폐기 포함)"""
    # 소셜 로그인 사용자인 경우 토큰 폐기
    if current_user.oauth_provider and current_user.oauth_access_token:
        result = await UserService.revoke_social_token(current_user)
        return result
    
    return {"message": "로그아웃되었습니다."}


@auth_router.get("/me", response_model=UserMeWithPostsResponse)
async def get_my_profile(
    include_posts: bool = Query(True, description="포스트 정보 포함 여부"),
    sort_by: str = Query(
        "latest", description="정렬 기준: latest(최신순), popular(좋아요순)"
    ),
    limit: int = Query(20, ge=1, le=100, description="포스트 조회 개수"),
    current_user: User = Depends(get_current_user),
):
    """내 프로필 조회 (포스트 포함)"""

    # 기본 프로필 정보
    profile_data = {
        "id": current_user.id,
        "email": current_user.email,
        "nickname": current_user.nickname,
        "profile_image_url": current_user.profile_image_url,
        "user_type": current_user.user_type,
        "is_social_login": bool(current_user.oauth_provider),  # 소셜로그인 여부
        "oauth_provider": current_user.oauth_provider,  # 소셜로그인 제공자 (kakao, google 등)
        "posts": [],
    }

    if not include_posts:
        return profile_data

    # 포스트 모델 import
    from app.features.artists.models import ArtistType
    from app.features.posts.models import Comment, Like, Post

    # 포스트 쿼리 구성
    posts_query = Post.filter(user=current_user).prefetch_related("artist")

    # 정렬 적용
    if sort_by == "popular":
        # 좋아요 수가 많은 순으로 정렬하려면 annotate가 필요하지만,
        # 현재는 간단하게 created_at 역순으로 하고 나중에 좋아요 수로 정렬
        posts = await posts_query.order_by("-created_at").limit(limit)
    else:  # latest
        posts = await posts_query.order_by("-created_at").limit(limit)

    # 각 포스트의 좋아요/댓글 수 계산
    post_responses = []
    for post in posts:
        likes_count = await Like.filter(post=post).count()
        comments_count = await Comment.filter(post=post).count()

        # 아티스트 이름 결정
        artist_name = None
        if post.artist:
            if post.artist.artist_type == ArtistType.GROUP:
                artist_name = post.artist.group_name
            else:
                artist_name = post.artist.stage_name

        post_responses.append(
            UserPostResponse(
                id=post.id,
                content=post.content,
                image_url=post.image_url,
                artist_id=post.artist.id,
                artist_name=artist_name,
                likes_count=likes_count,
                comments_count=comments_count,
                created_at=post.created_at,
                updated_at=post.updated_at,
            )
        )

    # 좋아요 수로 정렬이 요청된 경우 Python에서 정렬
    if sort_by == "popular":
        post_responses.sort(key=lambda x: x.likes_count, reverse=True)

    profile_data["posts"] = post_responses
    return profile_data


@auth_router.put("/me", response_model=UserMeResponse)
async def update_my_profile(
    nickname: str | None = None,
    profile_image: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
):
    """내 프로필 수정 (닉네임, 프로필 이미지)"""

    # 프로필 이미지 업로드 처리
    if profile_image:
        # 이미지 파일 유효성 검사
        if not profile_image.content_type or not profile_image.content_type.startswith(
            "image/"
        ):
            raise HTTPException(
                status_code=400, detail="이미지 파일만 업로드 가능합니다."
            )

        # 파일 크기 제한 (5MB)
        if profile_image.size and profile_image.size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=400, detail="파일 크기는 5MB 이하로 제한됩니다."
            )

        # 기존 이미지 삭제 (있다면)
        if current_user.profile_image_url:
            s3_handler.delete_file(current_user.profile_image_url)

        # 새 이미지 업로드
        image_url = await s3_handler.upload_file(profile_image, S3Folders.PROFILE)
        if not image_url:
            raise HTTPException(status_code=500, detail="이미지 업로드에 실패했습니다.")

        current_user.profile_image_url = image_url

    # 닉네임 업데이트
    if nickname is not None:
        current_user.nickname = nickname

    await current_user.save()
    return current_user


@auth_router.put("/me/password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
):
    """비밀번호 변경"""
    return await UserService.change_password(current_user, request)


@auth_router.delete("/me")
async def delete_my_account(
    current_user: User = Depends(get_current_user), response: Response = None
):
    """회원 탈퇴 (soft delete)"""
    return await UserService.delete_account(current_user, response)
