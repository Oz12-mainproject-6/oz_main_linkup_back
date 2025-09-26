from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
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
        ALTER TABLE "subscription" DROP COLUMN "is_active";
        COMMENT ON COLUMN "subscription"."user_id" IS '구독자';
        COMMENT ON COLUMN "subscription"."artist_id" IS '아티스트';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "subscription" ADD "is_active" BOOL NOT NULL DEFAULT True;
        COMMENT ON COLUMN "subscription"."user_id" IS '팬 유저';
        COMMENT ON COLUMN "subscription"."artist_id" IS '구독한 아티스트';
        DROP TABLE IF EXISTS "notifications";"""
