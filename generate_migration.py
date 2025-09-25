#!/usr/bin/env python3
"""
Migration generator script for phone_number field removal
Run this script to create a migration for the recent model changes
"""

import asyncio
import os
from tortoise import Tortoise
from app.config import TORTOISE_ORM

async def generate_migration():
    """Generate migration for model changes"""
    try:
        print("🔧 Initializing Tortoise ORM...")
        await Tortoise.init(config=TORTOISE_ORM)
        
        print("📝 Generating migration for recent changes...")
        # This will detect the phone_number field removal and profile_image_url addition
        os.system("uv run aerich migrate --name 'remove_phone_number_add_profile_image_url'")
        
        print("✅ Migration generated successfully!")
        print("💡 Run 'aerich upgrade' to apply the migration")
        
    except Exception as e:
        print(f"❌ Error generating migration: {e}")
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(generate_migration())