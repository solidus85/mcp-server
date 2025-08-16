#!/usr/bin/env python3
"""
Generate and Ingest Mock Emails into MCP Server
Uses LM Studio to generate realistic email chains and ingests them into the database
"""

import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
import random
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_mock_emails import EmailGenerator, EmailScenario


class EmailIngester:
    """Ingest generated emails into MCP Server"""
    
    def __init__(self, api_url: str = "http://localhost:8000", 
                 auth_token: str = "my-personal-api-token-12345"):
        self.api_url = api_url
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    async def ingest_email(self, email_data: dict) -> bool:
        """Ingest a single email into the system"""
        # Transform to match the ingestion API format
        payload = {
            "to": email_data.get("to", []) if isinstance(email_data.get("to"), list) else [email_data.get("to")],
            "from": email_data.get("from"),
            "subject": email_data.get("subject", "No Subject"),
            "datetime": email_data.get("datetime", datetime.now().isoformat()),
            "body": f"<html><body><p>{email_data.get('body', '')}</p></body></html>",
            "body_text": email_data.get("body", ""),
            "cc": email_data.get("cc", []),
            "email_id": email_data.get("email_id"),
            "message_id": email_data.get("message_id"),
            "in_reply_to": email_data.get("in_reply_to"),
            "thread_id": email_data.get("thread_id"),
            "headers": email_data.get("headers", {}),
            "attachments": email_data.get("attachments", []),
            "size_bytes": len(email_data.get("body", ""))
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.api_url}/api/v1/emails/ingest",
                    json=payload,
                    headers=self.headers
                ) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        print(f"✓ Ingested: {email_data.get('subject', 'No subject')[:50]}")
                        return True
                    else:
                        error = await response.text()
                        print(f"✗ Failed: {email_data.get('subject', 'No subject')[:50]} - {error}")
                        return False
            except Exception as e:
                print(f"✗ Error ingesting email: {e}")
                return False
    
    async def ingest_email_chain(self, emails: list) -> int:
        """Ingest a chain of emails"""
        success_count = 0
        for email in emails:
            if await self.ingest_email(email):
                success_count += 1
            await asyncio.sleep(0.1)  # Small delay between requests
        return success_count


class AdvancedEmailGenerator(EmailGenerator):
    """Extended email generator with more sophisticated scenarios"""
    
    async def generate_complex_scenario(self, scenario_type: str = "multi_company_project") -> list:
        """Generate complex multi-party email scenarios"""
        
        if scenario_type == "multi_company_project":
            prompt = """
Generate a realistic email chain for a software development project with these participants:
- TechCorp (vendor): Project Manager Sarah, Developer John, Tech Lead Michael
- GlobalBank (client): IT Director Robert, Security Manager James
- CloudSys (subcontractor): Solutions Architect Tom

The email chain should cover:
1. Initial project kickoff and requirements gathering
2. Technical architecture discussion
3. Security review concerns from the client
4. Timeline negotiation
5. Resource allocation issues
6. A technical blocker and its resolution
7. Status update before milestone delivery

Make it realistic with proper email etiquette, some back-and-forth, and occasional CC additions.
Generate 10-12 emails in the chain.

Format each email as JSON with: from, to, cc, subject, body, datetime (as ISO string)
"""
        
        elif scenario_type == "incident_response":
            prompt = """
Generate an urgent incident response email chain with:
- Initial alert from monitoring system
- Engineers discussing the issue
- Management asking for updates
- Customer communication drafts
- Resolution steps
- Post-mortem scheduling

Include appropriate urgency, technical details, and management communication.
Generate 8-10 emails showing the progression from detection to resolution.

Format each email as JSON with: from, to, cc, subject, body, datetime
"""
        
        elif scenario_type == "sales_to_implementation":
            prompt = """
Generate an email chain showing progression from sales inquiry to project implementation:
1. Initial customer inquiry
2. Sales team response with pricing
3. Technical feasibility discussion
4. Contract negotiation
5. Signed agreement confirmation
6. Implementation kickoff
7. Technical onboarding
8. First milestone delivery

Show the handoff between sales and implementation teams.
Generate 10-12 emails.

Format each email as JSON with: from, to, cc, subject, body, datetime
"""
        
        else:
            prompt = "Generate a professional email chain between colleagues discussing a project. Include 5-6 emails."
        
        response = await self.generate_with_llm(prompt, temperature=0.8)
        emails = self._parse_llm_json_response(response)
        return self._add_email_metadata(emails, EmailScenario.CLIENT_PROJECT)
    
    def _parse_llm_json_response(self, response: str) -> list:
        """Parse JSON responses from LLM more robustly"""
        emails = []
        
        # Try to extract JSON objects from the response
        import re
        
        # Look for JSON array
        array_match = re.search(r'\[[\s\S]*\]', response)
        if array_match:
            try:
                emails = json.loads(array_match.group())
                return emails
            except:
                pass
        
        # Look for individual JSON objects
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.finditer(json_pattern, response)
        
        for match in matches:
            try:
                email = json.loads(match.group())
                if 'from' in email or 'subject' in email:
                    emails.append(email)
            except:
                continue
        
        # If still no emails, try line-by-line parsing
        if not emails:
            current_email = {}
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('{'):
                    try:
                        email = json.loads(line.rstrip(','))
                        emails.append(email)
                    except:
                        pass
        
        return emails


