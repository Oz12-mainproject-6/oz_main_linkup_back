import asyncio
from datetime import datetime, timedelta

from tortoise import Tortoise

from app.config import TORTOISE_ORM
from app.features.artists.models import Artist, ArtistType
from app.features.events.models import EventCategory, Events
from app.features.images.models import ImageType, SharedImage
from app.features.notifications.models import Subscription
from app.features.posts.models import Comment, Like, Post
from app.features.users.auth import get_password_hash
from app.features.users.models import Company, User, UserType


async def create_dummy_data():
    """완전한 더미 데이터 생성 스크립트"""
    try:
        print("🔗 데이터베이스 연결 중...")
        await Tortoise.init(config=TORTOISE_ORM)
        await Tortoise.generate_schemas()
        print("✅ 데이터베이스 연결 성공!")
        print("🎭 더미 데이터 생성 시작...")

        # 기존 더미 데이터 완전 삭제 (순서 중요)
        print("🧹 기존 데이터 정리...")
        await Like.all().delete()  # 좋아요 먼저 삭제
        await Comment.filter(content__contains="더미").delete()  # 댓글 삭제
        await Post.filter(content__contains="더미").delete()  # 포스트 삭제
        await SharedImage.filter(name__contains="더미").delete()
        await Subscription.all().delete()  # 간단하게 모든 구독 삭제
        await Events.filter(title__contains="더미").delete()
        await Artist.filter(email__contains="dummy").delete()
        await Company.filter(contact_email__contains="dummy").delete()
        await User.filter(email__contains="dummy").delete()
        print("✅ 기존 데이터 정리 완료")

        # 1. 관리자 생성
        print("👑 관리자 생성 중...")
        admin_user = await User.create(
            email="admin_dummy@admin.com",
            password=get_password_hash("admin123!"),
            nickname="관리자",
            user_type=UserType.ADMIN,
            is_email_verified=True,
        )
        print("✅ 관리자 1개 생성 완료")

        # 2. 회사 사용자 생성
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

        # 3. 회사 프로필 생성
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

        # 4. 팬 사용자 생성
        print("👥 팬 사용자 생성 중...")
        fan_users = []
        fan_names = [
            "김팬",
            "이팬",
            "박팬",
            "최팬",
            "정팬",
            "장팬",
            "윤팬",
            "임팬",
            "한팬",
            "오팬",
        ]

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

        # 5. 아티스트 생성 (그룹 + 멤버들)
        print("🎤 아티스트 생성 중...")
        artists = []

        # 5-1. 그룹 생성 (group_name만 있고 stage_name 없음)
        print("👥 그룹 생성 중...")
        group_data = [
            ("에스파", "aespa_dummy@sm.com", 0, 4),  # SM, 4명
            ("블랙핑크", "bp_dummy@yg.com", 1, 4),  # YG, 4명
            ("트와이스", "twice_dummy@jyp.com", 2, 9),  # JYP, 9명
            ("뉴진스", "nj_dummy@sm.com", 0, 5),  # SM, 5명
            ("아이브", "ive_dummy@yg.com", 1, 6),  # YG, 6명
        ]

        groups = []
        for group_name, email, company_idx, member_count in group_data:
            group = await Artist.create(
                company=companies[company_idx],
                group_name=group_name,
                email=email,
                artist_type=ArtistType.GROUP,
                member_count=member_count,
                debut_date=datetime.now().date() - timedelta(days=365 * 2),
                is_active=True,
            )
            groups.append(group)
            artists.append(group)
        print(f"✅ 그룹 {len(groups)}개 생성 완료")

        # 5-2. 그룹 멤버 생성 (group_name + stage_name 모두 있음)
        print("🌟 그룹 멤버 생성 중...")
        member_data = [
            # 에스파 멤버들
            ("카리나", "에스파", "karina_dummy@sm.com", 0),
            ("윈터", "에스파", "winter_dummy@sm.com", 0),
            ("지젤", "에스파", "giselle_dummy@sm.com", 0),
            ("닝닝", "에스파", "ningning_dummy@sm.com", 0),
            # 블랙핑크 멤버들
            ("제니", "블랙핑크", "jennie_dummy@yg.com", 1),
            ("리사", "블랙핑크", "lisa_dummy@yg.com", 1),
            ("로제", "블랙핑크", "rose_dummy@yg.com", 1),
            ("지수", "블랙핑크", "jisoo_dummy@yg.com", 1),
            # 트와이스 멤버들 (일부만)
            ("나연", "트와이스", "nayeon_dummy@jyp.com", 2),
            ("정연", "트와이스", "jeongyeon_dummy@jyp.com", 2),
            ("모모", "트와이스", "momo_dummy@jyp.com", 2),
            ("사나", "트와이스", "sana_dummy@jyp.com", 2),
            ("지효", "트와이스", "jihyo_dummy@jyp.com", 2),
            # 뉴진스 멤버들
            ("민지", "뉴진스", "minji_dummy@sm.com", 0),
            ("하니", "뉴진스", "hani_dummy@sm.com", 0),
            ("다니엘", "뉴진스", "danielle_dummy@sm.com", 0),
            ("해린", "뉴진스", "haerin_dummy@sm.com", 0),
            ("혜인", "뉴진스", "hyein_dummy@sm.com", 0),
            # 아이브 멤버들
            ("안유진", "아이브", "yujin_dummy@yg.com", 1),
            ("가을", "아이브", "gaeul_dummy@yg.com", 1),
            ("레이", "아이브", "rei_dummy@yg.com", 1),
            ("원영", "아이브", "wonyoung_dummy@yg.com", 1),
            ("리즈", "아이브", "liz_dummy@yg.com", 1),
            ("이서", "아이브", "leeseo_dummy@yg.com", 1),
        ]

        members = []
        for stage_name, group_name, email, company_idx in member_data:
            # parent_group 찾기 (같은 group_name을 가진 GROUP 타입)
            parent_group = next(g for g in groups if g.group_name == group_name)

            member = await Artist.create(
                company=companies[company_idx],
                stage_name=stage_name,
                group_name=group_name,  # 멤버도 group_name을 가짐
                email=email,
                artist_type=ArtistType.INDIVIDUAL,
                parent_group=parent_group,  # FK 관계 설정!
                debut_date=datetime.now().date() - timedelta(days=365 * 2),
                birthdate=datetime.now().date() - timedelta(days=365 * 20),  # 20살
                is_active=True,
            )
            members.append(member)
            artists.append(member)
        print(f"✅ 그룹 멤버 {len(members)}개 생성 완료")

        # 5-3. 솔로 아티스트 생성 (stage_name만 있음)
        print("🎭 솔로 아티스트 생성 중...")
        solo_data = [
            ("아이유", "iu_dummy@kakao.com", 0),
            ("태연", "taeyeon_dummy@sm.com", 0),
            ("청하", "chungha_dummy@yg.com", 1),
            ("선미", "sunmi_dummy@jyp.com", 2),
            ("화사", "hwasa_dummy@yg.com", 1),
        ]

        solos = []
        for stage_name, email, company_idx in solo_data:
            solo = await Artist.create(
                company=companies[company_idx],
                stage_name=stage_name,
                # group_name=None (솔로는 그룹명 없음)
                email=email,
                artist_type=ArtistType.INDIVIDUAL,
                # parent_group=None (솔로는 부모 그룹 없음)
                debut_date=datetime.now().date()
                - timedelta(days=365 * 5),  # 5년 전 데뷔
                birthdate=datetime.now().date() - timedelta(days=365 * 25),  # 25살
                is_active=True,
            )
            solos.append(solo)
            artists.append(solo)
        print(f"✅ 솔로 아티스트 {len(solos)}개 생성 완료")

        print(
            f"🎉 총 아티스트 {len(artists)}개 생성 완료 (그룹: {len(groups)}, 멤버: {len(members)}, 솔로: {len(solos)})"
        )

        # 6. 이벤트 생성
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

        # 7. 구독 관계 생성
        print("💝 구독 관계 생성 중...")
        subscriptions = []
        for fan in fan_users:
            for _i, artist in enumerate(artists[:3]):  # 각 팬이 3명 구독
                subscription = await Subscription.create(
                    user=fan, artist=artist, is_active=True
                )
                subscriptions.append(subscription)
        print(f"✅ 구독 관계 {len(subscriptions)}개 생성 완료")

        # 8. 이미지 생성
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
            )

            # Torso 이미지
            torso_img = await SharedImage.create(
                name=f"더미_{artist_name}_torso.jpg",
                url=f"https://picsum.photos/300/500?random={i * 2 + 1}",
                image_type=ImageType.TORSO,
                uploaded_by=uploader,
                artist=artist,
            )
            images.extend([face_img, torso_img])
        print(f"✅ 이미지 {len(images)}개 생성 완료")

        # 9. 포스트 생성
        print("📝 포스트 생성 중...")
        posts = []
        post_contents = [
            "더미 포스트 - 오늘 정말 좋은 하루였어요! 팬분들 사랑해요 💕",
            "더미 포스트 - 새로운 앨범 작업 중이에요! 기대해주세요 🎵",
            "더미 포스트 - 콘서트 연습하느라 힘들지만 재밌어요 ✨",
            "더미 포스트 - 팬분들이 보내주신 응원 메시지 잘 받았어요 ❤️",
            "더미 포스트 - 날씨가 좋아서 기분이 좋네요! 모두 좋은 하루 되세요 ☀️",
            "더미 포스트 - 드디어 새 곡 녹음 완료! 곧 들려드릴게요 🎤",
            "더미 포스트 - 멤버들과 맛있는 저녁 먹었어요! 행복한 시간 🍽️",
            "더미 포스트 - 무대 위에서 여러분과 함께할 수 있어서 감사해요 🙏",
        ]

        # 실제 생성된 아티스트들을 다시 조회
        db_artists = await Artist.filter(email__contains="dummy").all()
        print(f"DB에서 조회한 아티스트 수: {len(db_artists)}")

        for i, content in enumerate(post_contents):
            if not db_artists:
                print("❌ 생성된 아티스트가 없습니다. 포스트 생성을 건너뛰겠습니다.")
                break

            fan = fan_users[i % len(fan_users)]
            artist = db_artists[i % len(db_artists)]

            print(f"포스트 생성: fan_id={fan.id}, artist_id={artist.id}")

            post = await Post.create(user=fan, artist=artist, content=content)
            posts.append(post)
        print(f"✅ 포스트 {len(posts)}개 생성 완료")

        # 10. 댓글 생성
        print("💬 댓글 생성 중...")
        comments = []
        comment_texts = [
            "더미 댓글 - 정말 좋은 글이네요!",
            "더미 댓글 - 항상 응원하고 있어요 💪",
            "더미 댓글 - 멋진 포스트 감사해요!",
            "더미 댓글 - 다음 활동도 기대할게요",
            "더미 댓글 - 오늘도 수고하셨어요!",
            "더미 댓글 - 건강하게 활동해주세요 ❤️",
            "더미 댓글 - 최고예요! 사랑해요",
            "더미 댓글 - 언제나 응원할게요!",
        ]

        for post in posts:
            # 각 포스트당 2-3개의 댓글 생성
            num_comments = (hash(str(post.id)) % 3) + 1  # 1-3개 랜덤
            for j in range(num_comments):
                commenter = fan_users[j % len(fan_users)]
                comment_text = comment_texts[(post.id + j) % len(comment_texts)]

                comment = await Comment.create(
                    post=post, user=commenter, content=comment_text
                )
                comments.append(comment)
        print(f"✅ 댓글 {len(comments)}개 생성 완료")

        # 11. 좋아요 생성
        print("👍 좋아요 생성 중...")
        likes = []
        for post in posts:
            # 각 포스트당 1-4개의 좋아요 생성
            num_likes = (hash(str(post.id)) % 4) + 1  # 1-4개 랜덤
            liked_users = set()

            for j in range(num_likes):
                liker = fan_users[j % len(fan_users)]
                if liker.id not in liked_users:  # 중복 좋아요 방지
                    liked_users.add(liker.id)
                    like = await Like.create(post=post, user=liker)
                    likes.append(like)
        print(f"✅ 좋아요 {len(likes)}개 생성 완료")

        await Tortoise.close_connections()

        print("\n🎉 모든 더미 데이터 생성 완료!")
        print("\n📊 생성된 데이터:")
        print("- 관리자: 1개")
        print(f"- 회사: {len(companies)}개")
        print(f"- 회사 사용자: {len(company_users)}개")
        print(f"- 팬 사용자: {len(fan_users)}개")
        print(f"- 아티스트: {len(artists)}개")
        print(f"- 이벤트: {len(events)}개")
        print(f"- 구독: {len(subscriptions)}개")
        print(f"- 이미지: {len(images)}개")
        print(f"- 포스트: {len(posts)}개")
        print(f"- 댓글: {len(comments)}개")
        print(f"- 좋아요: {len(likes)}개")

        print("\n👥 테스트 계정:")
        print("📌 관리자 계정:")
        print(f"  - {admin_user.email} / admin123!")
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
