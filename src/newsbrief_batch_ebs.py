#!/usr/bin/env python3
# NewsBrief Batch Processor for EBS (INSERT-only)
# Replicates the 8540 cron behavior without UPDATE operations.

import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import os
import re
import json
import time
from datetime import datetime, timedelta, timezone
from threading import Lock

import lancedb
import pandas as pd
from bs4 import BeautifulSoup

from id_tracker_ebs import is_digest_processed, mark_digest_processed

import sys
sys.path.insert(0, '/home/ubuntu/newspaper_project/handlers')
from newsbrief_with_links_handler import enrich_newsbrief_with_links
from tweet_keyword_handler import extract_tweet_keywords


GMAIL_USER = os.getenv('GMAIL_USER', 'prjfiles@gmail.com')
GMAIL_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', 'kwgfutaxitoesvlz')
DB_URI = '/mnt/lancedb_clean'
TABLE_NAME = 'unified_feed'
ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_KEY:
    raise RuntimeError('ANTHROPIC_API_KEY environment variable is required for NewsBrief processing')

FETCH_WINDOW_DAYS = 7
MAX_DIGESTS = 20
DELAY_SECONDS = 1

ALLOWLIST = [
    'Bloomberg',
    'WSJ',
    'Reuters',
    "Barron's",
    'Estadão',
    'Folha',
    'Business Insider',
    'Financial Times',
    'Topdown Charts',
    'Globo'
]

EXCLUSIONS_PATH = '/home/ubuntu/newspaper_project/keyword_exclusions.json'
if os.path.exists(EXCLUSIONS_PATH):
    with open(EXCLUSIONS_PATH, 'r') as f:
        KEYWORD_EXCLUSIONS = json.load(f)
else:
    KEYWORD_EXCLUSIONS = []

_print_lock = Lock()


def log(message: str) -> None:
    with _print_lock:
        print(message, flush=True)


def parse_email_datetime(date_header: str) -> datetime:
    if not date_header:
        return datetime.utcnow().replace(tzinfo=timezone.utc)
    try:
        dt = parsedate_to_datetime(date_header)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return datetime.utcnow().replace(tzinfo=timezone.utc)


def format_created_at(date_header: str) -> str:
    dt = parse_email_datetime(date_header)
    iso = dt.isoformat()
    if iso.endswith('+00:00'):
        iso = iso[:-6] + 'Z'
    return iso


def decode_str(value: str) -> str:
    if not value:
        return ''
    pieces = decode_header(value)
    text = ''
    for chunk, enc in pieces:
        if isinstance(chunk, bytes):
            text += chunk.decode(enc or 'utf-8', errors='ignore')
        else:
            text += chunk
    return text


def sender_allowed(sender_name: str) -> bool:
    lower = sender_name.lower()
    return any(tag.lower() in lower for tag in ALLOWLIST)


def connect_db():
    db = lancedb.connect(DB_URI)
    return db.open_table(TABLE_NAME)


def fetch_candidates():
    log('📥 Connecting to Gmail…')
    imap = imaplib.IMAP4_SSL('imap.gmail.com')
    imap.login(GMAIL_USER, GMAIL_PASSWORD)
    imap.select('INBOX')

    since_date = (datetime.now() - timedelta(days=FETCH_WINDOW_DAYS)).strftime('%d-%b-%Y')
    status, data = imap.search(None, f'(SINCE {since_date})')
    if status != 'OK':
        log('❌ Gmail search failed')
        imap.logout()
        return []

    email_ids = data[0].split()
    log(f"   📧 {len(email_ids)} emails found in window")

    digests = []
    for eid in reversed(email_ids):
        if len(digests) >= MAX_DIGESTS:
            break

        status, msg_data = imap.fetch(eid, '(RFC822)')
        if status != 'OK':
            continue

        msg = email.message_from_bytes(msg_data[0][1])
        sender_raw = decode_str(msg.get('From', ''))
        sender_name = sender_raw.split('<')[0].strip().strip('"')
        if not sender_allowed(sender_name):
            continue

        subject = decode_str(msg.get('Subject', ''))

        body_text = ''
        body_html = ''
        if msg.is_multipart():
            for part in msg.walk():
                try:
                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue
                    text = payload.decode('utf-8', errors='ignore')
                except Exception:
                    continue

                if part.get_content_type() == 'text/plain' and not body_text:
                    body_text = text
                elif part.get_content_type() == 'text/html' and not body_html:
                    body_html = text
        else:
            payload = msg.get_payload(decode=True) or b''
            text = payload.decode('utf-8', errors='ignore')
            if msg.get_content_type() == 'text/html':
                body_html = text
            else:
                body_text = text

        combined = body_html or body_text
        if len(combined) < 4000:
            continue

        message_id = msg.get('Message-ID') or f"digest-{eid.decode()}"
        date_header = msg.get('Date')
        created_at_iso = format_created_at(date_header)

        digests.append({
            'id': message_id,
            'sender': sender_name,
            'subject': subject,
            'content_text': body_text or BeautifulSoup(body_html, 'html.parser').get_text(separator='\n'),
            'content_html': body_html,
            'created_at': created_at_iso
        })

    imap.logout()
    log(f"   ✅ {len(digests)} NewsBrief candidates")
    return digests


