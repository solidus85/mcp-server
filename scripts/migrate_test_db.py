#!/usr/bin/env python3
"""
Script to setup and migrate the test database.
This ensures the test database schema is up-to-date before running tests.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load test environment
test_env_path = project_root / "tests" / ".env.test"
load_dotenv(test_env_path)


def run_alembic_migrations():
    """Run Alembic migrations on the test database."""
    print("Running Alembic migrations on test database...")
    
    # Set the DATABASE_URL environment variable to the test database
    env = os.environ.copy()
    env["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL")
    
    # Run alembic upgrade head
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error running migrations: {result.stderr}")
        return False
    
    print("Migrations completed successfully!")
    return True


async def setup_test_database():
    """Setup the test database schema using SQLAlchemy."""
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool
    
    # Import all models to ensure they're registered
    from src.database.connection import Base
    from src.database import models  # Import to register models
    from src.database import email_models  # Import to register email models
    
    test_database_url = os.getenv("TEST_DATABASE_URL")
    if not test_database_url:
        print("Error: TEST_DATABASE_URL not found in environment")
        return False
    
    print(f"Setting up test database: {test_database_url}")
    
    engine = create_async_engine(
        test_database_url,
        echo=False,
        poolclass=NullPool,
        pool_pre_ping=True,
    )
    
    try:
        async with engine.begin() as conn:
            # Drop all tables first
            print("Dropping existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
            
            # Create all tables
            print("Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
            
        print("Database schema created successfully!")
        return True
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False
        
    finally:
        await engine.dispose()


def main():
    """Main function to setup test database."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup and migrate test database")
    parser.add_argument(
        "--use-alembic",
        action="store_true",
        help="Use Alembic migrations instead of SQLAlchemy create_all"
    )
    parser.add_argument(
        "--no-drop",
        action="store_true",
        help="Don't drop existing tables (only works with --use-alembic)"
    )
    
    args = parser.parse_args()
    
    if args.use_alembic:
        # Use Alembic for migrations
        if not args.no_drop:
            # First setup clean database
            asyncio.run(setup_test_database())
        
        # Then run migrations
        success = run_alembic_migrations()
    else:
        # Use SQLAlchemy to create schema directly
        success = asyncio.run(setup_test_database())
    
    if success:
        print("\nTest database is ready!")
        print(f"Database URL: {os.getenv('TEST_DATABASE_URL')}")
    else:
        print("\nFailed to setup test database")
        sys.exit(1)


if __name__ == "__main__":
    main()