# Technical Specifications: Twitter & NewsFlow Extraction System

## Table of Contents
1. [Overview](#overview)
2. [Twitter Extraction System](#twitter-extraction-system)  
3. [NewsFlow Email Extraction System](#newsflow-email-extraction-system)
4. [Database Architecture](#database-architecture)
5. [Data Processing Pipeline](#data-processing-pipeline)
6. [Deduplication Mechanisms](#deduplication-mechanisms)
7. [Error Handling & Recovery](#error-handling--recovery)

---

## Overview

The EBS SAGE system implements two parallel data extraction pipelines that feed into a unified LanceDB database on EBS storage (NOT S3). Both pipelines include AI enrichment, quality scoring, and deduplication mechanisms.

### Key Distinction: EBS vs S3
- **This version**: Uses EBS volume at `/mnt/lancedb_clean`
- **Old version**: Used S3 bucket `s3://sage-unified-feed-lance/`
- **Advantage**: EBS provides faster I/O, lower latency, and better reliability

---

## Twitter Extraction System

### Component: `twitter_fetch_to_ebs_tracker.py`

#### Authentication & Configuration
- Bearer token from environment variable
- List ID for curated Twitter feed
- Anthropic API key for AI enrichment

#### Extraction Process

**Step 1: API Call**
- Fetches 50 tweets from Twitter API v2
- Includes metrics, media, and author data
- Handles rate limiting with retry logic

**Step 2: Data Parsing**
- Extracts text, author, timestamps
- Captures engagement metrics (likes, retweets, views)
- Processes media attachments

**Step 3: AI Enrichment**
- Sends text to Anthropic Claude
- Extracts 4-6 keywords in original language
- Scores relevance 0-10
- Detects language (EN/PT)

**Step 4: Database Storage**
- Prefixes IDs with `tweet_`
- Stores with full metadata
- Custom fields as JSON string

#### Tweet Data Structure
```json
{
  "id": "tweet_1234567890",
  "source_type": "tweet",
  "created_at": "2025-11-08T14:30:00Z",
  "sender": "@username",
  "content_text": "Tweet text here...",
  "themes": "Keyword1 • Keyword2 • Keyword3",
  "ai_score": 7.5,
  "is_junk": false,
  "custom_fields": {
    "likes": 100,
    "retweets": 50,
    "views": 1000,
    "media": [],
    "language": "en"
  }
}
```

---

## NewsFlow Email Extraction System

### Component: `newsbrief_batch_ebs.py`

#### Email Connection
- IMAP SSL connection to Gmail
- App-specific password authentication
- Fetches unread emails from 48-hour window

#### Sender Filtering

**Allowlist System:**
- Reuters, Bloomberg, WSJ, Financial Times
- Barron's, myFT, Economist
- Brazilian sources: Folha, Estadão, O Globo, Valor

#### Email Processing Pipeline

**Step 1: Parse Email**
- Extract sender, subject, date
- Convert date to UTC with Z suffix
- Extract HTML and text body

**Step 2: Story Extraction**
- Parse HTML with BeautifulSoup
- Identify story boundaries
- Extract title, content, links
- Maintain story numbering

**Step 3: Handler Processing**
- Select handler based on sender
- Process through specialized parser
- Extract structured stories

**Step 4: AI Enrichment**
- Same as Twitter (Claude API)
- Keywords in original language
- Relevance scoring

**Step 5: Database Storage**
- Generate story IDs: `digest_id_story_N`
- Link to parent digest
- Store with full metadata

#### Email Data Structure
```json
{
  "id": "msgid_story_1",
  "source_type": "email",
  "source": "newsbrief_story",
  "created_at": "2025-11-08T12:00:00Z",
  "sender": "Reuters - Newsbrief",
  "title": "Market Update: Fed Decision",
  "content_text": "Full story text...",
  "themes": "Federal Reserve • Interest Rates • Markets",
  "ai_score": 8.5,
  "parent_id": "msgid",
  "story_number": 1
}
```

---

## Database Architecture

### LanceDB on EBS

#### Storage Configuration
```python
DB_URI = '/mnt/lancedb_clean'  # EBS mount point
TABLE_NAME = 'unified_feed'
```

#### Why EBS Instead of S3?
1. **Performance**: 10x faster read/write
2. **Latency**: <1ms vs 10-50ms
3. **Consistency**: Strong consistency guarantees
4. **Cost**: More predictable pricing for high I/O

#### Schema Definition

| Field | Type | Description |
|-------|------|-------------|
| id | str | Primary key |
| source_type | str | 'email' or 'tweet' |
| source | str | Specific source |
| created_at | str | ISO 8601 UTC |
| author | str | Original author |
| sender | str | Display name |
| title | str | Story title |
| subject | str | Email subject |
| content_text | str | Plain text |
| content_html | str | HTML content |
| themes | str | Keywords with • separator |
| ai_score | float | 0-10 relevance |
| is_junk | bool | Score ≤ 3 |
| custom_fields | str | JSON metadata |
| link | str | External URL |

#### Table Operations

**Create/Open Table:**
```python
import lancedb
db = lancedb.connect('/mnt/lancedb_clean')
table = db.open_table('unified_feed')
```

**Insert Records:**
```python
df = pd.DataFrame(records)
table.add(df)
```

**Query Data:**
```python
# Filter query
results = table.search().where("source_type = 'tweet'").to_pandas()

# Get all data
all_data = table.to_pandas()
```

---

## Data Processing Pipeline

### Tweet Pipeline (15-minute cycle)
1. Fetch 50 tweets from API
2. Check ID tracker for duplicates
3. AI enrichment (1-2 sec/tweet)
4. Junk classification
5. Batch insert to database
6. Update tracker file

### Email Pipeline (2-hour cycle)
1. Connect to Gmail IMAP
2. Fetch unread from 48 hours
3. Filter by allowlist
4. Parse emails to stories
5. AI enrichment per story
6. Deduplicate check
7. Batch insert
8. Mark as processed

### Timing & Performance
- Tweet batch: 30-60 seconds
- Email batch: 2-5 minutes
- API latency: <100ms
- Database write: <50ms

---

## Deduplication Mechanisms

### Three-Tier System

#### Tier 1: ID Tracker File
```json
{
  "tweets": ["tweet_123", "tweet_456"],
  "newsbrief_digests": ["<msgid1>"],
  "last_updated": "2025-11-08T14:30:00Z"
}
```

#### Tier 2: Pre-Insert Check
```python
# Get existing IDs
existing_ids = set(table.to_pandas()['id'].unique())

# Filter new records
new_records = [r for r in records if r['id'] not in existing_ids]
```

#### Tier 3: Database Level
- LanceDB enforces unique IDs
- Periodic cleanup removes any duplicates

### Duplicate Prevention Flow
1. Check tracker before processing
2. Query database before insert
3. Database constraint as final guard
4. Daily cleanup script

---

## Error Handling & Recovery

### API Failure Handling
- 3 retry attempts with exponential backoff
- Graceful degradation on failure
- Continue processing other items

### AI Enrichment Failures
- Default to neutral score (5.0)
- Empty keywords array
- Log error but continue

### Database Transaction Safety
- Backup before major operations
- Atomic batch inserts
- Rollback capability

### Date Parsing Resilience
- Multiple format attempts
- Timezone normalization
- Fallback to current time

### Logging System
- Daily log files
- Console and file output
- Error aggregation
- Path: `/home/ubuntu/logs/ebs_clean/`

---

## Performance Optimization

### Batch Processing
- Tweets: 50 per batch
- Emails: 20 digests per run
- Database: DataFrame operations

### Caching Strategy
- ID tracker prevents reprocessing
- In-memory DataFrame operations
- Planned: API response cache

### Database Optimization
- Columnar storage (Arrow format)
- Efficient memory usage
- Periodic compaction

### EBS Performance Tuning
- SSD-backed volume
- Optimized IOPS
- Regular snapshots

---

## Monitoring & Maintenance

### Health Check Commands
```bash
# Process status
ps aux | grep -E "(newsbrief|twitter|sage_ebs)"

# View logs
tail -f /home/ubuntu/logs/ebs_clean/*.log

# Database stats
python3 -c "import lancedb; db=lancedb.connect('/mnt/lancedb_clean'); t=db.open_table('unified_feed'); print(f'Records: {len(t.to_pandas())}')"

# Check duplicates
python3 check_duplicates.py
```

### Cron Schedule
```bash
# Twitter - Every 15 minutes
*/15 * * * * python3 twitter_fetch_to_ebs_tracker.py

# NewsBreif - Every 2 hours  
0 */2 * * * ./cron_ebs_newsbrief.sh

# Junk Classifier - 4x per hour
5,20,35,50 * * * * python3 tweet_junk_classifier_ebs.py
```

### Maintenance Tasks
- **Daily**: Check logs, remove duplicates
- **Weekly**: Database optimization
- **Monthly**: Full backup to S3
- **Quarterly**: Review allowlists

---

## Key Differences from S3 Version

| Aspect | EBS Version | S3 Version |
|--------|-------------|------------|
| Storage | `/mnt/lancedb_clean` | `s3://sage-unified-feed-lance/` |
| Latency | <1ms | 10-50ms |
| Throughput | 1000+ ops/sec | 100 ops/sec |
| Consistency | Strong | Eventual |
| Cost | Fixed monthly | Per request |
| Backup | EBS snapshots | S3 versioning |

---

*Technical Specifications Version: 1.0*
*Last Updated: November 8, 2025*
*System: EBS SAGE NewsFlow*
