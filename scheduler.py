import schedule
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(r'C:\Users\inn\Documents\AI_Employee_Vault\Logs\scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

VAULT = Path(r'C:\Users\inn\Documents\AI_Employee_Vault')

def morning_briefing():
    logger.info('Morning Briefing trigger ho raha hai...')
    
    briefing_prompt = f'''You are my AI Employee. Today is {datetime.now().strftime('%Y-%m-%d')}.

Please do the following:
1. Check all files in Needs_Action/ folder
2. Check Done/ folder for tasks completed this week
3. Check Pending_Approval/ for any pending items
4. Generate a Monday Morning CEO Briefing in Briefings/ folder named {datetime.now().strftime('%Y-%m-%d')}_Briefing.md with:
   - Summary of completed tasks
   - Pending approvals
   - Any alerts or suggestions
5. Update Dashboard.md with latest status

Start now.'''

    prompt_file = VAULT / 'Needs_Action' / f'BRIEFING_TRIGGER_{datetime.now().strftime("%Y%m%d_%H%M")}.md'
    prompt_file.write_text(f'''---
type: scheduled_task
task: morning_briefing
created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
status: pending
---

## Morning Briefing Request

{briefing_prompt}
''', encoding='utf-8')
    
    logger.info('Morning Briefing task file bani! Claude process karega.')

def process_emails():
    logger.info('Email processing trigger ho raha hai...')
    task_file = VAULT / 'Needs_Action' / f'EMAIL_PROCESS_{datetime.now().strftime("%Y%m%d_%H%M")}.md'
    task_file.write_text(f'''---
type: scheduled_task
task: process_emails
created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
status: pending
---

## Email Processing Request
Check Needs_Action/ for any unprocessed emails and handle them per Company_Handbook rules.
''', encoding='utf-8')
    logger.info('Email processing task created!')

def main():
    logger.info('=== AI Employee Scheduler Shuru Ho Gaya ===')
    
    # Har roz subah 8 baje morning briefing
    schedule.every().day.at('08:00').do(morning_briefing)
    
    # Har 2 ghante email process karo
    schedule.every(2).hours.do(process_emails)
    
    # Har Sunday raat 10 baje weekly audit
    schedule.every().sunday.at('22:00').do(morning_briefing)
    
    logger.info('Schedule set ho gaya:')
    logger.info('  - Har roz 08:00 AM: Morning Briefing')
    logger.info('  - Har 2 ghante: Email Processing')
    logger.info('  - Har Sunday 10 PM: Weekly Audit')
    
    # Test ke liye abhi bhi ek baar chalao
    logger.info('Pehla test run abhi...')
    morning_briefing()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    main()