def parse_story_blocks(html: str):
    pattern = r'<strong[^>]*>(\d+)\.\s([^<]+)</strong>(.*?)(?=<strong|$)'
    matches = re.findall(pattern, html, re.DOTALL)
    stories = []
    for number, title, block in matches:
        block = block.strip()
        soup = BeautifulSoup(block, 'html.parser')
        text = soup.get_text(separator='\n').strip()
        link_match = re.search(r'href="([^"]+)"', block)
        link = link_match.group(1) if link_match else ''
        stories.append({
            'number': int(number),
            'title': title.strip(),
            'html': block,
            'text': text,
            'link': link
        })
    return stories


def extract_keywords(text: str):
    try:
        result = extract_tweet_keywords(text[:500], ANTHROPIC_KEY, KEYWORD_EXCLUSIONS)
        keywords = result.get('keywords') or []
        score = float(result.get('score', 8.0))
        return ' • '.join(keywords), score
    except Exception as exc:
        log(f"   ⚠️ Keyword extraction failed: {exc}")
        return '', 7.0


def build_story_records(digest, stories):
    records = []
    for story in stories:
        keywords, score = extract_keywords(story['text'])
        records.append({
            'id': f"{digest['id']}_story_{story['number']}",
            'source_type': 'email',
            'source': 'newsbrief_story',
            'created_at': digest['created_at'],
            'author': digest['sender'],
            'sender': f"{digest['sender']} - Newsbrief",
            'sender_tag': f"{digest['sender']} - Newsbrief",
            'title': f"{story['number']}. {story['title']}",
            'subject': f"{digest['subject']} - Story {story['number']}",
            'content_text': story['text'],
            'content_html': story['html'],
            'enriched_content': story['html'],
            'themes': keywords,
            'actors': None,
            'ai_score': score,
            'sentiment': None,
            'category': 'news',
            'market_impact': None,
            'link': story['link'],
            'parent_id': digest['id'],
            'story_number': story['number'],
            'is_junk': False,
            'custom_fields': json.dumps({'digest_subject': digest['subject']})
        })
    return records


def main():
    log('=' * 80)
    log('🚀 NewsBrief Batch Processor (EBS INSERT-only)')
    log('=' * 80)
    log(datetime.now().strftime('🕒 %Y-%m-%d %H:%M:%S'))

    table = connect_db()
    digests = fetch_candidates()
    if not digests:
        log('✅ No digests found')
        return

    total_stories = 0
    for digest in digests:
        if is_digest_processed(digest['id']):
            log(f"⏭️  Already processed: {digest['subject'][:60]}")
            continue

        log(f"📰 {digest['sender']} — {digest['subject'][:60]}")
        response = enrich_newsbrief_with_links(
            digest['subject'],
            digest['content_text'],
            digest['sender'],
            ANTHROPIC_KEY
        )

        summary_html = response.get('smart_summary', '')
        if not summary_html:
            log('   ❌ Handler returned empty summary')
            continue

        stories = parse_story_blocks(summary_html)
        if not stories:
            log('   ❌ No stories parsed from summary')
            continue

        story_records = build_story_records(digest, stories)
        # Check for existing stories before inserting

        existing_df = table.to_pandas()

        existing_ids = set(existing_df['id'].unique())

        

        # Filter out stories that already exist

        new_story_records = []

        for story in story_records:

            if story['id'] not in existing_ids:

                new_story_records.append(story)

        

        if new_story_records:

            table.add(pd.DataFrame(new_story_records))

            log(f"   ✅ Added {len(new_story_records)} new stories ({len(story_records) - len(new_story_records)} duplicates skipped)")

        else:

            log(f"   ℹ️ All {len(story_records)} stories already exist, skipping")

        

        # Original line (now replaced):

        # table.add(pd.DataFrame(story_records))
        mark_digest_processed(digest['id'])
        total_stories += len(story_records)
        time.sleep(DELAY_SECONDS)

    log('=' * 80)
    log(f"✅ Completed. Stories added: {total_stories}")
    log('=' * 80)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
