#!/usr/bin/env python3
"""
ID Tracker EBS - Prevent duplicate processing for EBS system
Thread-safe JSON file tracking
"""
import json
import os
from datetime import datetime
from threading import Lock

TRACKER_FILE = 'processed_ids_ebs.json'
_lock = Lock()

def load_tracker():
    """Load processed IDs"""
    default_tracker = {
        "newsbrief_digests": [], 
        "newsbrief_stories": [],
        "tweets": [], 
        "last_updated": datetime.now().isoformat()
    }
    
    if not os.path.exists(TRACKER_FILE):
        return default_tracker
    
    with _lock:
        try:
            with open(TRACKER_FILE, 'r') as f:
                tracker = json.load(f)
                # Ensure all required keys exist
                for key in default_tracker:
                    if key not in tracker:
                        tracker[key] = default_tracker[key]
                return tracker
        except:
            return default_tracker

def save_tracker(tracker):
    """Save processed IDs"""
    tracker['last_updated'] = datetime.now().isoformat()
    with _lock:
        with open(TRACKER_FILE, 'w') as f:
            json.dump(tracker, f, indent=2)

def is_digest_processed(digest_id):
    """Check if NewsBreif digest was already split"""
    tracker = load_tracker()
    return digest_id in tracker.get('newsbrief_digests', [])

def mark_digest_processed(digest_id):
    """Mark NewsBreif digest as processed"""
    tracker = load_tracker()
    if digest_id not in tracker.get('newsbrief_digests', []):
        if 'newsbrief_digests' not in tracker:
            tracker['newsbrief_digests'] = []
        tracker['newsbrief_digests'].append(digest_id)
        save_tracker(tracker)

def is_story_processed(story_id):
    """Check if story was already processed"""
    tracker = load_tracker()
    return story_id in tracker.get('newsbrief_stories', [])

def mark_story_processed(story_id):
    """Mark story as processed"""
    tracker = load_tracker()
    if story_id not in tracker.get('newsbrief_stories', []):
        if 'newsbrief_stories' not in tracker:
            tracker['newsbrief_stories'] = []
        tracker['newsbrief_stories'].append(story_id)
        save_tracker(tracker)

def is_tweet_processed(tweet_id):
    """Check if tweet was already processed"""
    tracker = load_tracker()
    return tweet_id in tracker.get('tweets', [])

def mark_tweet_processed(tweet_id):
    """Mark tweet as processed"""
    tracker = load_tracker()
    if tweet_id not in tracker.get('tweets', []):
        if 'tweets' not in tracker:
            tracker['tweets'] = []
        tracker['tweets'].append(tweet_id)
        save_tracker(tracker)
