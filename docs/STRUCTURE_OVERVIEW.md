# EBS SAGE System Structure (November 9, 2025)

This document captures how the EBS-backed SAGE deployment is wired on the AWS host. It mirrors the live instance running on ports 8543 (admin) and 8545 (NewsFlow feed).

## 1. High-Level Flow

1. **Email + Twitter ingest scripts** run on cron.
2. Scripts enrich content with Anthropic Claude, build LanceDB-ready records, and append them to the EBS volume at `/mnt/lancedb_clean/unified_feed`.
3. **Flask UI (`sage_ebs_clean.py`)** reads the LanceDB table, sanitises timestamps, applies sorting/filtering, and serves JSON to the NewsFlow interface.
4. **Admin UI (`scrapex_admin.py`)** lets operators manage allowlists, tagging rules, and handler mappings through JSON configs (no DB writes).
5. **Backups + documentation** live in this repo to keep the system portable.

```
Gmail / Twitter API --> Cron Scripts --> LanceDB (EBS) --> Flask Feed API --> NewsFlow UI
                                      \-> Admin JSON configs
```

## 2. Directory Layout

| Path | Purpose |
| --- | --- |
| `app/` | Flask apps (`sage_ebs_clean.py` for feed, `scrapex_admin.py` for admin tooling). |
| `handlers/` | Claude prompt wrappers (keyword extraction, NewsBrief summariser, etc.). |
| `scripts/` | Operational scripts (NewsBrief batch, Twitter fetch+enrich, junk classifier, ID tracker). |
| `templates/` | HTML files for the NewsFlow and admin interfaces. |
| `keyword_exclusions.json` | Optional keywords to suppress during enrichment. |
| `backups/` | Timestamped tarballs of this repo snapshot. |

The Python modules here align 1:1 with `/home/ubuntu/newspaper_project` on the server. ENV paths are resolved at runtime, so the repo can be cloned anywhere and pointed at a different LanceDB location.

## 3. Ingestion Pipelines

### 3.1 NewsBrief (`scripts/newsbrief_batch_ebs.py`)
- Connects to Gmail via IMAP (`GMAIL_USER`, `GMAIL_APP_PASSWORD`).
- Filters messages by sender using the `ALLOWLIST` array (Bloomberg, WSJ, Folha, etc.).
- Parses RFC-2822 date headers with timezone awareness; stores UTC ISO strings.
- Sends the email body to `enrich_newsbrief_with_links` (Claude) to split into numbered stories with links.
- Extracts keywords/score per story via `extract_tweet_keywords`.
- Writes each story as an insert-only record with parent digest metadata.
- Uses `/home/ubuntu/newspaper_project/processed_ids_ebs.json` to avoid reprocessing.
- Respects a 2-second sleep between digests to honour API pacing.

### 3.2 Twitter (`scripts/twitter_fetch_to_ebs_tracker.py`)
- Pulls list tweets via TwitterAPI.io (`TWITTERAPI_KEY`, `TWITTER_LIST_ID`).
- Enriches text through Claude for keywords (`themes`), language, and AI score.
- Flags `is_junk` when `ai_score <= 3` at insert time.
- Tracks processed tweet IDs to maintain insert-only semantics.
- Shares schema expectations with NewsBrief so both land in the same table.

### 3.3 Junk Classifier (`scripts/tweet_junk_classifier_ebs.py`)
- Optional clean-up script that sweeps for low-scoring tweets and marks `is_junk` respecting the 2-second update rule. (Kept for parity with prod; safe to disable if pure insert-only is desired.)

## 4. Storage

- **Database**: LanceDB on the attached EBS volume, mounted at `/mnt/lancedb_clean`.
- **Table**: `unified_feed` (identical schema to production port 8540).
- **Schema Notes**:
  - Primary ID pattern: `digest-id_story_n` for emails, `tweet_<id>` for tweets.
  - Columns: `created_at`, `sender`, `sender_tag`, `title`, `content_text`, `content_html`, `themes`, `ai_score`, `is_junk`, etc.
  - Insert-only expectation: scripts pre-check for duplicates before writing.

## 5. Front-End & Admin

- `app/sage_ebs_clean.py`: Flask feed service. Key behaviours:
  - Applies `_sanitize_datetime` to harmonise naive vs aware datetimes.
  - Converts `created_at` column via `apply(pd.to_datetime(..., utc=True))` before sorting.
  - Serves `/api/feed` to the NewsFlow UI (white theme template).
- `app/scrapex_admin.py`: Admin service (port 8543).
  - Endpoints for managing `allowed_senders.json`, `tag_detection_rules.json`, and `tag_handler_mappings.json`.
  - Provides `/api/tagging_rules` alias for UI compatibility.
  - Template `templates/admin_complete.html` includes dropdown-driven mapping creation.

## 6. Cron Jobs (reference)

```
# /etc/cron.d/sage_ebs
*/15 * * * * cd /home/ubuntu/newspaper_project && /usr/bin/env /home/ubuntu/newspaper_project/cron_wrapper.sh python3 twitter_fetch_to_ebs_tracker.py >> /home/ubuntu/logs/ebs_clean/twitter_fetch.log 2>&1
*/20 * * * * cd /home/ubuntu/newspaper_project && /usr/bin/env /home/ubuntu/newspaper_project/cron_wrapper.sh python3 newsbrief_batch_ebs.py >> /home/ubuntu/logs/ebs_clean/newsbrief_batch.log 2>&1
0 * * * * cd /home/ubuntu/newspaper_project && /usr/bin/env /home/ubuntu/newspaper_project/cron_wrapper.sh python3 tweet_junk_classifier_ebs.py >> /home/ubuntu/logs/ebs_clean/tweet_junk.log 2>&1
```

`cron_wrapper.sh` exports `ANTHROPIC_API_KEY` (and other secrets) before launching Python, keeping the scripts secret-free.

## 7. Backups & Restore Notes

- Fresh repo snapshot: `backups/EBS_SAGE_backup_20251109_133106Z.tar.gz`.
- For full LanceDB resilience, also rsync `/mnt/lancedb_clean` separately (not stored in git).
- Restore steps:
  1. Extract tarball to target host.
  2. Install `requirements.txt` in a virtualenv.
  3. Set ENV variables pointing to the LanceDB data directory and secrets.
  4. Launch Flask apps (ports 8543/8545) or run individual scripts as needed.

## 8. Related Documentation

- `TECHNICAL_SPECS_EXTRACTION.md`: Extraction & enrichment deep dive (saved previously for RAG planning).
- `README.md`: Quickstart + environment variable matrix.
- `backups/`: Historical repo snapshots for point-in-time recovery.

---
Generated November 9, 2025 to reflect the current production-ready EBS deployment.