NewsBrief Batch Processor for EBS (INSERT-only)
Replicates the 8540 cron behavior without UPDATE operations.
"""

import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import os
import re
import json
import time
from datetime import datetime, timedelta, timezone
from threading import Lock

import lancedb
import pandas as pd
from bs4 import BeautifulSoup

from id_tracker_ebs import is_digest_processed, mark_digest_processed

import sys
sys.path.insert(0, '/home/ubuntu/newspaper_project/handlers')
from newsbrief_with_links_handler import enrich_newsbrief_with_links
from tweet_keyword_handler import extract_tweet_keywords


GMAIL_USER = os.getenv('GMAIL_USER', 'prjfiles@gmail.com')
GMAIL_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', 'kwgfutaxitoesvlz')
DB_URI = '/mnt/lancedb_clean'
TABLE_NAME = 'unified_feed'
ANTHROPIC_KEY = os.getenv(
    'ANTHROPIC_API_KEY',
    ''YOUR_ANTHROPIC_API_KEY_HERE''
)

FETCH_WINDOW_DAYS = 7
MAX_DIGESTS = 20
DELAY_SECONDS = 1

ALLOWLIST = [
    'Bloomberg',
    'WSJ',
    'Reuters',
    "Barron's",
    'Estadão',
    'Folha',
    'Business Insider',
    'Financial Times',
    'Topdown Charts',
    'Globo'
]

EXCLUSIONS_PATH = '/home/ubuntu/newspaper_project/keyword_exclusions.json'
if os.path.exists(EXCLUSIONS_PATH):
    with open(EXCLUSIONS_PATH, 'r') as f:
        KEYWORD_EXCLUSIONS = json.load(f)
else:
    KEYWORD_EXCLUSIONS = []

_print_lock = Lock()


def log(message: str) -> None:
    with _print_lock:
        print(message, flush=True)


def parse_email_datetime(date_header: str) -> datetime:
    if not date_header:
        return datetime.utcnow().replace(tzinfo=timezone.utc)
    try:
        dt = parsedate_to_datetime(date_header)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return datetime.utcnow().replace(tzinfo=timezone.utc)


def format_created_at(date_header: str) -> str:
    dt = parse_email_datetime(date_header)
    iso = dt.isoformat()
    if iso.endswith('+00:00'):
        iso = iso[:-6] + 'Z'
    return iso


def decode_str(value: str) -> str:
    if not value:
        return ''
    pieces = decode_header(value)
    text = ''
    for chunk, enc in pieces:
        if isinstance(chunk, bytes):
            text += chunk.decode(enc or 'utf-8', errors='ignore')
        else:
            text += chunk
    return text


def sender_allowed(sender_name: str) -> bool:
    lower = sender_name.lower()
    return any(tag.lower() in lower for tag in ALLOWLIST)


def connect_db():
    db = lancedb.connect(DB_URI)
    return db.open_table(TABLE_NAME)


def fetch_candidates():
    log('📥 Connecting to Gmail…')
    imap = imaplib.IMAP4_SSL('imap.gmail.com')
    imap.login(GMAIL_USER, GMAIL_PASSWORD)
    imap.select('INBOX')

    since_date = (datetime.now() - timedelta(days=FETCH_WINDOW_DAYS)).strftime('%d-%b-%Y')
    status, data = imap.search(None, f'(SINCE {since_date})')
    if status != 'OK':
        log('❌ Gmail search failed')
        imap.logout()
        return []

    email_ids = data[0].split()
    log(f"   📧 {len(email_ids)} emails found in window")

    digests = []
    for eid in reversed(email_ids):
        if len(digests) >= MAX_DIGESTS:
            break

        status, msg_data = imap.fetch(eid, '(RFC822)')
        if status != 'OK':
            continue

        msg = email.message_from_bytes(msg_data[0][1])
        sender_raw = decode_str(msg.get('From', ''))
        sender_name = sender_raw.split('<')[0].strip().strip('"')
        if not sender_allowed(sender_name):
            continue

        subject = decode_str(msg.get('Subject', ''))

        body_text = ''
        body_html = ''
        if msg.is_multipart():
            for part in msg.walk():
                try:
                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue
                    text = payload.decode('utf-8', errors='ignore')
                except Exception:
                    continue

                if part.get_content_type() == 'text/plain' and not body_text:
                    body_text = text
                elif part.get_content_type() == 'text/html' and not body_html:
                    body_html = text
        else:
            payload = msg.get_payload(decode=True) or b''
            text = payload.decode('utf-8', errors='ignore')
            if msg.get_content_type() == 'text/html':
                body_html = text
            else:
                body_text = text

        combined = body_html or body_text
        if len(combined) < 4000:
            continue

        message_id = msg.get('Message-ID') or f"digest-{eid.decode()}"
        date_header = msg.get('Date')
        created_at_iso = format_created_at(date_header)

        digests.append({
            'id': message_id,
            'sender': sender_name,
            'subject': subject,
            'content_text': body_text or BeautifulSoup(body_html, 'html.parser').get_text(separator='\n'),
            'content_html': body_html,
            'created_at': created_at_iso
        })

    imap.logout()
    log(f"   ✅ {len(digests)} NewsBrief candidates")
    return digests


def parse_story_blocks(html: str):
    pattern = r'<strong[^>]*>(\d+)\.\s([^<]+)</strong>(.*?)(?=<strong|$)'
    matches = re.findall(pattern, html, re.DOTALL)
    stories = []
    for number, title, block in matches:
        block = block.strip()
        soup = BeautifulSoup(block, 'html.parser')
        text = soup.get_text(separator='\n').strip()
        link_match = re.search(r'href="([^"]+)"', block)
        link = link_match.group(1) if link_match else ''
        stories.append({
            'number': int(number),
            'title': title.strip(),
            'html': block,
            'text': text,
            'link': link
        })
    return stories


def extract_keywords(text: str):
    try:
        result = extract_tweet_keywords(text[:500], ANTHROPIC_KEY, KEYWORD_EXCLUSIONS)
        keywords = result.get('keywords') or []
        score = float(result.get('score', 8.0))
        return ' • '.join(keywords), score
    except Exception as exc:
        log(f"   ⚠️ Keyword extraction failed: {exc}")
        return '', 7.0


def build_story_records(digest, stories):
    records = []
    for story in stories:
        keywords, score = extract_keywords(story['text'])
        records.append({
            'id': f"{digest['id']}_story_{story['number']}",
            'source_type': 'email',
            'source': 'newsbrief_story',
            'created_at': digest['created_at'],
            'author': digest['sender'],
            'sender': f"{digest['sender']} - Newsbrief",
            'sender_tag': f"{digest['sender']} - Newsbrief",
            'title': f"{story['number']}. {story['title']}",
            'subject': f"{digest['subject']} - Story {story['number']}",
            'content_text': story['text'],
            'content_html': story['html'],
            'enriched_content': story['html'],
            'themes': keywords,
            'actors': '',
            'ai_score': score,
            'sentiment': '',
            'category': 'news',
            'market_impact': '',
            'link': story['link'],
            'parent_id': digest['id'],
            'story_number': story['number'],
            'is_junk': False,
            'custom_fields': json.dumps({'digest_subject': digest['subject']})
        })
    return records


def main():
    log('=' * 80)
    log('🚀 NewsBrief Batch Processor (EBS INSERT-only)')
    log('=' * 80)
    log(datetime.now().strftime('🕒 %Y-%m-%d %H:%M:%S'))

    table = connect_db()
    digests = fetch_candidates()
    if not digests:
        log('✅ No digests found')
        return

    total_stories = 0
    for digest in digests:
        if is_digest_processed(digest['id']):
            log(f"⏭️  Already processed: {digest['subject'][:60]}")
            continue

        log(f"📰 {digest['sender']} — {digest['subject'][:60]}")
        response = enrich_newsbrief_with_links(
            digest['subject'],
            digest['content_text'],
            digest['sender'],
            ANTHROPIC_KEY
        )

        summary_html = response.get('smart_summary', '')
        if not summary_html:
            log('   ❌ Handler returned empty summary')
            continue

        stories = parse_story_blocks(summary_html)
        if not stories:
            log('   ❌ No stories parsed from summary')
            continue

        story_records = build_story_records(digest, stories)
        # Check for existing stories before inserting

        existing_df = table.to_pandas()

        existing_ids = set(existing_df['id'].unique())

        

        # Filter out stories that already exist

        new_story_records = []

        for story in story_records:

            if story['id'] not in existing_ids:

                new_story_records.append(story)

        

        if new_story_records:

            table.add(pd.DataFrame(new_story_records))

            log(f"   ✅ Added {len(new_story_records)} new stories ({len(story_records) - len(new_story_records)} duplicates skipped)")

        else:

            log(f"   ℹ️ All {len(story_records)} stories already exist, skipping")

        

        # Original line (now replaced):

        # table.add(pd.DataFrame(story_records))
        mark_digest_processed(digest['id'])
        total_stories += len(story_records)
        time.sleep(DELAY_SECONDS)

    log('=' * 80)
    log(f"✅ Completed. Stories added: {total_stories}")
    log('=' * 80)


if __name__ == '__main__':
    main()

