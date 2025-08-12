"""
Base utilities and dependencies for API routes
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.connection import DatabaseManager

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager():
    """Get database manager (can be overridden for testing)"""
    global _db_manager
    if _db_manager is None:
        from src.database.connection import db_manager
        _db_manager = db_manager
    return _db_manager


async def get_db() -> AsyncSession:
    """Get database session"""
    manager = get_db_manager()
    async with manager.get_session() as session:
        yield session