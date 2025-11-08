"""
WSJ Opinion Handler - Simple Title-Only Display
Just shows the opinion title, nothing else
"""

def is_wsj_teaser(sender_email, sender_display_name, title, content_text):
    """
    Detect WSJ Opinion emails
    """
    sender_lower = (sender_display_name or '').lower()
    sender_email_lower = (sender_email or '').lower()
    title_lower = (title or '').lower()
    
    # Check if it's from WSJ
    is_wsj = (
        'wsj' in sender_lower or
        'wall street' in sender_lower or
        'emma tucker' in sender_lower or
        'spencer' in sender_lower or
        'wei' in sender_lower or
        'wsj.com' in sender_email_lower or
        'interactive.wsj.com' in sender_email_lower
    )
    
    # Check if it's an Opinion piece
    is_opinion = 'opinion' in title_lower or 'opinion:' in title_lower
    
    # WSJ Opinion teasers are short (< 1000 chars typically)
    is_short = len(content_text) < 2000
    
    return is_wsj and is_opinion and is_short


def extract_wsj_teaser_content(title, content_html):
    """
    Extract just the clean title for WSJ Opinion
    
    Returns simple format:
    📰 WSJ Opinion: [Clean Title]
    """
    
    # Clean the title
    clean_title = title.strip()
    
    # Remove "Opinion:" prefix if it's at the start
    if clean_title.lower().startswith('opinion:'):
        clean_title = clean_title[8:].strip()
    
    # Remove "FW:" if present
    if clean_title.upper().startswith('FW:'):
        clean_title = clean_title[3:].strip()
    
    # Remove "Opinion:" again if still there
    if clean_title.lower().startswith('opinion:'):
        clean_title = clean_title[8:].strip()
    
    # Simple format - just the title
    summary = f"Rule: WSJ Opinion\n\n📰 WSJ Opinion: {clean_title}"
    
    return {
        'smart_summary': summary,
        'actors': ['WSJ', 'Opinion'],
        'themes': ['Opinion Column'],
        'ai_relevance_score': 7.0
    }


def enrich_wsj_teaser(title, content_html):
    """
    Wrapper function for compatibility
    """
    return extract_wsj_teaser_content(title, content_html)
