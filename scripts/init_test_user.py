#!/usr/bin/env python3
"""
Initialize test user in the database for development/testing
"""

import asyncio
import sys
from pathlib import Path
import logging
from sqlalchemy import select

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.database.connection import init_database, get_db_session
from src.database.models import User
from src.utils import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_test_user():
    """Create test user if it doesn't exist"""
    
    if not settings.enable_test_users:
        logger.warning("Test users are disabled in configuration. Set ENABLE_TEST_USERS=true to enable.")
        return False
    
    # Initialize database
    await init_database()
    
    # Use async generator properly with async with
    from src.database.connection import DatabaseManager
    db_manager = DatabaseManager()
    
    async with db_manager.get_session() as session:
        try:
            # Check if user already exists
            result = await session.execute(
                select(User).where(User.username == settings.test_username)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                logger.info(f"Test user '{settings.test_username}' already exists")
                return True
            
            # Create new test user
            hashed_password = get_password_hash(settings.test_password)
            
            test_user = User(
                username=settings.test_username,
                email=settings.test_email,
                password_hash=hashed_password,
                is_active=True,
                is_superuser=settings.test_is_admin
            )
            
            session.add(test_user)
            await session.commit()
            
            logger.info(f"✅ Test user created successfully:")
            logger.info(f"   Username: {settings.test_username}")
            logger.info(f"   Password: {settings.test_password}")
            logger.info(f"   Email: {settings.test_email}")
            logger.info(f"   Is Admin: {settings.test_is_admin}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating test user: {e}")
            await session.rollback()
            return False


async def main():
    """Main function"""
    logger.info("Initializing test user...")
    logger.info(f"Database URL: {settings.database_url}")
    
    try:
        success = await create_test_user()
        
        if success:
            logger.info("\n" + "="*50)
            logger.info("Test user is ready for use!")
            logger.info("You can now login with:")
            logger.info(f"  Username: {settings.test_username}")
            logger.info(f"  Password: {settings.test_password}")
            logger.info("="*50)
        else:
            logger.error("Failed to create test user")
            sys.exit(1)
    finally:
        # Ensure proper cleanup
        from src.database.connection import close_database
        await close_database()
        # Give a moment for async tasks to complete
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(main())