import pytest
from httpx import AsyncClient

from app.features.artists.models import Artist
from app.features.users.models import User
from app.main import app

# pytest가 이 파일의 모든 테스트를 async 함수로 실행하도록 설정
pytestmark = pytest.mark.asyncio


async def test_create_post(client: AsyncClient):
    """
    포스트 생성 API 테스트
    """
    # 1. 테스트에 필요한 데이터 생성
    # - 포스트를 작성할 사용자
    user = await User.create(
        email="testuser@example.com",
        password="password",
        nickname="testuser",
    )
    # - 포스트가 속할 아티스트
    artist = await Artist.create(
        name="testartist",
        agency="test agency",
    )

    # 2. API 요청 데이터 준비
    post_data = {
        "artist_id": artist.id,
        "post_content": "This is a test post content.",
    }

    # 3. 포스트 생성 API 호출
    from app.features.users.dependencies import get_current_user

    async def override_get_current_user():
        return user

    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await client.post(
        "/api/posts/",
        data=post_data,
    )

    # 4. 응답 검증
    assert response.status_code == 200
    response_data = response.json()

    assert response_data["content"] == post_data["post_content"]
    assert response_data["user"]["id"] == user.id
    assert response_data["artist"]["id"] == artist.id
    assert "id" in response_data
    assert "created_at" in response_data

    # 의존성 오버라이드 복원
    app.dependency_overrides.clear()
