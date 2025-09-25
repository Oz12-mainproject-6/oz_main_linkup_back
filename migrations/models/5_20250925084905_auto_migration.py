from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ADD "profile_image_url" VARCHAR(500);
        ALTER TABLE "user" ADD "original_user_type" VARCHAR(7);
        ALTER TABLE "user" DROP COLUMN "phone_number";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ADD "phone_number" VARCHAR(20);
        ALTER TABLE "user" DROP COLUMN "profile_image_url";
        ALTER TABLE "user" DROP COLUMN "original_user_type";"""
