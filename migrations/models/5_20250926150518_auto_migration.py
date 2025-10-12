from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "subscription" ADD "subscription_type" VARCHAR(9) NOT NULL DEFAULT 'direct';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "subscription" DROP COLUMN "subscription_type";"""
