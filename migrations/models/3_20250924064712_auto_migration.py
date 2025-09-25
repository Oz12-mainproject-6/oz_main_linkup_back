from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ALTER COLUMN "user_type" TYPE VARCHAR(7) USING "user_type"::VARCHAR(7);
        ALTER TABLE "shared_image" DROP COLUMN "is_public";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "user" ALTER COLUMN "user_type" TYPE VARCHAR(9) USING "user_type"::VARCHAR(9);
        ALTER TABLE "shared_image" ADD "is_public" BOOL NOT NULL DEFAULT True;"""
