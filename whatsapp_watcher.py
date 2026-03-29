import time
import logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(r'C:\Users\inn\Documents\AI_Employee_Vault\Logs\whatsapp_watcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

VAULT = Path(r'C:\Users\inn\Documents\AI_Employee_Vault')
NEEDS_ACTION = VAULT / 'Needs_Action'
SESSION_PATH = str(VAULT / 'whatsapp_session')
CHECK_INTERVAL = 30
processed = set()

def safe_click(page, selector):
    try:
        el = page.query_selector(selector)
        if el and el.is_visible():
            el.click()
            return True
    except:
        pass
    return False

def safe_text(el):
    try:
        return el.inner_text().strip() if el else ''
    except:
        return ''

def get_unread_chats(page):
    # Multiple selectors try karo
    selectors = [
        'div[role="listitem"]',
        '[data-testid="cell-frame-container"]',
        'div[tabindex="-1"]'
    ]
    for sel in selectors:
        try:
            chats = page.query_selector_all(sel)
            if chats and len(chats) > 0:
                logger.info(f'Chats found with selector: {sel} — Count: {len(chats)}')
                return chats
        except:
            continue
    return []

def has_unread(chat):
    unread_selectors = [
        '[data-testid="icon-unread-count"]',
        'span[data-testid="unread-count"]',
        'span[aria-label*="unread"]',
        'span._ahlk',
        'span.x1yc453h'
    ]
    for sel in unread_selectors:
        try:
            el = chat.query_selector(sel)
            if el and el.is_visible():
                return True
        except:
            continue
    return False

def extract_chat_info(chat):
    name = 'Unknown'
    preview = 'New message'
    
    name_selectors = [
        '[data-testid="cell-frame-title"]',
        'span[title]',
        'span._ao3e',
        'div._ao3e span'
    ]
    for sel in name_selectors:
        try:
            el = chat.query_selector(sel)
            text = safe_text(el)
            if text:
                name = text
                break
        except:
            continue

    preview_selectors = [
        'span.x1iyjqo2',
        '[data-testid="last-msg-status"] + span',
        'div._ao3e + div span',
        'span._ao3f'
    ]
    for sel in preview_selectors:
        try:
            el = chat.query_selector(sel)
            text = safe_text(el)
            if text:
                preview = text
                break
        except:
            continue

    # Fallback - inner text se extract karo
    if name == 'Unknown':
        try:
            lines = [l.strip() for l in chat.inner_text().split('\n') if l.strip()]
            if lines:
                name = lines[0]
            if len(lines) > 1:
                preview = lines[1]
        except:
            pass

    return name, preview

def create_task_file(name, preview):
    safe_name = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    timestamp = datetime.now().strftime('%H%M%S')
    task_file = NEEDS_ACTION / f'WHATSAPP_{safe_name}_{timestamp}.md'
    task_file.write_text(f'''---
type: whatsapp
from: {name}
received: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
status: pending
---

## Naya WhatsApp Message!
**From:** {name}
**Preview:** {preview}

## Claude ke liye Tasks
- [ ] Message content check karo
- [ ] Reply draft karo agar zaroorat ho
- [ ] Urgent hai toh Pending_Approval mein bhejo
- [ ] Dashboard update karo
- [ ] Move to /Done jab complete ho
''', encoding='utf-8')
    return task_file

def check_messages(page):
    global processed
    try:
        page.wait_for_timeout(2000)
        chats = get_unread_chats(page)
        
        if not chats:
            logger.info('Koi chat nahi mili — retry next cycle')
            return

        found = 0
        for chat in chats:
            try:
                if not has_unread(chat):
                    continue

                name, preview = extract_chat_info(chat)
                chat_id = f"{name}_{datetime.now().strftime('%Y%m%d_%H')}"

                if chat_id in processed:
                    continue

                task_file = create_task_file(name, preview)
                processed.add(chat_id)
                found += 1
                logger.info(f'[NEW] {name}: {preview} → {task_file.name}')

            except Exception as e:
                logger.error(f'Chat skip: {e}')
                continue

        if found > 0:
            logger.info(f'✅ {found} naye messages capture hue!')
        else:
            logger.info('Koi naya unread message nahi...')

    except Exception as e:
        logger.error(f'Check error: {e}')

def main():
    logger.info('=== WhatsApp Watcher Shuru Ho Gaya ===')
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            SESSION_PATH,
            channel='chrome',
            headless=False,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )

        page = browser.new_page() if not browser.pages else browser.pages[0]
        logger.info('WhatsApp Web khul raha hai...')
        page.goto('https://web.whatsapp.com')
        logger.info('QR scan karo agar pehli baar hai...')

        # Wait for any of these selectors
        try:
            page.wait_for_selector(
                '#pane-side, [aria-label="Chat list"], div[role="listitem"]',
                timeout=120000
            )
        except PlaywrightTimeout:
            logger.error('WhatsApp load timeout — restart karo')
            return

        page.wait_for_timeout(5000)
        logger.info('✅ WhatsApp connected! Monitoring shuru...')

        while True:
            check_messages(page)
            time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()