async def generate_test_dataset():
    """Generate a comprehensive test dataset"""
    generator = AdvancedEmailGenerator()
    ingester = EmailIngester()
    
    # Setup companies
    generator.setup_default_companies()
    
    print("=" * 60)
    print("MOCK EMAIL GENERATION AND INGESTION SYSTEM")
    print("=" * 60)
    
    all_generated = []
    
    # 1. Generate standard scenarios
    print("\n📧 Generating Standard Scenarios...")
    standard_scenarios = [
        (EmailScenario.INTERNAL_DISCUSSION, 5, {"topic": "Q4 Planning"}),
        (EmailScenario.CLIENT_PROJECT, 8, {"project": "Mobile App Development"}),
        (EmailScenario.VENDOR_NEGOTIATION, 6, {"topic": "Cloud Services Contract"}),
        (EmailScenario.SUPPORT_TICKET, 4, {"issue": "API Performance Issues"}),
        (EmailScenario.TEAM_COLLABORATION, 5, {"project": "Database Migration"}),
        (EmailScenario.MEETING_COORDINATION, 4, {"topic": "Architecture Review"}),
    ]
    
    for scenario, num_emails, context in standard_scenarios:
        print(f"\n  → Generating {scenario.value}...")
        try:
            emails = await generator.generate_email_chain(scenario, num_emails, context)
            all_generated.extend(emails)
            print(f"    ✓ Generated {len(emails)} emails")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    # 2. Generate complex scenarios
    print("\n🔧 Generating Complex Scenarios...")
    complex_scenarios = [
        "multi_company_project",
        "incident_response",
        "sales_to_implementation"
    ]
    
    for scenario in complex_scenarios:
        print(f"\n  → Generating {scenario}...")
        try:
            emails = await generator.generate_complex_scenario(scenario)
            all_generated.extend(emails)
            print(f"    ✓ Generated {len(emails)} emails")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    # 3. Save generated emails
    print("\n💾 Saving generated emails...")
    output_file = "generated_test_emails.json"
    with open(output_file, 'w') as f:
        json.dump(all_generated, f, indent=2)
    print(f"  ✓ Saved {len(all_generated)} emails to {output_file}")
    
    # 4. Ingest into database
    print("\n📥 Ingesting emails into database...")
    success_count = await ingester.ingest_email_chain(all_generated)
    print(f"  ✓ Successfully ingested {success_count}/{len(all_generated)} emails")
    
    # 5. Generate statistics
    print("\n📊 Generation Statistics:")
    print(f"  • Total emails generated: {len(all_generated)}")
    print(f"  • Unique threads: {len(set(e.get('thread_id') for e in all_generated if e.get('thread_id')))}")
    print(f"  • Unique senders: {len(set(e.get('from') for e in all_generated if e.get('from')))}")
    print(f"  • Date range: {min(e.get('datetime', '') for e in all_generated)[:10]} to {max(e.get('datetime', '') for e in all_generated)[:10]}")
    
    return all_generated


async def interactive_generation():
    """Interactive email generation mode"""
    generator = AdvancedEmailGenerator()
    ingester = EmailIngester()
    generator.setup_default_companies()
    
    print("\n🎮 INTERACTIVE EMAIL GENERATION MODE")
    print("=" * 40)
    
    while True:
        print("\nSelect an option:")
        print("1. Generate standard scenario")
        print("2. Generate custom prompt")
        print("3. Generate and ingest batch")
        print("4. Exit")
        
        choice = input("\nYour choice: ").strip()
        
        if choice == "1":
            print("\nAvailable scenarios:")
            for i, scenario in enumerate(EmailScenario, 1):
                print(f"{i}. {scenario.value}")
            
            scenario_num = int(input("Select scenario number: "))
            num_emails = int(input("Number of emails to generate: "))
            
            scenario = list(EmailScenario)[scenario_num - 1]
            emails = await generator.generate_email_chain(scenario, num_emails)
            
            print(f"\n✓ Generated {len(emails)} emails")
            
            if input("Ingest into database? (y/n): ").lower() == 'y':
                success = await ingester.ingest_email_chain(emails)
                print(f"✓ Ingested {success} emails")
        
        elif choice == "2":
            print("\nEnter your custom prompt for email generation:")
            prompt = input("> ")
            
            response = await generator.generate_with_llm(prompt)
            print("\nGenerated content:")
            print(response)
            
            if input("\nParse and ingest? (y/n): ").lower() == 'y':
                emails = generator._parse_llm_json_response(response)
                if emails:
                    success = await ingester.ingest_email_chain(emails)
                    print(f"✓ Ingested {success} emails")
                else:
                    print("Could not parse emails from response")
        
        elif choice == "3":
            num_chains = int(input("Number of email chains to generate: "))
            emails_per_chain = int(input("Emails per chain: "))
            
            all_emails = []
            for i in range(num_chains):
                scenario = random.choice(list(EmailScenario))
                print(f"Generating chain {i+1}/{num_chains} ({scenario.value})...")
                
                emails = await generator.generate_email_chain(scenario, emails_per_chain)
                all_emails.extend(emails)
            
            print(f"\n✓ Generated {len(all_emails)} total emails")
            
            if input("Ingest all into database? (y/n): ").lower() == 'y':
                success = await ingester.ingest_email_chain(all_emails)
                print(f"✓ Ingested {success} emails")
        
        elif choice == "4":
            break
        
        else:
            print("Invalid choice")
    
    print("\n👋 Goodbye!")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate and ingest mock emails")
    parser.add_argument("--mode", choices=["batch", "interactive"], default="batch",
                       help="Generation mode")
    parser.add_argument("--api-url", default="http://localhost:8000",
                       help="MCP Server API URL")
    parser.add_argument("--lm-studio-url", default="http://localhost:1234/v1",
                       help="LM Studio API URL")
    parser.add_argument("--auth-token", default="my-personal-api-token-12345",
                       help="API authentication token")
    
    args = parser.parse_args()
    
    if args.mode == "interactive":
        await interactive_generation()
    else:
        await generate_test_dataset()


if __name__ == "__main__":
    asyncio.run(main())