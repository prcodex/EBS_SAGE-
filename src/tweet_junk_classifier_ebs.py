#!/usr/bin/env python3
'''
Automatic Junk Classifier for Tweets - EBS Version
Runs after enrichment, auto-junks tweets with low AI scores (<= 3)
'''

import lancedb
import pandas as pd
import time
from datetime import datetime

EBS_DB = "/mnt/lancedb"
JUNK_THRESHOLD = 3  # auto-junk scores 1-3
DELAY_SECONDS = 2   # Respect 2-second rule for safe LanceDB updates


def main():
    print("=" * 80)
    print("TWEET AUTO-JUNK CLASSIFIER - EBS")
    print("=" * 80)
    print(f"Time: {datetime.now()}")
    print(f"Database: {EBS_DB}")
    print(f"Threshold: ai_score <= {JUNK_THRESHOLD}")
    print("")

    db = lancedb.connect(EBS_DB)
    table = db.open_table('unified_feed')
    df = table.to_pandas()

    # Find candidates: tweets with AI score 1-3 that aren't already junk
    candidates = df[
        (df['source_type'] == 'tweet') &
        (df['ai_score'] > 0) &
        (df['ai_score'] <= JUNK_THRESHOLD) &
        (df['is_junk'] == False)
    ].sort_values('ai_score')

    print(f"📊 Found {len(candidates)} tweets with ai_score <= {JUNK_THRESHOLD}\n")

    if len(candidates) == 0:
        print("✅ No tweets to auto-junk")
        print("=" * 80)
        return

    print("📋 Tweets to be auto-junked:")
    for _, tweet in candidates.head(10).iterrows():  # Show first 10
        sender = str(tweet.get('sender_tag') or 'Unknown')[:20]
        title = str(tweet.get('title') or tweet.get('content_text') or '')[:60]
        score = tweet.get('ai_score', 0)
        print(f"  🗑️  Score {score:.1f} | {sender:20s} | {title}")
    if len(candidates) > 10:
        print(f"  ... and {len(candidates) - 10} more")
    print("")

    junked = 0
    errors = 0
    
    for _, tweet in candidates.iterrows():
        tweet_id = tweet['id']
        try:
            # Update using pandas approach (EBS compatible)
            table.update(
                where=f"id = '{tweet_id}'",
                values={'is_junk': True}
            )
            time.sleep(DELAY_SECONDS)
            junked += 1
            if junked % 5 == 0:
                print(f"  ✅ Junked {junked}/{len(candidates)}...")
        except Exception as exc:
            print(f"  ❌ Error junking {tweet_id}: {exc}")
            errors += 1

    print("")
    print("=" * 80)
    print(f"✅ Auto-junked {junked}/{len(candidates)} tweets")
    if errors > 0:
        print(f"⚠️  Errors: {errors}")
    print("   They now appear in the Tweet Junk view (restore any if needed)")
    print("=" * 80)


if __name__ == '__main__':
    main()
