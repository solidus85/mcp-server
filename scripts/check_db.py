#!/usr/bin/env python
"""
Database connectivity checker
Usage: python scripts/check_db.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import db_manager
from src.config import settings


async def check_database():
    """Check database connectivity and configuration"""
    print("=" * 60)
    print("DATABASE CONNECTIVITY CHECK")
    print("=" * 60)
    
    # Display configuration (hiding password)
    db_url = settings.database_url
    if "@" in db_url:
        # Hide password in display
        parts = db_url.split("@")
        user_pass = parts[0].split("://")[1]
        if ":" in user_pass:
            user = user_pass.split(":")[0]
            masked_url = db_url.replace(user_pass, f"{user}:****")
        else:
            masked_url = db_url
    else:
        masked_url = db_url
    
    print(f"\nConfiguration:")
    print(f"  Database URL: {masked_url}")
    print(f"  Debug Mode: {settings.debug}")
    
    # Test connection
    print(f"\nTesting connection...")
    try:
        connected = await db_manager.test_connection()
        if connected:
            print("✅ Successfully connected to database!")
            
            # Try to create tables
            print("\nCreating tables (if not exist)...")
            await db_manager.create_tables()
            print("✅ Tables ready!")
            
            # Get session and check
            async with db_manager.get_session() as session:
                # Try a simple query
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1"))
                print("✅ Query execution successful!")
            
            print("\n" + "=" * 60)
            print("DATABASE IS READY FOR USE!")
            print("=" * 60)
            
        else:
            print("❌ Failed to connect to database")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Database Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your .env file has correct DATABASE_URL")
        print("2. Ensure PostgreSQL is running: sudo service postgresql status")
        print("3. Verify database exists: sudo -u postgres psql -l")
        print("4. Check credentials are correct")
        sys.exit(1)
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(check_database())