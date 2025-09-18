import asyncio
from tortoise import Tortoise
from app.config import TORTOISE_ORM
from app.features.users.models import User, UserType, Company
from app.features.artists.models import Artist, ArtistRole
from app.features.events.models import Events, EventCategory
from app.features.subscriptions.models import Subscription
from app.features.images.models import SharedImage, ImageType
from datetime import datetime, timedelta

async def create_dummy_data():
    await Tortoise.init(config=TORTOISE_ORM)
    print("🎭 더미 데이터 생성 시작...")
    
    # 기존 데이터 확인
    existing_users = await User.filter(email__startswith="manager").count()
    if existing_users > 0:
        print(f"⚠️ 기존 더미 데이터 {existing_users}개 발견됨. 삭제 후 진행...")
        await User.filter(email__contains="@company.com").delete()
        await User.filter(email__contains="fan").delete()
        await Company.all().delete()
        await Artist.all().delete()
        await Events.all().delete()
        await Subscription.all().delete()
        await SharedImage.all().delete()
        print("✅ 기존 데이터 삭제 완료")
    
    # 1. 회사 사용자 먼저 생성
    company_users = []
    company_names = ["SM엔터테인먼트", "YG엔터테인먼트", "JYP엔터테인먼트"]
    
    for i, name in enumerate(company_names):
        company_user = await User.create(
            email=f"manager{i+1}@company.com",
            password="company123!",
            nickname=f"{name} 매니저",
            user_type=UserType.COMPANY,
            is_email_verified=True
        )
        company_users.append(company_user)
    print("✅ 회사 사용자 3개 생성 완료")
    
    # 2. 회사 프로필 생성
    companies = []
    for i, (name, user) in enumerate(zip(company_names, company_users)):
        company = await Company.create(
            user=user,
            name=name,
            contact_email=f"contact@{name.lower().replace('엔터테인먼트', '')}.com",
            contact_phone=f"02-123-456{i+1}",
            address=f"서울시 강남구 {name} 빌딩"
        )
        companies.append(company)
    print("✅ 회사 프로필 3개 생성 완료")
    
    # 3. 팬 사용자 생성
    fan_users = []
    fan_names = ["김팬", "이팬", "박팬", "최팬", "정팬", "강팬", "조팬", "윤팬", "장팬", "임팬"]
    for i, name in enumerate(fan_names):
        fan_user = await User.create(
            email=f"fan{i+1}@gmail.com",
            password="fan123!",
            nickname=name,
            user_type=UserType.FAN,
            is_email_verified=True
        )
        fan_users.append(fan_user)
    print("✅ 팬 사용자 10개 생성 완료")
    
    # 4. 아티스트 생성
    artists = []
    artist_data = [
        ("에스파", "aespa", 0),
        ("블랙핑크", "BLACKPINK", 1),
        ("트와이스", "TWICE", 2),
        ("뉴진스", "NewJeans", 0),
        ("아이브", "IVE", 1),
        ("르세라핌", "LE SSERAFIM", 0),
        ("스테이씨", "STAYC", 2),
        ("아이들", "(G)I-DLE", 1),
        ("에버글로우", "EVERGLOW", 0),
        ("우주소녀", "WJSN", 2)
    ]
    
    for i, (name_ko, name_en, company_idx) in enumerate(artist_data):
        artist = await Artist.create(
            company=companies[company_idx],
            real_name=name_ko,
            stage_name=name_ko,
            role=ArtistRole.LEADER
        )
        artists.append(artist)
    print(f"✅ 아티스트 {len(artists)}개 생성 완료")
    
    # 5. 이벤트 생성
    event_templates = [
        ("팬미팅", "팬들과의 특별한 만남의 시간"),
        ("콘서트", "음악으로 하나되는 시간"),
        ("앨범 발매 기념", "새로운 음악과의 만남"),
        ("생일 축하", "특별한 날을 함께 축하해요"),
        ("컴백 쇼케이스", "새로운 모습으로 돌아왔습니다")
    ]
    
    categories = list(EventCategory)
    for i in range(20):
        template = event_templates[i % len(event_templates)]
        artist = artists[i % len(artists)]
        
        await Events.create(
            title=f"{artist.name} {template[0]}",
            description=f"{artist.name}의 {template[1]}",
            start_date=datetime.now() + timedelta(days=i*7),
            end_date=datetime.now() + timedelta(days=i*7+2),
            location=f"서울 올림픽공원 체조경기장",
            max_participants=1000 + i*100,
            artist_id=artist.id,
            company_id=artist.company_id,
            category=categories[i % len(categories)]
        )
    print("✅ 이벤트 20개 생성 완료")
    
    # 6. 구독 생성
    fans = await User.filter(user_type=UserType.FAN).all()
    for fan in fans:
        # 각 팬이 3-7명의 아티스트를 구독
        num_subscriptions = 3 + (fan.id % 5)
        for i in range(min(num_subscriptions, len(artists))):
            await Subscription.create(
                user_id=fan.id,
                artist_id=artists[i].id,
                is_active=True
            )
    print("✅ 구독 관계 생성 완료")
    
    # 7. 이미지 생성
    for i, artist in enumerate(artists):
        # 얼굴 이미지
        await SharedImage.create(
            name=f"{artist.name}_profile.jpg",
            url=f"https://picsum.photos/400/400?random={i*2}",
            image_type=ImageType.FACE,
            artist_id=artist.id,
            is_public=True
        )
        
        # 전신 이미지
        await SharedImage.create(
            name=f"{artist.name}_full.jpg",
            url=f"https://picsum.photos/300/500?random={i*2+1}",
            image_type=ImageType.TORSO,
            artist_id=artist.id,
            is_public=True
        )
    print("✅ 아티스트 이미지 생성 완료")
    
    await Tortoise.close_connections()
    print("🎉 모든 더미 데이터 생성 완료!")
    print("\n📊 생성된 데이터:")
    print(f"- 회사: {len(companies)}개")
    print(f"- 회사 사용자: {len(company_users)}개")
    print(f"- 팬 사용자: {len(fan_users)}개")
    print(f"- 아티스트: {len(artists)}개")
    print(f"- 이벤트: 20개")
    print(f"- 이미지: {len(artists)*2}개")
    
    print("\n👥 테스트 계정:")
    print("📌 회사 계정:")
    for user in company_users:
        print(f"  - {user.email} / company123!")
    print("📌 팬 계정:")
    for i, user in enumerate(fan_users[:3]):  # 처음 3명만 표시
        print(f"  - {user.email} / fan123!")
    print("  - ... 더 많은 팬 계정 있음")
    print("\n🔗 테스트 URL:")
    print("- http://localhost:8000/api/idol (아티스트 목록)")
    print("- http://localhost:8000/docs (API 문서)")

if __name__ == "__main__":
    asyncio.run(create_dummy_data())