from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE INDEX IF NOT EXISTS "idx_shared_imag_artist__54b631" ON "shared_image" ("artist_id", "image_type");
        CREATE INDEX IF NOT EXISTS "idx_shared_imag_image_t_a130ec" ON "shared_image" ("image_type");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_shared_imag_image_t_a130ec";
        DROP INDEX IF EXISTS "idx_shared_imag_artist__54b631";"""
