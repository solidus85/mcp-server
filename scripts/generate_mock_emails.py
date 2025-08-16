#!/usr/bin/env python3
"""
Mock Email Generation System using LM Studio
Generates realistic email chains for testing purposes
"""

import json
import random
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid


class EmailScenario(Enum):
    """Different types of email scenarios"""
    INTERNAL_DISCUSSION = "internal_discussion"
    CLIENT_PROJECT = "client_project"
    VENDOR_NEGOTIATION = "vendor_negotiation"
    SUPPORT_TICKET = "support_ticket"
    TEAM_COLLABORATION = "team_collaboration"
    EXECUTIVE_BRIEFING = "executive_briefing"
    SALES_INQUIRY = "sales_inquiry"
    MEETING_COORDINATION = "meeting_coordination"


@dataclass
class Company:
    """Company information for email generation"""
    name: str
    domain: str
    industry: str
    employees: List['Person'] = field(default_factory=list)
    
    def __hash__(self):
        return hash((self.name, self.domain))
    
    def __eq__(self, other):
        if not isinstance(other, Company):
            return False
        return self.name == other.name and self.domain == other.domain


@dataclass
class Person:
    """Person information for email generation"""
    first_name: str
    last_name: str
    email: str
    role: str
    company: Company
    department: Optional[str] = None
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class EmailGenerator:
    """Generate mock emails using LM Studio"""
    
    def __init__(self, lm_studio_url: str = "http://localhost:1234/v1"):
        self.api_url = lm_studio_url
        self.companies = []
        self.people = []
        
    def create_company(self, name: str, domain: str, industry: str) -> Company:
        """Create a company"""
        company = Company(name=name, domain=domain, industry=industry)
        self.companies.append(company)
        return company
    
    def create_person(self, first_name: str, last_name: str, role: str, 
                     company: Company, department: Optional[str] = None) -> Person:
        """Create a person"""
        email = f"{first_name.lower()}.{last_name.lower()}@{company.domain}"
        person = Person(
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            company=company,
            department=department
        )
        company.employees.append(person)
        self.people.append(person)
        return person
    
    def setup_default_companies(self):
        """Setup default companies for testing"""
        # Main company
        techcorp = self.create_company("TechCorp Solutions", "techcorp.com", "Technology")
        self.create_person("John", "Smith", "Senior Developer", techcorp, "Engineering")
        self.create_person("Sarah", "Johnson", "Project Manager", techcorp, "PMO")
        self.create_person("Michael", "Chen", "Tech Lead", techcorp, "Engineering")
        self.create_person("Emily", "Davis", "Product Manager", techcorp, "Product")
        self.create_person("David", "Wilson", "CEO", techcorp, "Executive")
        
        # Client company
        globalbank = self.create_company("Global Bank Inc", "globalbank.com", "Finance")
        self.create_person("Robert", "Thompson", "IT Director", globalbank, "IT")
        self.create_person("Lisa", "Anderson", "Project Sponsor", globalbank, "Operations")
        self.create_person("James", "Martinez", "Security Manager", globalbank, "Security")
        
        # Vendor company
        cloudsys = self.create_company("CloudSys Infrastructure", "cloudsys.io", "Cloud Services")
        self.create_person("Alex", "Kumar", "Sales Engineer", cloudsys, "Sales")
        self.create_person("Maria", "Garcia", "Account Manager", cloudsys, "Sales")
        self.create_person("Tom", "Brown", "Solutions Architect", cloudsys, "Technical")
        
        # Consulting firm
        advisors = self.create_company("Strategic Advisors", "advisors.com", "Consulting")
        self.create_person("Jennifer", "White", "Senior Consultant", advisors, "Consulting")
        self.create_person("Mark", "Taylor", "Principal", advisors, "Leadership")
    
    async def generate_with_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate content using LM Studio"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "phi-4",
                "messages": [
                    {"role": "system", "content": "You are an expert at creating realistic business email content."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": 1000,
                "stream": False
            }
            
            async with session.post(f"{self.api_url}/chat/completions", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    raise Exception(f"LM Studio API error: {response.status}")
    
    def build_scenario_prompt(self, scenario: EmailScenario, participants: List[Person], 
                            context: Dict[str, Any]) -> str:
        """Build a prompt for the LLM based on scenario"""
        
        prompts = {
            EmailScenario.INTERNAL_DISCUSSION: """
Create an email chain between {participants} about {topic}.
The discussion should be professional and include:
- Initial proposal or question
- Responses with feedback and suggestions
- Follow-up questions
- Resolution or next steps
Keep each email realistic and concise.
""",
            EmailScenario.CLIENT_PROJECT: """
Create an email chain between {client_participants} from {client_company} and {vendor_participants} from {vendor_company} about {project}.
Include:
- Project requirements discussion
- Timeline and milestone negotiations
- Technical clarifications
- Status updates
Make it professional with appropriate client-vendor dynamics.
""",
            EmailScenario.VENDOR_NEGOTIATION: """
Create an email chain about vendor negotiation between {participants}.
Include:
- Initial inquiry or RFP
- Pricing discussions
- Service level agreements
- Contract terms
- Final agreement
Keep it business-focused and realistic.
""",
            EmailScenario.SUPPORT_TICKET: """
Create a support ticket email chain between {customer} and {support_team} about {issue}.
Include:
- Initial problem report
- Troubleshooting steps
- Additional information requests
- Resolution attempts
- Final resolution or escalation
""",
            EmailScenario.TEAM_COLLABORATION: """
Create a collaborative email chain between team members {participants} working on {project}.
Include:
- Task assignments
- Progress updates
- Blocker discussions
- Code reviews or document reviews
- Meeting scheduling
Keep it casual but professional.
""",
            EmailScenario.MEETING_COORDINATION: """
Create an email chain for coordinating a meeting between {participants} about {topic}.
Include:
- Initial meeting request
- Schedule conflicts
- Agenda proposals
- Location/call details
- Pre-meeting materials
- Post-meeting follow-up
"""
        }
        
        template = prompts.get(scenario, prompts[EmailScenario.INTERNAL_DISCUSSION])
        return template.format(**context)
    
    async def generate_email_chain(self, scenario: EmailScenario, 
                                  num_emails: int = 5,
                                  custom_context: Optional[Dict] = None) -> List[Dict]:
        """Generate a complete email chain"""
        
        # Select participants based on scenario
        participants = self._select_participants(scenario)
        
        # Build context
        context = self._build_context(scenario, participants)
        if custom_context:
            context.update(custom_context)
        
        # Generate the prompt
        prompt = self.build_scenario_prompt(scenario, participants, context)
        prompt += f"\n\nGenerate exactly {num_emails} emails in JSON format with fields: from, to, cc (optional), subject, body, datetime"
        
        # Generate emails using LLM
        response = await self.generate_with_llm(prompt)
        
        # Parse and structure the emails
        emails = self._parse_email_response(response, participants)
        
        # Add metadata and threading
        emails = self._add_email_metadata(emails, scenario)
        
        return emails
    
    def _select_participants(self, scenario: EmailScenario) -> List[Person]:
        """Select appropriate participants for the scenario"""
        if not self.people:
            self.setup_default_companies()
        
        if scenario == EmailScenario.INTERNAL_DISCUSSION:
            # Select people from the same company
            company = random.choice(self.companies)
            return random.sample([p for p in self.people if p.company == company], 
                                min(3, len(company.employees)))
        
        elif scenario == EmailScenario.CLIENT_PROJECT:
            # Select from different companies
            companies = random.sample(self.companies, min(2, len(self.companies)))
            participants = []
            for company in companies:
                participants.extend(random.sample(company.employees, 
                                                min(2, len(company.employees))))
            return participants
        
        else:
            # Random selection
            return random.sample(self.people, min(4, len(self.people)))
    
    def _build_context(self, scenario: EmailScenario, participants: List[Person]) -> Dict:
        """Build context for the email generation"""
        topics = {
            EmailScenario.INTERNAL_DISCUSSION: [
                "Q4 planning and budget allocation",
                "new feature development timeline",
                "team restructuring proposal",
                "security incident response",
                "performance review process changes"
            ],
            EmailScenario.CLIENT_PROJECT: [
                "ERP system implementation",
                "cloud migration project",
                "mobile app development",
                "data analytics platform",
                "cybersecurity assessment"
            ],
            EmailScenario.VENDOR_NEGOTIATION: [
                "SaaS platform licensing",
                "hardware procurement",
                "consulting services agreement",
                "maintenance contract renewal",
                "training services"
            ],
            EmailScenario.SUPPORT_TICKET: [
                "application performance issues",
                "login authentication problems",
                "data synchronization errors",
                "report generation failures",
                "API integration issues"
            ],
            EmailScenario.TEAM_COLLABORATION: [
                "sprint planning for next release",
                "code review for authentication module",
                "database optimization project",
                "UI/UX redesign initiative",
                "testing strategy discussion"
            ],
            EmailScenario.MEETING_COORDINATION: [
                "quarterly business review",
                "project kickoff meeting",
                "technical architecture review",
                "stakeholder alignment session",
                "team retrospective"
            ]
        }
        
        context = {
            "participants": ", ".join([p.full_name for p in participants]),
            "topic": random.choice(topics.get(scenario, ["general discussion"])),
            "project": random.choice(topics.get(EmailScenario.CLIENT_PROJECT, ["project"])),
            "issue": random.choice(topics.get(EmailScenario.SUPPORT_TICKET, ["technical issue"]))
        }
        
        # Add company-specific context
        if len(set(p.company for p in participants)) > 1:
            companies = list(set(p.company for p in participants))
            context["client_company"] = companies[0].name
            context["vendor_company"] = companies[1].name if len(companies) > 1 else companies[0].name
            context["client_participants"] = ", ".join([p.full_name for p in participants if p.company == companies[0]])
            context["vendor_participants"] = ", ".join([p.full_name for p in participants if p.company != companies[0]])
        
        # Add specific participants
        context["customer"] = participants[0].full_name if participants else "Customer"
        context["support_team"] = ", ".join([p.full_name for p in participants[1:3]]) if len(participants) > 1 else "Support Team"
        
        return context
    
    def _parse_email_response(self, response: str, participants: List[Person]) -> List[Dict]:
        """Parse LLM response into structured emails"""
        emails = []
        
        try:
            # Try to parse as JSON directly
            import re
            json_matches = re.findall(r'\{[^}]+\}', response, re.DOTALL)
            
            for match in json_matches:
                try:
                    email_data = json.loads(match)
                    emails.append(email_data)
                except:
                    pass
        except:
            pass
        
        # If JSON parsing fails, create structured emails from text
        if not emails:
            lines = response.split('\n')
            current_email = {}
            
            for line in lines:
                if line.startswith('From:'):
                    if current_email:
                        emails.append(current_email)
                    current_email = {'from': line[5:].strip()}
                elif line.startswith('To:'):
                    current_email['to'] = line[3:].strip()
                elif line.startswith('Subject:'):
                    current_email['subject'] = line[8:].strip()
                elif line.startswith('Body:') or line.startswith('Content:'):
                    current_email['body'] = line[5:].strip() if line.startswith('Body:') else line[8:].strip()
            
            if current_email:
                emails.append(current_email)
        
        # Ensure we have valid email addresses
        for email in emails:
            # Map names to actual email addresses
            for person in participants:
                if person.full_name in email.get('from', ''):
                    email['from'] = person.email
                if person.full_name in email.get('to', ''):
                    email['to'] = person.email
        
        return emails
    
    def _add_email_metadata(self, emails: List[Dict], scenario: EmailScenario) -> List[Dict]:
        """Add metadata like timestamps, IDs, and threading"""
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        base_time = datetime.now() - timedelta(days=random.randint(1, 30))
        
        for i, email in enumerate(emails):
            # Add email ID
            email['email_id'] = f"msg_{uuid.uuid4().hex[:8]}"
            email['message_id'] = f"<{email['email_id']}@{email.get('from', 'example.com').split('@')[-1]}>"
            
            # Add threading
            email['thread_id'] = thread_id
            if i > 0:
                email['in_reply_to'] = emails[i-1]['message_id']
                # Prepend RE: to subject if not present
                if not email.get('subject', '').startswith('RE:'):
                    email['subject'] = f"RE: {emails[0].get('subject', 'Discussion')}"
            
            # Add timestamp
            email['datetime'] = (base_time + timedelta(hours=i*random.randint(1, 6))).isoformat()
            
            # Add scenario tag
            email['tags'] = [scenario.value]
            
            # Add default values
            email.setdefault('cc', [])
            email.setdefault('bcc', [])
            email.setdefault('attachments', [])
            
        return emails


async def main():
    """Main function to demonstrate email generation"""
    generator = EmailGenerator()
    
    # Setup companies and people
    generator.setup_default_companies()
    
    print("Mock Email Generation System")
    print("=" * 50)
    
    # Generate different scenarios
    scenarios_to_generate = [
        (EmailScenario.CLIENT_PROJECT, 6),
        (EmailScenario.INTERNAL_DISCUSSION, 4),
        (EmailScenario.VENDOR_NEGOTIATION, 5),
        (EmailScenario.TEAM_COLLABORATION, 4),
    ]
    
    all_emails = []
    
    for scenario, num_emails in scenarios_to_generate:
        print(f"\nGenerating {scenario.value} scenario with {num_emails} emails...")
        
        try:
            emails = await generator.generate_email_chain(scenario, num_emails)
            all_emails.extend(emails)
            
            print(f"Generated {len(emails)} emails for {scenario.value}")
            
            # Print sample
            if emails:
                print(f"  First email: {emails[0].get('subject', 'No subject')}")
                print(f"  From: {emails[0].get('from', 'Unknown')}")
                print(f"  To: {emails[0].get('to', 'Unknown')}")
        
        except Exception as e:
            print(f"Error generating {scenario.value}: {e}")
    
    # Save to file
    output_file = "generated_emails.json"
    with open(output_file, 'w') as f:
        json.dump(all_emails, f, indent=2)
    
    print(f"\n✓ Generated {len(all_emails)} total emails")
    print(f"✓ Saved to {output_file}")
    
    return all_emails


if __name__ == "__main__":
    asyncio.run(main())