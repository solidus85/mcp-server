#!/usr/bin/env python
"""
Comprehensive test script for email ingestion pipeline
Tests all aspects of the email management system
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import db_manager
from src.database.email_repositories import EmailRepository, PersonRepository, ProjectRepository
from src.database.email_models import Person, Project, Email, EmailRecipient, RecipientType
from src.config import settings


async def test_email_pipeline():
    """Test complete email ingestion pipeline"""
    print("=" * 80)
    print("EMAIL INGESTION PIPELINE TEST")
    print("=" * 80)
    
    async with db_manager.get_session() as session:
        email_repo = EmailRepository(session)
        person_repo = PersonRepository(session)
        project_repo = ProjectRepository(session)
        
        try:
            # Step 1: Create test projects
            print("\n1. Creating test projects...")
            
            # Create main project
            main_project_data = {
                "name": "Main Company Project",
                "description": "Primary project for main company",
                "email_domains": ["company.com", "company.org"],
                "is_active": True,
                "auto_assign": True,
                "tags": ["main", "production"]
            }
            main_project = await project_repo.create(**main_project_data)
            print(f"   ✅ Created project: {main_project.name}")
            
            # Create client project
            client_project_data = {
                "name": "Client Project Alpha",
                "description": "Project for client Alpha",
                "email_domains": ["client-alpha.com"],
                "is_active": True,
                "auto_assign": True,
                "tags": ["client", "alpha"]
            }
            client_project = await project_repo.create(**client_project_data)
            print(f"   ✅ Created project: {client_project.name}")
            
            # Step 2: Test email ingestion with automatic person creation
            print("\n2. Testing email ingestion with auto person/project assignment...")
            
            test_emails = [
                {
                    "email_id": "msg001",
                    "message_id": "<msg001@company.com>",
                    "from": "john.doe@company.com",
                    "to": ["jane.smith@company.com", "bob.wilson@client-alpha.com"],
                    "cc": ["mary.jones@company.org"],
                    "subject": "Project Alpha - Kickoff Meeting",
                    "body": "<html><body><p>Hello team,</p><p>Let's schedule our kickoff meeting.</p></body></html>",
                    "body_text": "Hello team,\n\nLet's schedule our kickoff meeting.",
                    "datetime_sent": datetime.now() - timedelta(days=2),
                    "headers": {"X-Priority": "High"},
                    "size_bytes": 1024
                },
                {
                    "email_id": "msg002",
                    "message_id": "<msg002@client-alpha.com>",
                    "from": "bob.wilson@client-alpha.com",
                    "to": ["john.doe@company.com"],
                    "cc": ["jane.smith@company.com"],
                    "subject": "RE: Project Alpha - Kickoff Meeting",
                    "body": "<html><body><p>Sounds good!</p></body></html>",
                    "body_text": "Sounds good!",
                    "datetime_sent": datetime.now() - timedelta(days=1),
                    "in_reply_to": "<msg001@company.com>",
                    "thread_id": "thread001",
                    "size_bytes": 512
                },
                {
                    "email_id": "msg003",
                    "message_id": "<msg003@external.com>",
                    "from": "external.user@external.com",
                    "to": ["john.doe@company.com", "jane.smith@company.com"],
                    "subject": "External Inquiry",
                    "body": "<html><body><p>I have a question about your services.</p></body></html>",
                    "body_text": "I have a question about your services.",
                    "datetime_sent": datetime.now(),
                    "size_bytes": 768
                }
            ]
            
            ingested_emails = []
            for email_data in test_emails:
                # Extract required parameters
                email = await email_repo.ingest_email(
                    email_id=email_data["email_id"],
                    from_email=email_data["from"],
                    to_emails=email_data["to"],
                    subject=email_data["subject"],
                    body=email_data["body"],
                    body_text=email_data["body_text"],
                    datetime_sent=email_data["datetime_sent"],
                    cc_emails=email_data.get("cc", []),
                    message_id=email_data.get("message_id"),
                    in_reply_to=email_data.get("in_reply_to"),
                    thread_id=email_data.get("thread_id"),
                    headers=email_data.get("headers"),
                    attachments=email_data.get("attachments"),
                    size_bytes=email_data.get("size_bytes")
                )
                ingested_emails.append(email)
                print(f"   ✅ Ingested email: {email.subject[:50]}...")
                print(f"      - From: {email.sender.email}")
                print(f"      - Project: {email.project.name if email.project else 'None (external)'}")
                print(f"      - Recipients: {len(email.recipients)}")
            
            # Commit the ingested emails
            await session.commit()
            
            # Step 3: Verify person creation and project assignment
            print("\n3. Verifying person creation and project assignments...")
            
            # Check people were created
            all_people = await person_repo.get_all()
            print(f"   Total people created: {len(all_people)}")
            
            for person in all_people:
                print(f"   - {person.email}: {person.full_name}")
                print(f"     Projects: {[p.name for p in person.projects]}")
                print(f"     External: {person.is_external}")
            
            # Step 4: Test search functionality
            print("\n4. Testing search functionality...")
            
            # Search emails by project
            main_project_emails = await email_repo.search_emails(
                project_id=main_project.id
            )
            print(f"   Emails in Main Company Project: {len(main_project_emails)}")
            
            # Search emails by sender
            john = await person_repo.get_by_email("john.doe@company.com")
            if john:
                john_emails = await email_repo.search_emails(
                    person_id=john.id
                )
                print(f"   Emails from/to john.doe@company.com: {len(john_emails)}")
            
            # Search emails by date range
            recent_emails = await email_repo.search_emails(
                date_from=datetime.now() - timedelta(days=1)
            )
            print(f"   Emails from last 24 hours: {len(recent_emails)}")
            
            # Step 5: Test thread functionality
            print("\n5. Testing email threads...")
            
            thread_emails = await email_repo.get_thread_emails("thread001")
            print(f"   Emails in thread 'thread001': {len(thread_emails)}")
            
            # Step 6: Test statistics
            print("\n6. Testing statistics...")
            
            # Count emails
            from sqlalchemy import func, select
            email_count_stmt = select(func.count(Email.id))
            result = await session.execute(email_count_stmt)
            total_emails = result.scalar()
            
            print(f"   Total emails: {total_emails}")
            
            # Count unread emails
            unread_stmt = select(func.count(Email.id)).where(Email.is_read == False)
            result = await session.execute(unread_stmt)
            unread_count = result.scalar()
            print(f"   Unread emails: {unread_count}")
            
            # Count by project
            print(f"   Emails by project:")
            project_count_stmt = select(
                Email.project_id,
                func.count(Email.id).label('count')
            ).group_by(Email.project_id)
            result = await session.execute(project_count_stmt)
            for row in result:
                if row.project_id:
                    project = await project_repo.get(row.project_id)
                    if project:
                        print(f"     - {project.name}: {row.count}")
                else:
                    print(f"     - No project: {row.count}")
            
            # Project statistics
            project_count_stmt = select(func.count(Project.id))
            result = await session.execute(project_count_stmt)
            total_projects = result.scalar()
            
            active_projects_stmt = select(func.count(Project.id)).where(Project.is_active == True)
            result = await session.execute(active_projects_stmt)
            active_projects = result.scalar()
            
            print(f"   Total projects: {total_projects}")
            print(f"   Active projects: {active_projects}")
            
            # Step 7: Test update operations
            print("\n7. Testing update operations...")
            
            # Mark first email as read and flagged
            first_email = ingested_emails[0]
            updated_email = await email_repo.update(
                first_email.id, 
                is_read=True,
                is_flagged=True
            )
            print(f"   ✅ Updated email status - Read: {updated_email.is_read}, Flagged: {updated_email.is_flagged}")
            
            # Update person information
            john = await person_repo.get_by_email("john.doe@company.com")
            if john:
                updated_john = await person_repo.update(
                    john.id,
                    first_name="John",
                    last_name="Doe",
                    organization="Main Company",
                    phone="+1-555-0100"
                )
                print(f"   ✅ Updated person: {updated_john.full_name} - {updated_john.organization}")
            
            # Step 8: Test bulk operations
            print("\n8. Testing bulk person-project assignment...")
            
            # Get external person
            external_person = await person_repo.get_by_email("external.user@external.com")
            if external_person:
                # Assign to main project
                success = await person_repo.add_to_project(
                    external_person.id, 
                    main_project.id,
                    role="guest"
                )
                if success:
                    print(f"   ✅ Added external user to Main Company Project as guest")
            
            # Commit all changes
            await session.commit()
            
            # Step 9: Final verification
            print("\n9. Final verification...")
            
            # Re-fetch and verify data
            final_email_count_stmt = select(func.count(Email.id))
            result = await session.execute(final_email_count_stmt)
            final_email_count = result.scalar()
            
            final_person_count_stmt = select(func.count(Person.id))
            result = await session.execute(final_person_count_stmt)
            final_person_count = result.scalar()
            
            final_project_count_stmt = select(func.count(Project.id))
            result = await session.execute(final_project_count_stmt)
            final_project_count = result.scalar()
            
            print(f"   Final counts:")
            print(f"     - Emails: {final_email_count}")
            print(f"     - People: {final_person_count}")
            print(f"     - Projects: {final_project_count}")
            
            # Verify PostgreSQL-specific features
            print("\n10. Testing PostgreSQL-specific features...")
            
            # Test ARRAY column (email_domains)
            company_project = await project_repo.get_by_name("Main Company Project")
            if company_project:
                print(f"   Email domains (ARRAY): {company_project.email_domains}")
                print(f"   Has domain 'company.com': {company_project.has_domain('test@company.com')}")
                print(f"   Has domain 'other.com': {company_project.has_domain('test@other.com')}")
            
            # Test JSONB columns
            first_email_refetch = await email_repo.get(first_email.id)
            if first_email_refetch:
                print(f"   Headers (JSONB): {json.dumps(first_email_refetch.headers, indent=2)}")
                print(f"   Attachments (JSONB): {first_email_refetch.attachments}")
            
            print("\n" + "=" * 80)
            print("✅ EMAIL PIPELINE TEST COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            return False
        
    return True


async def cleanup_test_data():
    """Clean up test data from previous runs"""
    print("\nCleaning up previous test data...")
    
    async with db_manager.get_session() as session:
        try:
            # Delete test emails
            from sqlalchemy import delete
            
            # Delete emails with test email_ids
            await session.execute(
                delete(Email).where(Email.email_id.in_(["msg001", "msg002", "msg003"]))
            )
            
            # Delete test projects
            await session.execute(
                delete(Project).where(Project.name.in_([
                    "Main Company Project", 
                    "Client Project Alpha"
                ]))
            )
            
            await session.commit()
            print("   ✅ Previous test data cleaned up")
            
        except Exception as e:
            print(f"   ⚠️  Cleanup warning: {e}")
            await session.rollback()


async def main():
    """Main test runner"""
    try:
        # Initialize database connection
        print("Initializing database connection...")
        connected = await db_manager.test_connection()
        if not connected:
            print("❌ Failed to connect to database")
            return
        
        # Clean up previous test data
        await cleanup_test_data()
        
        # Run the test
        success = await test_email_pipeline()
        
        if success:
            print("\n🎉 All tests passed successfully!")
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
            
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())