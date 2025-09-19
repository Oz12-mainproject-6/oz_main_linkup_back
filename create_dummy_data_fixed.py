import asyncio
from datetime import datetime, timedelta

from tortoise import Tortoise

from app.config import TORTOISE_ORM
from app.features.artists.models import Artist, ArtistRole, ArtistType
from app.features.events.models import EventCategory, Events
from app.features.images.models import ImageType, SharedImage
from app.features.subscriptions.models import Subscription
from app.features.users.auth import get_password_hash
from app.features.users.models import Company, User, UserType


async def create_dummy_data():
    """완전한 더미 데이터 생성 스크립트"""
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        print("🎭 더미 데이터 생성 시작...")

        # 기존 더미 데이터 완전 삭제 (순서 중요)
        print("🧹 기존 데이터 정리...")
        await SharedImage.filter(name__contains="더미").delete()
        await Subscription.all().delete()  # 간단하게 모든 구독 삭제
        await Events.filter(title__contains="더미").delete()
        await Artist.filter(email__contains="dummy").delete()
        await Company.filter(contact_email__contains="dummy").delete()
        await User.filter(email__contains="dummy").delete()
        print("✅ 기존 데이터 정리 완료")

        # 1. 회사 사용자 생성
        print("👔 회사 사용자 생성 중...")
        company_users = []
        company_data = [
            ("SM엔터테인먼트", "sm_dummy@company.com"),
            ("YG엔터테인먼트", "yg_dummy@company.com"),
            ("JYP엔터테인먼트", "jyp_dummy@company.com"),
        ]

        for name, email in company_data:
            user = await User.create(
                email=email,
                password=get_password_hash("company123!"),
                nickname=f"{name} 매니저",
                user_type=UserType.COMPANY,
                is_email_verified=True,
            )
            company_users.append(user)
        print(f"✅ 회사 사용자 {len(company_users)}개 생성 완료")

        # 2. 회사 프로필 생성
        print("🏢 회사 프로필 생성 중...")
        companies = []
        for i, (user, (name, _)) in enumerate(
            zip(company_users, company_data, strict=False)
        ):
            company = await Company.create(
                user=user,
                name=name,
                contact_email=f"contact_dummy_{i + 1}@company.com",
                contact_phone=f"02-123-456{i + 1}",
                address=f"서울시 강남구 {name} 빌딩",
            )
            companies.append(company)
        print(f"✅ 회사 프로필 {len(companies)}개 생성 완료")

        # 3. 팬 사용자 생성
        print("👥 팬 사용자 생성 중...")
        fan_users = []
        fan_names = ["김팬", "이팬", "박팬", "최팬", "정팬"]

        for i, name in enumerate(fan_names):
            user = await User.create(
                email=f"fan_dummy_{i + 1}@gmail.com",
                password=get_password_hash("fan123!"),
                nickname=name,
                user_type=UserType.FAN,
                is_email_verified=True,
            )
            fan_users.append(user)
        print(f"✅ 팬 사용자 {len(fan_users)}개 생성 완료")

        # 4. 아티스트 생성 (필수 필드만)
        print("🎤 아티스트 생성 중...")
        artists = []
        artist_data = [
            ("에스파", "aespa_dummy@sm.com", 0),
            ("블랙핑크", "bp_dummy@yg.com", 1),
            ("트와이스", "twice_dummy@jyp.com", 2),
            ("뉴진스", "nj_dummy@sm.com", 0),
            ("아이브", "ive_dummy@yg.com", 1),
        ]

        for name, email, company_idx in artist_data:
            artist = await Artist.create(
                company=companies[company_idx],
                group_name=name,
                email=email,
                artist_type=ArtistType.GROUP,
                role=ArtistRole.LEADER,
                debut_date=datetime.now().date() - timedelta(days=365),
                is_active=True,
            )
            artists.append(artist)
        print(f"✅ 아티스트 {len(artists)}개 생성 완료")

        # 5. 이벤트 생성
        print("📅 이벤트 생성 중...")
        events = []
        event_types = ["더미 팬미팅", "더미 콘서트", "더미 쇼케이스"]
        categories = [
            EventCategory.FANMEETING,
            EventCategory.CONCERT,
            EventCategory.SHOWCASE,
        ]

        for i in range(6):
            event_type = event_types[i % 3]
            artist = artists[i % len(artists)]

            artist_name = (
                artist.stage_name or artist.group_name or f"Artist {artist.id}"
            )
            event = await Events.create(
                title=f"{artist_name} {event_type}",
                description=f"{artist_name}의 특별한 {event_type} 이벤트",
                start_time=datetime.now() + timedelta(days=i * 10),
                end_time=datetime.now() + timedelta(days=i * 10, hours=3),
                location="서울 올림픽홀",
                artist=artist,
                category=categories[i % 3],
            )
            events.append(event)
        print(f"✅ 이벤트 {len(events)}개 생성 완료")

        # 6. 구독 관계 생성
        print("💝 구독 관계 생성 중...")
        subscriptions = []
        for fan in fan_users:
            for _i, artist in enumerate(artists[:3]):  # 각 팬이 3명 구독
                subscription = await Subscription.create(
                    user=fan, artist=artist, is_active=True
                )
                subscriptions.append(subscription)
        print(f"✅ 구독 관계 {len(subscriptions)}개 생성 완료")

        # 7. 이미지 생성
        print("🖼️ 이미지 생성 중...")
        images = []
        for i, artist in enumerate(artists):
            # 간단하게 첫 번째 회사 사용자를 업로더로 사용
            uploader = company_users[0]

            # Face 이미지
            artist_name = (
                artist.stage_name or artist.group_name or f"Artist {artist.id}"
            )
            face_img = await SharedImage.create(
                name=f"더미_{artist_name}_face.jpg",
                url=f"https://picsum.photos/400/400?random={i * 2}",
                image_type=ImageType.FACE,
                uploaded_by=uploader,
                artist=artist,
                is_public=True,
            )

            # Torso 이미지
            torso_img = await SharedImage.create(
                name=f"더미_{artist_name}_torso.jpg",
                url=f"https://picsum.photos/300/500?random={i * 2 + 1}",
                image_type=ImageType.TORSO,
                uploaded_by=uploader,
                artist=artist,
                is_public=True,
            )
            images.extend([face_img, torso_img])
        print(f"✅ 이미지 {len(images)}개 생성 완료")

        await Tortoise.close_connections()

        print("\n🎉 모든 더미 데이터 생성 완료!")
        print("\n📊 생성된 데이터:")
        print(f"- 회사: {len(companies)}개")
        print(f"- 회사 사용자: {len(company_users)}개")
        print(f"- 팬 사용자: {len(fan_users)}개")
        print(f"- 아티스트: {len(artists)}개")
        print(f"- 이벤트: {len(events)}개")
        print(f"- 구독: {len(subscriptions)}개")
        print(f"- 이미지: {len(images)}개")

        print("\n👥 테스트 계정:")
        print("📌 회사 계정:")
        for user in company_users:
            print(f"  - {user.email} / company123!")
        print("📌 팬 계정:")
        for user in fan_users:
            print(f"  - {user.email} / fan123!")

        print("\n🔗 테스트 URL:")
        print("- http://localhost:8000/api/idol (아티스트 목록)")
        print("- http://localhost:8000/docs (API 문서)")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        import traceback

        traceback.print_exc()
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(create_dummy_data())
