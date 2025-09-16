"""OAuth social login utilities."""

import os
from typing import Any

import httpx
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, status

# OAuth 설정
oauth = OAuth()

# Google OAuth 설정
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid_configuration",
    client_kwargs={"scope": "openid email profile"},
)

# Kakao OAuth 설정
oauth.register(
    name="kakao",
    client_id=os.getenv("KAKAO_CLIENT_ID"),
    client_secret=os.getenv("KAKAO_CLIENT_SECRET"),
    authorize_url="https://kauth.kakao.com/oauth/authorize",
    access_token_url="https://kauth.kakao.com/oauth/token",
    client_kwargs={"scope": "profile_nickname profile_image account_email"},
)


class OAuthProvider:
    """OAuth 제공자 상수"""

    GOOGLE = "google"
    KAKAO = "kakao"


async def get_google_user_info(access_token: str) -> dict[str, Any]:
    """Google 액세스 토큰으로 사용자 정보 조회"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="구글 사용자 정보를 가져올 수 없습니다",
            )

        return response.json()


async def get_kakao_user_info(access_token: str) -> dict[str, Any]:
    """Kakao 액세스 토큰으로 사용자 정보 조회"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="카카오 사용자 정보를 가져올 수 없습니다",
            )

        return response.json()


async def verify_google_token(token: str) -> dict[str, Any] | None:
    """Google ID 토큰 검증"""
    try:
        user_info = await get_google_user_info(token)
        return {
            "provider": OAuthProvider.GOOGLE,
            "oauth_id": user_info["id"],
            "email": user_info["email"],
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
        }
    except Exception:
        return None


async def verify_kakao_token(token: str) -> dict[str, Any] | None:
    """Kakao 액세스 토큰 검증"""
    try:
        user_info = await get_kakao_user_info(token)
        kakao_account = user_info.get("kakao_account", {})
        profile = kakao_account.get("profile", {})

        return {
            "provider": OAuthProvider.KAKAO,
            "oauth_id": str(user_info["id"]),
            "email": kakao_account.get("email"),
            "name": profile.get("nickname"),
            "picture": profile.get("profile_image_url"),
        }
    except Exception:
        return None


async def get_oauth_user_info(provider: str, token: str) -> dict[str, Any] | None:
    """OAuth 제공자별 사용자 정보 조회"""
    if provider == OAuthProvider.GOOGLE:
        return await verify_google_token(token)
    elif provider == OAuthProvider.KAKAO:
        return await verify_kakao_token(token)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="지원하지 않는 OAuth 제공자입니다",
        )
