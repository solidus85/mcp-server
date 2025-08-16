#!/usr/bin/env python3
"""
Simple script to ingest generated emails into the database
"""

import json
import asyncio
import aiohttp
import sys
from pathlib import Path


async def ingest_emails(file_path: str = "generated_emails.json"):
    """Ingest emails from JSON file into database"""
    
    # Load emails from file
    with open(file_path, 'r') as f:
        emails = json.load(f)
    
    print(f"Found {len(emails)} emails to ingest")
    
    api_url = "http://localhost:8000"
    auth_token = "my-personal-api-token-12345"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    success_count = 0
    failed_count = 0
    
    async with aiohttp.ClientSession() as session:
        for i, email in enumerate(emails, 1):
            # Transform to API format
            payload = {
                "to": email.get("to", []) if isinstance(email.get("to"), list) else [email.get("to")],
                "from": email.get("from"),
                "subject": email.get("subject", "No Subject"),
                "datetime": email.get("datetime"),
                "body": f"<html><body><p>{email.get('body', '')}</p></body></html>",
                "body_text": email.get("body", ""),
                "cc": email.get("cc", []) if isinstance(email.get("cc"), list) else 
                      [email.get("cc")] if email.get("cc") else [],
                "email_id": email.get("email_id"),
                "message_id": email.get("message_id"),
                "in_reply_to": email.get("in_reply_to"),
                "thread_id": email.get("thread_id"),
                "headers": email.get("headers", {}),
                "attachments": email.get("attachments", []),
                "size_bytes": len(email.get("body", ""))
            }
            
            try:
                async with session.post(
                    f"{api_url}/api/v1/emails/ingest",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in [200, 201]:
                        success_count += 1
                        print(f"✓ [{i}/{len(emails)}] Ingested: {email.get('subject', 'No subject')[:50]}")
                    else:
                        failed_count += 1
                        error = await response.text()
                        print(f"✗ [{i}/{len(emails)}] Failed: {email.get('subject', 'No subject')[:50]}")
                        print(f"  Error: {error[:100]}")
            except asyncio.TimeoutError:
                failed_count += 1
                print(f"✗ [{i}/{len(emails)}] Timeout: {email.get('subject', 'No subject')[:50]}")
            except Exception as e:
                failed_count += 1
                print(f"✗ [{i}/{len(emails)}] Error: {str(e)[:100]}")
            
            # Small delay between requests
            await asyncio.sleep(0.05)
    
    print(f"\n{'='*50}")
    print(f"Ingestion complete!")
    print(f"✓ Success: {success_count}")
    print(f"✗ Failed: {failed_count}")
    print(f"Total: {len(emails)}")
    
    return success_count, failed_count


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ingest generated emails")
    parser.add_argument("--file", default="generated_emails.json", help="JSON file with emails")
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"Error: File {args.file} not found")
        sys.exit(1)
    
    await ingest_emails(args.file)


if __name__ == "__main__":
    asyncio.run(main())