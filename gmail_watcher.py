import os
import time
import logging
from pathlib import Path
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(r'C:\Users\inn\Documents\AI_Employee_Vault\Logs\gmail_watcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Gmail API scope - sirf read access
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
VAULT = Path(r'C:\Users\inn\Documents\AI_Employee_Vault')
NEEDS_ACTION = VAULT / 'Needs_Action'
CREDENTIALS_FILE = VAULT / 'credentials.json'
TOKEN_FILE = VAULT / 'token.json'
CHECK_INTERVAL = 120  # har 2 minute mein check

def get_gmail_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def check_emails(service, processed_ids):
    results = service.users().messages().list(
        userId='me',
        q='is:unread is:important',
        maxResults=10
    ).execute()
    
    messages = results.get('messages', [])
    new_emails = [m for m in messages if m['id'] not in processed_ids]
    
    for msg in new_emails:
        full_msg = service.users().messages().get(
            userId='me', id=msg['id']
        ).execute()
        
        headers = {h['name']: h['value'] for h in full_msg['payload']['headers']}
        sender = headers.get('From', 'Unknown')
        subject = headers.get('Subject', 'No Subject')
        snippet = full_msg.get('snippet', '')
        
        # Task file banao Needs_Action mein
        task_file = NEEDS_ACTION / f'EMAIL_{msg["id"][:8]}.md'
        task_file.write_text(f'''---
type: email
from: {sender}
subject: {subject}
received: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
status: pending
---

## Naya Email Aya!
**From:** {sender}
**Subject:** {subject}

**Preview:**
{snippet}

## Claude ke liye Tasks
- [ ] Email content check karo
- [ ] Reply draft karo agar zaroorat ho
- [ ] Dashboard update karo
- [ ] Move to /Done jab complete ho
''', encoding='utf-8')
        
        processed_ids.add(msg['id'])
        logger.info(f'[NEW EMAIL] From: {sender} | Subject: {subject}')
    
    return processed_ids

def main():
    logger.info('=== Gmail Watcher Shuru Ho Gaya ===')
    logger.info(f'Har {CHECK_INTERVAL} second mein check karega...')
    
    service = get_gmail_service()
    processed_ids = set()
    
    logger.info('✅ Gmail connected! Emails monitor ho rahe hain...')
    
    while True:
        try:
            processed_ids = check_emails(service, processed_ids)
        except Exception as e:
            logger.error(f'Error: {e}')
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()
