from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import event, MetaData

from ..config import settings
from ..utils import setup_logging

logger = setup_logging("Database.Connection")

# Create base class for models with naming conventions
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self._engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker] = None
        
        # Convert sqlite URL to async version if needed
        if self.database_url.startswith("sqlite://"):
            self.database_url = self.database_url.replace("sqlite://", "sqlite+aiosqlite://")
        # Convert postgresql URL to async version if needed
        elif self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    async def initialize(self):
        """Initialize the database engine and sessionmaker"""
        if self._engine is not None:
            return
        
        logger.info(f"Initializing database connection")
        
        # Create engine with appropriate settings
        engine_kwargs = {
            "echo": settings.debug,
            "future": True,
        }
        
        # Use NullPool for SQLite to avoid connection issues
        if "sqlite" in self.database_url:
            engine_kwargs["poolclass"] = NullPool
            # Add check_same_thread for SQLite
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            # Connection pool settings for PostgreSQL
            engine_kwargs.update({
                "pool_size": 20,
                "max_overflow": 10,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
            })
        
        self._engine = create_async_engine(self.database_url, **engine_kwargs)
        
        # Create sessionmaker
        self._sessionmaker = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Set up event listeners
        self._setup_event_listeners()
        
        logger.info("Database connection initialized successfully")
    
    def _setup_event_listeners(self):
        """Set up SQLAlchemy event listeners"""
        @event.listens_for(self._engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            # Enable foreign keys for SQLite
            if "sqlite" in self.database_url:
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
    
    async def create_tables(self):
        """Create all database tables"""
        if self._engine is None:
            await self.initialize()
        
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created")
    
    async def drop_tables(self):
        """Drop all database tables"""
        if self._engine is None:
            await self.initialize()
        
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("Database tables dropped")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session"""
        if self._sessionmaker is None:
            await self.initialize()
        
        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self):
        """Close the database connection"""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None
            logger.info("Database connection closed")
    
    async def test_connection(self) -> bool:
        """Test the database connection"""
        try:
            if self._engine is None:
                await self.initialize()
            
            from sqlalchemy import text
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session"""
    async with db_manager.get_session() as session:
        yield session


async def init_database():
    """Initialize database (for app startup)"""
    await db_manager.initialize()
    await db_manager.create_tables()


async def close_database():
    """Close database (for app shutdown)"""
    await db_manager.close()