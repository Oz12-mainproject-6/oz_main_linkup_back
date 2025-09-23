from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "email_verification" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "email" VARCHAR(200) NOT NULL,
    "code" VARCHAR(6) NOT NULL,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "is_used" BOOL NOT NULL DEFAULT False
);
COMMENT ON COLUMN "email_verification"."created_at" IS '생성일시';
COMMENT ON COLUMN "email_verification"."updated_at" IS '수정일시';
COMMENT ON COLUMN "email_verification"."id" IS '인증 ID';
COMMENT ON COLUMN "email_verification"."email" IS '인증할 이메일';
COMMENT ON COLUMN "email_verification"."code" IS '인증 코드';
COMMENT ON COLUMN "email_verification"."expires_at" IS '만료 시간';
COMMENT ON COLUMN "email_verification"."is_used" IS '사용 여부';
COMMENT ON TABLE "email_verification" IS '이메일 인증 모델';
CREATE TABLE IF NOT EXISTS "user" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "email" VARCHAR(200) NOT NULL UNIQUE,
    "password" VARCHAR(200) NOT NULL,
    "phone_number" VARCHAR(20),
    "nickname" VARCHAR(50),
    "user_type" VARCHAR(9) NOT NULL DEFAULT 'fan',
    "push_notification_enabled" BOOL NOT NULL DEFAULT True,
    "in_app_notification_enabled" BOOL NOT NULL DEFAULT True,
    "oauth_provider" VARCHAR(50),
    "oauth_id" VARCHAR(200),
    "is_email_verified" BOOL NOT NULL DEFAULT False,
    "last_login_at" TIMESTAMPTZ,
    "deleted_at" TIMESTAMPTZ,
    CONSTRAINT "uid_user_oauth_p_a0c344" UNIQUE ("oauth_provider", "oauth_id")
);
COMMENT ON COLUMN "user"."created_at" IS '생성일시';
COMMENT ON COLUMN "user"."updated_at" IS '수정일시';
COMMENT ON COLUMN "user"."id" IS '사용자 ID';
COMMENT ON COLUMN "user"."email" IS '이메일';
COMMENT ON COLUMN "user"."password" IS '비밀번호';
COMMENT ON COLUMN "user"."phone_number" IS '전화번호';
COMMENT ON COLUMN "user"."nickname" IS '별명';
COMMENT ON COLUMN "user"."user_type" IS '사용자 타입';
COMMENT ON COLUMN "user"."push_notification_enabled" IS '푸시 알림 활성화';
COMMENT ON COLUMN "user"."in_app_notification_enabled" IS '앱 내 알림 활성화';
COMMENT ON COLUMN "user"."oauth_provider" IS '소셜 로그인 제공자';
COMMENT ON COLUMN "user"."oauth_id" IS '소셜 로그인 ID';
COMMENT ON COLUMN "user"."is_email_verified" IS '이메일 인증 여부';
COMMENT ON COLUMN "user"."last_login_at" IS '마지막 로그인 시간';
COMMENT ON COLUMN "user"."deleted_at" IS '삭제 시간';
COMMENT ON TABLE "user" IS '사용자 모델 (일반 유저 + 소속사 계정)';
CREATE TABLE IF NOT EXISTS "company" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(200) NOT NULL,
    "business_number" VARCHAR(50),
    "contact_email" VARCHAR(200),
    "contact_phone" VARCHAR(20),
    "address" TEXT,
    "description" TEXT,
    "user_id" BIGINT NOT NULL UNIQUE REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "company"."created_at" IS '생성일시';
COMMENT ON COLUMN "company"."updated_at" IS '수정일시';
COMMENT ON COLUMN "company"."id" IS '소속사 ID';
COMMENT ON COLUMN "company"."name" IS '소속사명';
COMMENT ON COLUMN "company"."business_number" IS '사업자등록번호';
COMMENT ON COLUMN "company"."contact_email" IS '담당자 이메일';
COMMENT ON COLUMN "company"."contact_phone" IS '담당자 전화번호';
COMMENT ON COLUMN "company"."address" IS '주소';
COMMENT ON COLUMN "company"."description" IS '소속사 소개';
COMMENT ON COLUMN "company"."user_id" IS '소속사 계정';
COMMENT ON TABLE "company" IS '소속사 모델';
CREATE TABLE IF NOT EXISTS "artist" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "stage_name" VARCHAR(200),
    "group_name" VARCHAR(200),
    "birthdate" DATE,
    "gender" VARCHAR(200),
    "role" VARCHAR(11),
    "mbti" VARCHAR(4),
    "height" VARCHAR(255),
    "nickname" VARCHAR(200),
    "email" VARCHAR(200) UNIQUE,
    "debut_date" DATE,
    "artist_type" VARCHAR(10) NOT NULL,
    "member_count" INT,
    "is_active" BOOL NOT NULL DEFAULT True,
    "company_id" BIGINT NOT NULL REFERENCES "company" ("id") ON DELETE CASCADE,
    "parent_group_id" BIGINT REFERENCES "artist" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "artist"."created_at" IS '생성일시';
