#!/usr/bin/env python
"""
Test email models and database connectivity
Usage: python scripts/test_email_models.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import db_manager
from src.database.email_repositories import (
    PersonRepository, ProjectRepository, EmailRepository
)
from src.database.email_models import Person, Project, Email
from src.config import settings


async def test_email_models():
    """Test email models and operations"""
    print("=" * 60)
    print("EMAIL MODELS TEST")
    print("=" * 60)
    
    try:
        # Initialize database
        print("\n1. Initializing database connection...")
        await db_manager.initialize()
        print("✅ Database connected")
        
        # Create tables
        print("\n2. Creating tables...")
        await db_manager.create_tables()
        print("✅ Tables created")
        
        # Test in a transaction
        async with db_manager.get_session() as session:
            print("\n3. Testing email models...")
            
            # Create repositories
            person_repo = PersonRepository(Person, session)
            project_repo = ProjectRepository(Project, session)
            email_repo = EmailRepository(Email, session)
            
            # Create a project
            print("\n   Creating test project...")
            project = await project_repo.create(
                name="Test Project",
                description="Testing email management",
                email_domains=["example.com", "test.org"],  # PostgreSQL ARRAY
                is_active=True,
                auto_assign=True
            )
            print(f"   ✅ Created project: {project.name}")
            print(f"      Email domains: {project.email_domains}")
            
            # Create people
            print("\n   Creating test people...")
            sender, created = await person_repo.get_or_create(
                email="sender@example.com",
                display_name="John Sender"
            )
            print(f"   ✅ {'Created' if created else 'Found'} sender: {sender.email}")
            
            recipient1, _ = await person_repo.get_or_create(
                email="recipient1@example.com",
                display_name="Jane Recipient"
            )
            recipient2, _ = await person_repo.get_or_create(
                email="recipient2@test.org",
                display_name="Bob Recipient"
            )
            print(f"   ✅ Created recipients")
            
            # Add people to project
            print("\n   Adding people to project...")
            await project_repo.add_person(project.id, sender.id, "member")
            await project_repo.add_person(project.id, recipient1.id, "member")
            print(f"   ✅ Added people to project")
            
            # Ingest an email
            print("\n   Ingesting test email...")
            email = await email_repo.ingest_email(
                email_id=f"test-email-{uuid4().hex[:8]}",
                from_email="sender@example.com",
                to_emails=["recipient1@example.com"],
                cc_emails=["recipient2@test.org"],
                subject="Test Email Subject",
                body="<html><body>This is a test email body</body></html>",
                body_text="This is a test email body",
                datetime_sent=datetime.now(timezone.utc),
                message_id=f"<{uuid4().hex}@example.com>",
                headers={"X-Test": "true"},  # PostgreSQL JSONB
                attachments=[{"name": "test.pdf", "size": 1024}]  # PostgreSQL JSONB
            )
            print(f"   ✅ Ingested email: {email.subject}")
            print(f"      From: {email.sender.email}")
            print(f"      Project: {email.project.name if email.project else 'None'}")
            
            # Search emails
            print("\n   Searching emails...")
            results = await email_repo.search_emails(
                query="test",
                project_id=project.id
            )
            print(f"   ✅ Found {len(results)} emails")
            
            # Test project domain matching
            print("\n   Testing domain matching...")
            test_project = await project_repo.find_project_for_email(
                from_email="user@example.com",
                to_emails=["another@test.org"]
            )
            print(f"   ✅ Matched project: {test_project.name if test_project else 'None'}")
            
            # Commit the transaction
            await session.commit()
            print("\n✅ All tests passed! Transaction committed.")
            
            # Display statistics
            print("\n4. Database statistics:")
            person_count = await person_repo.count()
            project_count = await project_repo.count()
            email_count = await email_repo.count()
            
            print(f"   People: {person_count}")
            print(f"   Projects: {project_count}")
            print(f"   Emails: {email_count}")
        
        print("\n" + "=" * 60)
        print("EMAIL MODELS TEST SUCCESSFUL!")
        print("=" * 60)
        print("\nYour PostgreSQL database is properly configured and working.")
        print("The email management models are ready for use.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(test_email_models())