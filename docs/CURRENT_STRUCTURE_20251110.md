# EBS SAGE System Structure - November 10, 2025

## Active Services and Ports

| Port | Service | Description | Status |
|------|---------|-------------|--------|
| 8543 | Admin Interface | Configuration management | ✅ Active |
| 8545 | Main Feed Interface | NewsFlow + Tweets display | ✅ Active |
| 8546 | Analysis Interface | Deep AI analysis results | ✅ Active |

## Batch Processes

### 1. NewsBreif/NewsFlow Batch
- **Script**: `scripts/newsbrief_batch_ebs.py`
- **Schedule**: Every 30 minutes
- **Cron**: `*/30 * * * * /home/ubuntu/newspaper_project/cron_ebs_newsbrief.sh`
- **Function**: Fetches emails, parses stories, enriches with AI

### 2. Twitter Batch
- **Script**: `scripts/twitter_fetch_to_ebs_tracker.py`
- **Schedule**: Every 15 minutes
- **Cron**: `*/15 * * * * cd /home/ubuntu/newspaper_project && /usr/bin/env /home/ubuntu/newspaper_project/cron_wrapper.sh python3 twitter_fetch_to_ebs_tracker.py`
- **Function**: Fetches tweets, enriches with keywords, scores relevance

### 3. Analysis Batch
- **Script**: `analysis_batch_processor.py`
- **Schedule**: Every 2 hours (recommended)
- **Function**: Deep AI analysis using tag-handler mappings
- **Storage**: Separate `analysis_results` table

## Database Structure

### LanceDB Tables
- **Location**: `/mnt/lancedb_clean`
- **Main Table**: `unified_feed`
- **Analysis Table**: `analysis_results`
- **Format**: Apache Arrow columnar storage

### Schema Fields
- Core: `id`, `created_at`, `source_type`, `sender`, `title`
- Content: `content_text`, `content_html`, `link`
- AI: `themes`, `actors`, `ai_score`, `language`
- Status: `is_junk`, `is_analyzed`

## Handler System

### Available Handlers (26 total)
Located in `/home/ubuntu/newspaper_project/handlers/`:

**Universal/General:**
- `aaa_universal_handler.py`
- `debug_handler.py`

**Publisher-Specific:**
- `bloomberg_breaking_news_handler.py`
- `reuters_handler.py`
- `wsj_teaser_handler.py`
- `ft_handler.py`
- `economist_handler.py`
- `barrons_handler.py`
- `folha_handler.py`
- `estadao_handler.py`
- `globo_handler.py`

**Specialized Analysis:**
- `gold_standard_enhanced_handler.py`
- `breakfast_with_dave_handler.py`
- `newsbrief_with_links_handler.py`
- `cochrane_detailed_summary_handler.py`
- `drive_research_handler.py`
- `elerian_rep_handler.py`
- `gsrates_handler.py`
- `itau_daily_handler.py`
- `javier_blas_handler.py`
- `joe_handler.py`
- `macrocharts_handler.py`
- `tony_handler.py`
- `tony_pasquariello_handler.py`
- `ubs_research_handler.py`
- `video_handler.py`
- `tweet_keyword_handler.py`

## Configuration Files

### Core Configuration
- `allowed_senders.json` - Master list of email senders
- `tag_detection_rules.json` - Content classification rules
- `tag_handler_mappings.json` - Tag to handler routing
- `newsflow_allowlist.json` - NewsFlow batch filter

### Tracking Files
- `processed_ids_ebs.json` - Deduplication tracker
- `analyzed_ids.json` - Analysis batch tracker

## Recent Changes (November 10, 2025)

### Admin Interface Fixes
1. Fixed JavaScript errors preventing interface loading
2. Added missing save endpoint for detection rules
3. Implemented dynamic handler list loading
4. Fixed delete functionality for rules and mappings

### System Enhancements
1. NewsFlow batch now uses dual-list system:
   - `newsflow_allowlist.json` for sender selection
   - `allowed_senders.json` for email patterns
2. Analysis batch with 8-step processing pipeline
3. Improved junk classification logic

## Workflow

### Email Processing Flow
1. Gmail IMAP → Fetch emails
2. Check against `allowed_senders.json`
3. Filter by `newsflow_allowlist.json` (for NewsBrief batch)
4. Parse stories from digest
5. Apply `tag_detection_rules.json`
6. Route to handler via `tag_handler_mappings.json`
7. AI enrichment (keywords, scores)
8. Store in LanceDB `unified_feed`

### Twitter Processing Flow
1. TwitterAPI.io → Fetch tweets
2. Extract text and metadata
3. AI keyword extraction
4. Score relevance (0-10)
5. Mark junk if score ≤ 3
6. Store in LanceDB `unified_feed`

### Analysis Processing Flow
1. Read from `unified_feed` (last 24-48 hours)
2. Filter for items matching tagging rules
3. Select handler based on tag-handler mapping
4. Perform deep 8-step analysis
5. Store results in `analysis_results`
6. Display on port 8546

## Maintenance Commands

### Service Management
```bash
# Check all services
netstat -tlnp | grep -E '(8543|8545|8546)'

# Restart admin interface
sudo pkill -f scrapex_admin && nohup python3 scrapex_admin.py &

# Restart main feed
sudo pkill -f sage_ebs_clean && nohup python3 app/sage_ebs_clean.py &

# Restart analysis interface
sudo pkill -f sage_analysis_interface && nohup python3 sage_analysis_interface.py &
```

### Manual Batch Runs
```bash
# Run NewsBreif batch
cd /home/ubuntu/newspaper_project && python3 scripts/newsbrief_batch_ebs.py

# Run Twitter batch
cd /home/ubuntu/newspaper_project && python3 scripts/twitter_fetch_to_ebs_tracker.py

# Run Analysis batch
cd /home/ubuntu/newspaper_project && python3 analysis_batch_processor.py
```

### Check Logs
```bash
# NewsBreif logs
tail -f /home/ubuntu/logs/ebs_clean/newsbrief_batch.log

# Twitter logs
tail -f /home/ubuntu/logs/ebs_clean/twitter_fetch.log

# Admin interface logs
tail -f /home/ubuntu/newspaper_project/admin.log
```

---
*System snapshot as of November 10, 2025 13:55 UTC*