COMMENT ON COLUMN "artist"."updated_at" IS '수정일시';
COMMENT ON COLUMN "artist"."id" IS '아티스트 ID';
COMMENT ON COLUMN "artist"."stage_name" IS '개인 예명 (개인 아티스트만)';
COMMENT ON COLUMN "artist"."group_name" IS '그룹명 (그룹만)';
COMMENT ON COLUMN "artist"."birthdate" IS '생년월일';
COMMENT ON COLUMN "artist"."gender" IS '성별';
COMMENT ON COLUMN "artist"."role" IS '역할';
COMMENT ON COLUMN "artist"."mbti" IS 'MBTI';
COMMENT ON COLUMN "artist"."height" IS '키';
COMMENT ON COLUMN "artist"."nickname" IS '별명';
COMMENT ON COLUMN "artist"."email" IS '이메일';
COMMENT ON COLUMN "artist"."debut_date" IS '데뷔일';
COMMENT ON COLUMN "artist"."artist_type" IS '아티스트 타입';
COMMENT ON COLUMN "artist"."member_count" IS '멤버 수 (그룹인 경우)';
COMMENT ON COLUMN "artist"."is_active" IS '활동 상태';
COMMENT ON COLUMN "artist"."company_id" IS '소속사';
COMMENT ON COLUMN "artist"."parent_group_id" IS '소속 그룹 (멤버인 경우만)';
COMMENT ON TABLE "artist" IS '아티스트 모델 (그룹/멤버/솔로 통합)';
CREATE TABLE IF NOT EXISTS "events" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "title" VARCHAR(200) NOT NULL,
    "description" TEXT,
    "start_time" TIMESTAMPTZ NOT NULL,
    "end_time" TIMESTAMPTZ,
    "location" VARCHAR(200),
    "category" VARCHAR(10) NOT NULL,
    "instant_notification_sent" BOOL NOT NULL DEFAULT False,
    "one_hour_notification_sent" BOOL NOT NULL DEFAULT False,
    "visibility" VARCHAR(16) NOT NULL DEFAULT 'public',
    "is_active" BOOL NOT NULL DEFAULT True,
    "artist_id" BIGINT NOT NULL REFERENCES "artist" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "events"."created_at" IS '생성일시';
COMMENT ON COLUMN "events"."updated_at" IS '수정일시';
COMMENT ON COLUMN "events"."id" IS '이벤트 ID';
COMMENT ON COLUMN "events"."title" IS '이벤트 제목';
COMMENT ON COLUMN "events"."description" IS '이벤트 설명';
COMMENT ON COLUMN "events"."start_time" IS '시작 시간';
COMMENT ON COLUMN "events"."end_time" IS '종료 시간';
COMMENT ON COLUMN "events"."location" IS '위치';
COMMENT ON COLUMN "events"."category" IS '이벤트 카테고리';
COMMENT ON COLUMN "events"."instant_notification_sent" IS '등록 즉시 알림 발송 여부';
COMMENT ON COLUMN "events"."one_hour_notification_sent" IS '1시간 전 알림 발송 여부';
COMMENT ON COLUMN "events"."visibility" IS '공개 설정';
COMMENT ON COLUMN "events"."is_active" IS '활성 상태';
COMMENT ON COLUMN "events"."artist_id" IS '아티스트';
COMMENT ON TABLE "events" IS '이벤트 모델';
CREATE TABLE IF NOT EXISTS "post" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "content" TEXT NOT NULL,
    "artist_id" BIGINT NOT NULL REFERENCES "artist" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "post"."created_at" IS '생성일시';
COMMENT ON COLUMN "post"."updated_at" IS '수정일시';
COMMENT ON COLUMN "post"."id" IS '포스트 ID';
COMMENT ON COLUMN "post"."content" IS '게시글 내용';
COMMENT ON COLUMN "post"."artist_id" IS '관련 아티스트';
COMMENT ON COLUMN "post"."user_id" IS '작성자';
COMMENT ON TABLE "post" IS '포스트 모델 (팬 포스트)';
CREATE TABLE IF NOT EXISTS "comment" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "content" VARCHAR(500) NOT NULL,
    "post_id" BIGINT NOT NULL REFERENCES "post" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "comment"."created_at" IS '생성일시';
