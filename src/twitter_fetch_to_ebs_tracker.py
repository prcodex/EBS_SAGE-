#!/usr/bin/env python3
"""Twitter list fetcher for the EBS LanceDB instance (insert-only).
Fetches, enriches, and classifies tweets BEFORE inserting them so that
keywords, AI scores, and junk status are populated without updates.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import lancedb
import pandas as pd
import requests

HANDLERS_DIR = "/home/ubuntu/newspaper_project/handlers"
if HANDLERS_DIR not in sys.path:
    sys.path.insert(0, HANDLERS_DIR)

from tweet_keyword_handler import extract_tweet_keywords  # noqa: E402

print("🐦 EBS Twitter Fetcher (media aware, enriched insert-only)")
print("=" * 80)

TWITTERAPI_KEY = os.getenv("TWITTERAPI_KEY") or "new1_a811096ecd294661a8a0db8e8319e0ef"
LIST_ID = os.getenv("TWITTER_LIST_ID", "1955968749036572718")
FETCH_COUNT = int(os.getenv("TWITTER_FETCH_COUNT", "30"))
EBS_DB = os.getenv("EBS_LANCEDB_PATH", "/mnt/lancedb_clean")
EBS_TABLE = os.getenv("EBS_LANCEDB_TABLE", "unified_feed")
TRACKER_FILE = os.getenv("EBS_TRACKER_FILE", "/home/ubuntu/newspaper_project/processed_ids_ebs.json")
EXCLUSIONS_PATH = os.getenv("KEYWORD_EXCLUSIONS_PATH", "/home/ubuntu/newspaper_project/keyword_exclusions.json")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY environment variable is required for tweet enrichment")

if not os.path.exists(EXCLUSIONS_PATH):
    raise FileNotFoundError(f"Keyword exclusions file not found: {EXCLUSIONS_PATH}")

with open(EXCLUSIONS_PATH, "r", encoding="utf-8") as f:
    keyword_exclusions = json.load(f)

tracker_path = Path(TRACKER_FILE)
if tracker_path.exists():
    processed_ids = set(json.loads(tracker_path.read_text()).get("tweets", []))
else:
    processed_ids = set()
print(f"Tracker entries: {len(processed_ids)}")

print(f"Connecting to LanceDB table {EBS_TABLE} at {EBS_DB}...")
db = lancedb.connect(EBS_DB)
table = db.open_table(EBS_TABLE)

existing_df = table.search().where("source_type = \"tweet\"").limit(5000).to_pandas()
existing_ids = set(existing_df["id"].tolist()) if not existing_df.empty else set()
print(f"Existing tweets already stored: {len(existing_ids)}\n")

print(f"Fetching {FETCH_COUNT} tweets from TwitterAPI.io list {LIST_ID}\n")
url = "https://api.twitterapi.io/twitter/list/tweets"
headers = {"x-api-key": TWITTERAPI_KEY}
params = {"listId": LIST_ID, "count": FETCH_COUNT}

response = requests.get(url, headers=headers, params=params, timeout=30)
if response.status_code != 200:
    print(f"Twitter API error: {response.status_code}")
    print(response.text)
    raise SystemExit(1)

data = response.json()
tweets = data.get("tweets", [])
print(f"Retrieved {len(tweets)} tweets\n")

new_rows = []
media_tweets = 0
enriched = 0

for tweet in tweets:
    tweet_id = f"tweet_{tweet.get('id')}"
    if tweet_id in processed_ids or tweet_id in existing_ids:
        continue

    author = tweet.get("author", {})
    username = author.get("userName", "unknown")
    display_name = author.get("name", username)
    text = tweet.get("text", "") or ""

    entities = tweet.get("entities", {}) or {}
    urls = entities.get("urls", [])
    first_url = (urls[0].get("expanded_url") or urls[0].get("url")) if urls else ""

    created_raw = tweet.get("createdAt", tweet.get("created_at", ""))
    created_iso = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    if created_raw:
        try:
            dt = datetime.strptime(created_raw, "%a %b %d %H:%M:%S %z %Y")
            created_iso = dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except ValueError:
            try:
                dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                created_iso = dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            except ValueError:
                pass

    media_list = []
    extended_entities = tweet.get("extendedEntities", {})
    media_items = extended_entities.get("media") if isinstance(extended_entities, dict) else None
    if not media_items:
        media_items = tweet.get("media")
    if media_items:
        for item in media_items:
            media_type = item.get("type", "photo")
            if media_type == "photo":
                link = item.get("media_url_https")
                if link:
                    media_list.append({"type": "photo", "url": link})
            elif media_type in ("video", "animated_gif"):
                best = None
                max_bitrate = 0
                for variant in item.get("video_info", {}).get("variants", []):
                    if variant.get("content_type") == "video/mp4":
                        bitrate = variant.get("bitrate", 0)
                        if bitrate > max_bitrate:
                            max_bitrate = bitrate
                            best = variant
                if best:
                    media_list.append(
                        {
                            "type": media_type,
                            "url": best.get("url"),
                            "thumbnail": item.get("media_url_https", ""),
                        }
                    )
    has_media = bool(media_list)
    if has_media:
        media_tweets += 1

    enrichment = extract_tweet_keywords(text, ANTHROPIC_KEY, keyword_exclusions)
    keywords = enrichment.get("keywords") or []
    keywords_str = " • ".join(keywords)
    ai_score = float(enrichment.get("score", 0) or 0.0)
    language = enrichment.get("language", "en")
    enriched += 1

    if not keywords and ai_score <= 0:
        is_junk = False
    else:
        is_junk = ai_score <= 3

    custom_fields = {
        "display_name": display_name,
        "likes": tweet.get("likeCount", 0),
        "retweets": tweet.get("retweetCount", 0),
        "replies": tweet.get("replyCount", 0),
        "views": tweet.get("viewCount", 0),
        "has_media": has_media,
        "media": media_list,
        "language": language,
        "keywords": keywords,
        "ai_score": ai_score,
    }

    new_rows.append(
        {
            "id": tweet_id,
            "source_type": "tweet",
            "source": "twitter_api",
            "created_at": created_iso,
            "author": display_name,
            "sender": f"@{username}",
            "title": text[:100] + ("..." if len(text) > 100 else ""),
            "subject": text[:120],
            "content_text": text,
            "content_html": "",
            "tags": "",
            "themes": keywords_str,
            "actors": keywords_str,
            "ai_score": ai_score,
            "sentiment": None,
            "category": "tweet",
            "market_impact": None,
            "parent_id": "",
            "story_number": 0,
            "is_junk": is_junk,
            "custom_fields": json.dumps(custom_fields),
            "sender_tag": f"@{username}",
            "enriched_content": text,
            "link": first_url,
        }
    )

    time.sleep(1)

if new_rows:
    print(f"Saving {len(new_rows)} tweets ({media_tweets} with media, enriched={enriched})")
    df = pd.DataFrame(new_rows)
    table.add(df)
    processed_ids.update(row["id"] for row in new_rows)
    tracker_path.write_text(json.dumps({"tweets": sorted(list(processed_ids))}, indent=2))
    print("Tweets saved to LanceDB\n")
else:
    print("No new tweets to save (all already processed)\n")

print("=" * 80)
print("🎉 EBS twitter fetch complete")
print("=" * 80)
