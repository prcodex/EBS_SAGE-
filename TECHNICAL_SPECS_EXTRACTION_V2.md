# Technical Specifications V2: Complete System Architecture

## System Evolution

### Phase 1: Original SAGE (Port 8540)
- S3-based storage
- 8-step processing pipeline
- 26 specialized handlers
- White Twitter interface

### Phase 2: EBS Migration (November 2025)
- Moved to /mnt/lancedb_clean
- Insert-only architecture
- Split batch processing

### Phase 3: Current Architecture
**Three Independent Batch Systems:**

## Batch 1: NewsBreif Ingestion

### Schedule: Every 2 hours
### File: `newsbrief_batch_ebs.py`

**Process Flow:**
1. Connect to Gmail IMAP
2. Fetch unread emails (48-hour window)
3. Filter by allowlist (7 publishers)
4. Parse email structure
5. Extract individual stories
6. AI enrichment (keywords + score)
7. Insert to LanceDB
8. Update tracker

**Key Features:**
- Portuguese content preserved
- Story-level extraction
- Link preservation
- Duplicate prevention

## Batch 2: Twitter Ingestion

### Schedule: Every 15 minutes
### File: `twitter_fetch_to_ebs_tracker.py`

**Process Flow:**
1. Call Twitter API v2
2. Fetch 50 tweets from list
3. Extract text and metadata
4. AI enrichment
5. Auto-junk classification
6. Insert to LanceDB
7. Update tracker

**Key Features:**
- Real-time scoring
- Engagement metrics
- Media extraction
- Language detection

## Batch 3: Deep Analysis (Proposed)

### Schedule: Every 4-6 hours
### File: `analysis_batch_processor.py`

**8-Step Analysis Pipeline:**
1. **READ** - Query unified_feed (read-only)
2. **DETECT** - Apply tag_detection_rules
3. **TAG** - Assign appropriate tags
4. **ROUTE** - Select handler via mappings
5. **ENRICH** - Execute specialized handler
6. **EXTRACT** - Deep actors/themes analysis
7. **SYNTHESIZE** - Create comprehensive output
8. **STORE** - Save to analysis_results

**Available Handlers (26 total):**
- `aaa_universal_handler` - Fallback with source detection
- `gold_standard_enhanced` - Deep thematic analysis (6-10 bullets)
- `rosenberg_deep_research` - Detailed 5-7 analytical bullets
- `newsbrief_with_links` - Story extraction with links
- `itau_daily` - Portuguese summaries
- `cochrane_detailed` - Academic economics
- `shadow_handler` - Chart analysis with VLM
- `bloomberg_breaking` - Title-only extraction
- `breakfast_with_dave` - Market commentary
- `drive_research` - Research reports
- `elerian_rep` - Economic analysis
- `gsrates` - Goldman Sachs rates
- `javier_blas` - Commodities analysis
- `joe_handler` - Market updates
- `macrocharts` - Visual analysis
- Plus 11 more specialized handlers

## Database Architecture

### Primary Storage: EBS
```
/mnt/lancedb_clean/
├── unified_feed/      # Raw ingestion data
└── analysis_results/  # Deep analysis (proposed)
```

### Schema: unified_feed
- `id`: Primary key
- `source_type`: 'email' or 'tweet'
- `created_at`: UTC with Z suffix
- `sender`: Display name
- `content_text`: Plain text
- `themes`: Keywords (• separated)
- `ai_score`: 0-10 relevance
- `is_junk`: Boolean (tracked externally)

### Performance Metrics
- Latency: <1ms (vs 10-50ms on S3)
- Throughput: 1000+ ops/sec
- Storage: 100GB EBS volume
- Records: ~10,000 as of Nov 9

## API Endpoints

### Port 8545: Main Feed
- `GET /` - Web interface
- `GET /api/feed` - JSON data
- `POST /api/mark_junk/<id>` - Mark as junk
- `POST /api/unmark_junk/<id>` - Restore item

### Port 8543: Admin Interface
- `GET /` - Admin dashboard
- `GET /api/tag_handler_mappings` - Get mappings
- `POST /api/tag_handler_mappings` - Add/delete mappings
- `GET /api/tagging_rules` - Get detection rules

### Port 8546: Analysis Explorer (Proposed)
- `GET /` - Analysis interface
- `GET /api/analysis/<id>` - Get item analysis
- `GET /api/analysis/recent` - Recent analyses
- `GET /api/pipeline/<id>` - Show 8-step journey

## Key Innovations

### Insert-Only Architecture
- No UPDATE operations
- All enrichment pre-insertion
- External junk tracking
- Data integrity preserved

### Junk Persistence
- File: `junked_ids.json`
- Thread-safe operations
- Survives restarts
- No database updates

### Handler System
- 26 specialized handlers
- Tag-based routing
- Configurable mappings
- Deep analysis capability

## Deployment

### Cron Schedule
```bash
# NewsBreif - Every 2 hours
0 */2 * * * /home/ubuntu/newspaper_project/cron_ebs_newsbrief.sh

# Twitter - Every 15 minutes
*/15 * * * * /home/ubuntu/newspaper_project/cron_wrapper.sh python3 twitter_fetch_to_ebs_tracker.py

# Analysis - Every 4 hours (proposed)
0 */4 * * * python3 analysis_batch_processor.py
```

### Environment Variables
```bash
export ANTHROPIC_API_KEY="your_key_here"
export GMAIL_USER="your_email"
export GMAIL_APP_PASSWORD="your_app_password"
export TWITTER_BEARER_TOKEN="your_token"
```

## Future Roadmap

### Q4 2025
- Implement analysis batch
- Create analysis interface
- Deploy to port 8546

### Q1 2026
- RAG system integration
- Vector embeddings
- Semantic search

### Q2 2026
- Real-time streaming
- WebSocket updates
- Predictive analytics

---

*Version: 2.0*
*Updated: November 9, 2025*
*System: EBS SAGE with Analysis Pipeline*