COMMENT ON COLUMN "comment"."updated_at" IS '수정일시';
COMMENT ON COLUMN "comment"."id" IS '댓글 ID';
COMMENT ON COLUMN "comment"."content" IS '댓글 내용';
COMMENT ON COLUMN "comment"."post_id" IS '포스트';
COMMENT ON COLUMN "comment"."user_id" IS '작성자';
COMMENT ON TABLE "comment" IS '포스트 댓글';
CREATE TABLE IF NOT EXISTS "like" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "post_id" BIGINT NOT NULL REFERENCES "post" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_like_post_id_a3e5c1" UNIQUE ("post_id", "user_id")
);
COMMENT ON COLUMN "like"."created_at" IS '생성일시';
COMMENT ON COLUMN "like"."updated_at" IS '수정일시';
COMMENT ON COLUMN "like"."id" IS '좋아요 ID';
COMMENT ON COLUMN "like"."post_id" IS '포스트';
COMMENT ON COLUMN "like"."user_id" IS '사용자';
COMMENT ON TABLE "like" IS '포스트 좋아요';
CREATE TABLE IF NOT EXISTS "shared_image" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "url" TEXT NOT NULL,
    "name" VARCHAR(255),
    "size" BIGINT,
    "content_type" VARCHAR(100),
    "image_type" VARCHAR(5) NOT NULL,
    "is_public" BOOL NOT NULL DEFAULT True,
    "artist_id" BIGINT REFERENCES "artist" ("id") ON DELETE CASCADE,
    "event_id" BIGINT REFERENCES "events" ("id") ON DELETE CASCADE,
    "uploaded_by_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "shared_image"."created_at" IS '생성일시';
COMMENT ON COLUMN "shared_image"."updated_at" IS '수정일시';
COMMENT ON COLUMN "shared_image"."id" IS '이미지 ID';
COMMENT ON COLUMN "shared_image"."url" IS 'S3 이미지 URL';
COMMENT ON COLUMN "shared_image"."name" IS '원본 파일명';
COMMENT ON COLUMN "shared_image"."size" IS '파일 크기 (bytes)';
COMMENT ON COLUMN "shared_image"."content_type" IS 'MIME 타입';
COMMENT ON COLUMN "shared_image"."image_type" IS '이미지 타입';
COMMENT ON COLUMN "shared_image"."is_public" IS '구독자가 사용 가능한지';
COMMENT ON COLUMN "shared_image"."artist_id" IS '관련 아티스트';
COMMENT ON COLUMN "shared_image"."event_id" IS '관련 이벤트';
COMMENT ON COLUMN "shared_image"."uploaded_by_id" IS '업로드한 사용자 (소속사)';
COMMENT ON TABLE "shared_image" IS '공유 가능한 이미지 풀 (소속사가 업로드, 구독자가 사용)';
CREATE TABLE IF NOT EXISTS "image_usage" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "post_id" BIGINT REFERENCES "post" ("id") ON DELETE CASCADE,
    "shared_image_id" BIGINT NOT NULL REFERENCES "shared_image" ("id") ON DELETE CASCADE,
    "used_by_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "image_usage"."created_at" IS '생성일시';
COMMENT ON COLUMN "image_usage"."updated_at" IS '수정일시';
COMMENT ON COLUMN "image_usage"."id" IS '사용 기록 ID';
COMMENT ON COLUMN "image_usage"."post_id" IS '포스트';
COMMENT ON COLUMN "image_usage"."shared_image_id" IS '사용된 이미지';
COMMENT ON COLUMN "image_usage"."used_by_id" IS '사용한 사용자';
COMMENT ON TABLE "image_usage" IS '이미지 사용 기록 (팬 포스트에서 공유 이미지 사용)';
CREATE TABLE IF NOT EXISTS "notifications" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "type" VARCHAR(22) NOT NULL,
    "message" VARCHAR(200),
    "entity_type" VARCHAR(6),
    "entity_id" BIGINT,
    "read_at" TIMESTAMPTZ,
    "url" VARCHAR(255),
    "user_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "notifications"."created_at" IS '생성일시';
COMMENT ON COLUMN "notifications"."updated_at" IS '수정일시';
COMMENT ON COLUMN "notifications"."id" IS '알림 ID';
COMMENT ON COLUMN "notifications"."type" IS '알림 타입';
COMMENT ON COLUMN "notifications"."message" IS '알림 메시지';
COMMENT ON COLUMN "notifications"."entity_type" IS '관련 엔티티 타입';
COMMENT ON COLUMN "notifications"."entity_id" IS '관련 엔티티 ID';
COMMENT ON COLUMN "notifications"."read_at" IS '읽은 시간';
COMMENT ON COLUMN "notifications"."url" IS '알림 관련 URL';
COMMENT ON COLUMN "notifications"."user_id" IS '사용자';
COMMENT ON TABLE "notifications" IS '알림 모델';
CREATE TABLE IF NOT EXISTS "subscription" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "is_active" BOOL NOT NULL DEFAULT True,
    "artist_id" BIGINT NOT NULL REFERENCES "artist" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_subscriptio_user_id_937a2d" UNIQUE ("user_id", "artist_id")
);
COMMENT ON COLUMN "subscription"."created_at" IS '생성일시';
COMMENT ON COLUMN "subscription"."updated_at" IS '수정일시';
COMMENT ON COLUMN "subscription"."id" IS '구독 ID';
COMMENT ON COLUMN "subscription"."is_active" IS '구독 상태';
COMMENT ON COLUMN "subscription"."artist_id" IS '구독한 아티스트';
COMMENT ON COLUMN "subscription"."user_id" IS '팬 유저';
COMMENT ON TABLE "subscription" IS '팬 → 아티스트 구독';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
