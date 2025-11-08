"""
Bloomberg Breaking News Handler - Simple Title-Only Display
Just shows the breaking news title, nothing else
Same approach as WSJ Opinion
"""

def is_bloomberg_breaking_news(sender_display_name, title, content_text):
    """
    Detect Bloomberg Breaking News alerts
    """
    sender_lower = (sender_display_name or '').lower()
    title_lower = (title or '').lower()
    
    # Check if it's from Bloomberg
    is_bloomberg = 'bloomberg' in sender_lower
    
    # Check if it's Breaking News
    is_breaking = 'breaking news' in title_lower or 'breaking:' in title_lower
    
    # Breaking news are short alerts (< 2000 chars typically)
    is_short = len(content_text) < 2000
    
    return is_bloomberg and is_breaking


def extract_bloomberg_breaking_news(title):
    """
    Extract just the clean title for Bloomberg Breaking News
    
    Returns simple format:
    📰 Bloomberg Breaking News: [Clean Title]
    """
    
    # Clean the title
    clean_title = title.strip()
    
    # Remove "Breaking News:" prefix if at start
    if clean_title.lower().startswith('breaking news:'):
        clean_title = clean_title[14:].strip()
    elif clean_title.lower().startswith('breaking:'):
        clean_title = clean_title[9:].strip()
    
    # Remove "FW:" if present
    if clean_title.upper().startswith('FW:'):
        clean_title = clean_title[3:].strip()
    
    # Check again for breaking news prefix after FW removal
    if clean_title.lower().startswith('breaking news:'):
        clean_title = clean_title[14:].strip()
    
    # Simple format - just the title
    summary = f"Rule: Bloomberg Breaking News\n\n📰 Bloomberg Breaking News: {clean_title}"
    
    return {
        'smart_summary': summary,
        'actors': ['Bloomberg'],
        'themes': ['Breaking News', 'News Alert'],
        'ai_relevance_score': 8.0
    }
