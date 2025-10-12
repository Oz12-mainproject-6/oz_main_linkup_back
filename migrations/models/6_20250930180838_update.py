from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "uid_artist_email_00eaba";
        ALTER TABLE "artist" DROP COLUMN "height";
        ALTER TABLE "artist" DROP COLUMN "mbti";
        ALTER TABLE "artist" DROP COLUMN "nickname";
        ALTER TABLE "artist" DROP COLUMN "role";
        ALTER TABLE "artist" DROP COLUMN "gender";
        ALTER TABLE "artist" DROP COLUMN "member_count";
        ALTER TABLE "artist" DROP COLUMN "email";
        DROP TABLE IF EXISTS "image_usage";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "artist" ADD "height" VARCHAR(255);
        ALTER TABLE "artist" ADD "mbti" VARCHAR(4);
        ALTER TABLE "artist" ADD "nickname" VARCHAR(200);
        ALTER TABLE "artist" ADD "role" VARCHAR(11);
        ALTER TABLE "artist" ADD "gender" VARCHAR(200);
        ALTER TABLE "artist" ADD "member_count" INT;
        ALTER TABLE "artist" ADD "email" VARCHAR(200) UNIQUE;
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_artist_email_00eaba" ON "artist" ("email");"""
