#!/usr/bin/env python
"""
Example client for ingesting emails into the MCP server
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any


class EmailIngestClient:
    """Client for ingesting emails via MCP Server API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_prefix = "/api/v1"
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    async def create_project(self, session: aiohttp.ClientSession, project_data: Dict) -> Dict:
        """Create a new project"""
        url = f"{self.base_url}{self.api_prefix}/projects/"
        async with session.post(url, json=project_data, headers=self.headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def ingest_email(self, session: aiohttp.ClientSession, email_data: Dict) -> Dict:
        """Ingest a single email"""
        url = f"{self.base_url}{self.api_prefix}/emails/ingest"
        
        # Convert datetime to ISO format string
        if isinstance(email_data.get('datetime'), datetime):
            email_data['datetime'] = email_data['datetime'].isoformat()
        
        async with session.post(url, json=email_data, headers=self.headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def search_emails(self, session: aiohttp.ClientSession, params: Dict = None) -> List[Dict]:
        """Search for emails"""
        url = f"{self.base_url}{self.api_prefix}/emails/"
        async with session.get(url, params=params, headers=self.headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_person(self, session: aiohttp.ClientSession, email: str) -> Dict:
        """Get person by email"""
        url = f"{self.base_url}{self.api_prefix}/people/"
        params = {"email": email}
        async with session.get(url, params=params, headers=self.headers) as response:
            if response.status == 200:
                people = await response.json()
                return people[0] if people else None
            return None


async def main():
    """Example usage of the email ingest client"""
    
    # Initialize client
    client = EmailIngestClient()
    
    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: Create projects
            print("Creating projects...")
            
            acme_project = await client.create_project(session, {
                "name": "ACME Corporation",
                "description": "Main client project",
                "email_domains": ["acme.com", "acme.org"],
                "is_active": True,
                "auto_assign": True,
                "tags": ["client", "priority"]
            })
            print(f"Created project: {acme_project['name']}")
            
            internal_project = await client.create_project(session, {
                "name": "Internal Operations",
                "description": "Internal company project",
                "email_domains": ["ourcompany.com"],
                "is_active": True,
                "auto_assign": True,
                "tags": ["internal"]
            })
            print(f"Created project: {internal_project['name']}")
            
        except aiohttp.ClientResponseError as e:
            if e.status != 400:  # Ignore if projects already exist
                raise
            print("Projects already exist, continuing...")
        
        # Step 2: Ingest sample emails
        print("\nIngesting emails...")
        
        sample_emails = [
            {
                "email_id": "example001",
                "from": "alice@ourcompany.com",
                "to": ["bob@acme.com", "charlie@acme.com"],
                "cc": ["david@ourcompany.com"],
                "subject": "Q4 Project Planning",
                "body": "<html><body><p>Hi team,</p><p>Let's discuss our Q4 project goals.</p></body></html>",
                "body_text": "Hi team,\n\nLet's discuss our Q4 project goals.",
                "datetime": datetime.now() - timedelta(days=5),
                "headers": {
                    "X-Priority": "High",
                    "X-Mailer": "Outlook"
                }
            },
            {
                "email_id": "example002",
                "from": "bob@acme.com",
                "to": ["alice@ourcompany.com"],
                "cc": ["charlie@acme.com"],
                "subject": "RE: Q4 Project Planning",
                "body": "<html><body><p>Sounds great! I'll prepare the requirements doc.</p></body></html>",
                "body_text": "Sounds great! I'll prepare the requirements doc.",
                "datetime": datetime.now() - timedelta(days=4),
                "in_reply_to": "example001",
                "thread_id": "thread_q4_planning"
            },
            {
                "email_id": "example003",
                "from": "vendor@external.com",
                "to": ["alice@ourcompany.com", "david@ourcompany.com"],
                "subject": "Service Proposal",
                "body": "<html><body><p>Please find attached our service proposal.</p></body></html>",
                "body_text": "Please find attached our service proposal.",
                "datetime": datetime.now() - timedelta(days=2),
                "attachments": [
                    {
                        "filename": "proposal.pdf",
                        "size": 2048000,
                        "mime_type": "application/pdf"
                    }
                ]
            }
        ]
        
        for email in sample_emails:
            try:
                result = await client.ingest_email(session, email)
                print(f"Ingested: {email['subject']} (ID: {result['id']})")
            except Exception as e:
                print(f"Error ingesting email: {e}")
        
        # Step 3: Search for emails
        print("\nSearching for emails...")
        
        # Search by project
        print("\nEmails in ACME project:")
        acme_emails = await client.search_emails(session, {
            "project_id": acme_project.get('id'),
            "limit": 10
        })
        for email in acme_emails:
            print(f"  - {email['subject']} from {email['sender']['email']}")
        
        # Search by date range
        print("\nRecent emails (last 3 days):")
        recent_emails = await client.search_emails(session, {
            "date_from": (datetime.now() - timedelta(days=3)).isoformat(),
            "limit": 10
        })
        for email in recent_emails:
            print(f"  - {email['subject']} ({email['datetime_sent']})")
        
        # Step 4: Check people created
        print("\nPeople in the system:")
        for email_addr in ["alice@ourcompany.com", "bob@acme.com", "vendor@external.com"]:
            person = await client.get_person(session, email_addr)
            if person:
                print(f"  - {person['email']}: {person.get('full_name', 'N/A')}")
                if person.get('projects'):
                    print(f"    Projects: {', '.join(p['name'] for p in person['projects'])}")


if __name__ == "__main__":
    print("MCP Server Email Ingest Client Example")
    print("=" * 50)
    asyncio.run(main())