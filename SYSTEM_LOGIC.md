# EBS SAGE System Logic & Architecture

## Core Processing Logic

### 1. Email Processing Logic (NewsBreif)

The system processes newsletter emails through a multi-stage pipeline:

**Stage 1: Email Fetching**
- Connect to Gmail via IMAP
- Search for unread emails from last 48 hours
- Filter by sender allowlist (Reuters, Bloomberg, WSJ, etc.)

**Stage 2: Content Parsing**
- Extract HTML and text content
- Parse story structure using BeautifulSoup
- Identify individual news items within digests

**Stage 3: Story Extraction**
- Split digest into individual stories
- Extract title, content, and links
- Maintain story numbering and hierarchy

**Stage 4: AI Enrichment**
- Send content to Anthropic Claude API
- Extract 4-6 keywords in original language
- Calculate relevance score (0-10)
- Detect content language (EN/PT)

**Stage 5: Data Storage**
- Generate unique story IDs
- Check for duplicates before insertion
- Store in LanceDB with full metadata
- Update processed IDs tracker

### 2. Twitter Processing Logic

**Stage 1: API Fetching**
- Call Twitter API v2 for list tweets
- Fetch last 50 tweets from configured list
- Parse tweet JSON structure

**Stage 2: Content Extraction**
- Extract text, author, metrics
- Parse media attachments
- Extract URLs and mentions

**Stage 3: AI Analysis**
- Same enrichment as emails
- Additional junk classification
- Real-time scoring

**Stage 4: Storage**
- Prefix IDs with 'tweet_'
- Store with engagement metrics
- Track in processed_ids

### 3. Deduplication Logic

The system uses three-tier deduplication:

**Tier 1: ID Tracking**
- JSON file tracks all processed IDs
- Check before processing new items
- Prevents reprocessing

**Tier 2: Pre-Insert Check**
- Query database for existing IDs
- Filter out duplicates from batch
- Only insert new records

**Tier 3: Database Constraints**
- Unique ID enforcement
- Periodic cleanup scripts
- Integrity verification

### 4. Date/Time Logic

**UTC Standardization**
- All dates stored in UTC
- 'Z' suffix for clarity
- Microseconds preserved

**Timezone Handling**
- Parse email headers with timezone
- Convert to UTC before storage
- Display in Brazil time (UTC-3)

**Pandas Processing**
- Individual date parsing (not batch)
- Handles mixed formats gracefully
- Fallback for invalid dates

### 5. AI Scoring Logic

**Score Calculation**
- 0-3: Low relevance/junk
- 4-6: Moderate relevance
- 7-10: High relevance

**Factors Considered**
- Financial keywords presence
- Market impact potential
- Source credibility
- Content coherence

**Junk Classification**
- Score ≤ 3 marked as junk
- Separate view in interface
- Periodic cleanup option

### 6. Language Detection Logic

**Bilingual Support**
- Detect Portuguese vs English
- Preserve original language
- No automatic translation

**Keyword Extraction**
- Language-specific processing
- Cultural context awareness
- Proper noun handling

### 7. Flask API Logic

**Request Processing**
1. Connect to LanceDB
2. Load full dataset
3. Apply filters (source, junk status)
4. Parse dates individually
5. Sort by timestamp
6. Format response JSON

**Performance Optimization**
- In-memory operations
- Lazy loading
- Response caching

### 8. Cron Job Logic

**NewsBreif (Every 2 hours)**
- Check for new emails
- Process in batches of 20
- Log results

**Twitter (Every 15 minutes)**
- Fetch recent tweets
- Quick enrichment
- Real-time updates

**Junk Classifier (4x per hour)**
- Review recent entries
- Update junk status
- Maintain quality

## Data Structures

### Record Structure
Each record contains:
- Unique identifier
- Source information
- Temporal data
- Content (text/HTML)
- AI enrichment
- Custom metadata

### Tracker Structure
Processed IDs organized by:
- Tweet IDs
- NewsBreif digest IDs
- Story IDs
- Last update timestamp

### Configuration Structure
System settings for:
- API endpoints
- Credentials
- Thresholds
- Schedules

## Error Handling Logic

### Graceful Degradation
- API failures don't stop processing
- Missing enrichment gets default values
- Partial success is acceptable

### Retry Logic
- 3 attempts for API calls
- Exponential backoff
- Dead letter queue for failures

### Logging Strategy
- Separate logs per component
- Daily rotation
- Error aggregation

## Performance Characteristics

### Throughput
- 10-20 emails per minute
- 50 tweets per batch
- 1000+ records without degradation

### Latency
- API response: <100ms
- Enrichment: 1-2 seconds
- Full pipeline: <5 seconds

### Resource Usage
- Memory: ~200MB steady state
- CPU: <5% average
- Storage: ~1MB per 500 records

## Security Model

### Authentication
- Gmail app passwords
- API bearer tokens
- Environment variables

### Authorization
- Read-only email access
- Limited API scopes
- Sanitized outputs

### Data Protection
- No PII storage
- Encrypted connections
- Secure key management

## Scalability Considerations

### Horizontal Scaling
- Stateless processing
- Distributed cron jobs
- Load balancing ready

### Vertical Scaling
- Batch size adjustment
- Concurrent processing
- Memory optimization

### Data Scaling
- Partitioning strategy
- Archive old data
- Index optimization

---
*This document describes the core logic and architecture of the EBS SAGE system*
