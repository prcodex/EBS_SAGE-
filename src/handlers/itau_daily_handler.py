"""
SCRAPEX 2.6 - Itau Daily Handler with AI-Extracted Actors/Themes
ONE Claude call extracts: formatted_content + actors + themes
"""

from bs4 import BeautifulSoup
import re
from anthropic import Anthropic
import json

def is_itau_daily(title, sender_display_name, content_text):
    """Detect if this is an Itau Daily macro report"""
    if not sender_display_name or ('pedro' not in sender_display_name.lower() and 'itau' not in sender_display_name.lower()):
        return False
    
    title_lower = title.lower() if title else ""
    title_indicators = ['daily', 'macro wrap', 'diário']
    
    has_title_match = any(ind in title_lower for ind in title_indicators)
    has_key_points = 'key points:' in content_text.lower()
    
    return has_title_match or has_key_points


def detect_country(title, content_text):
    """Detect which country's daily report"""
    title_lower = title.lower() if title else ""
    
    if 'brazil' in title_lower or 'brasil' in title_lower:
        return 'Brazil', '🇧🇷'
    if 'us daily' in title_lower:
        return 'US', '🇺🇸'
    if 'china' in title_lower:
        return 'China', '🇨🇳'
    if 'europe' in title_lower:
        return 'Europe', '🇪🇺'
    if 'mexico' in title_lower:
        return 'Mexico', '🇲🇽'
    if 'chile' in title_lower or 'peru' in title_lower:
        return 'Chile & Peru', '🇨🇱🇵🇪'
    if 'argentina' in title_lower:
        return 'Argentina', '🇦🇷'
    
    return 'General', '🌍'


def extract_with_claude_v26(content_html, content_text, api_key):
    """
    ONE Claude call extracts: formatted_content + actors + themes
    Returns dict with all three
    """
    
    # Get raw text from HTML
    soup = BeautifulSoup(content_html, 'html.parser')
    for tag in soup(['script', 'style', 'meta', 'link', 'head']):
        tag.decompose()
    
    body = soup.find('body') or soup
    raw_text = body.get_text(separator='\n')
    
    # Limit input (15K chars)
    if len(raw_text) > 15000:
        raw_text = raw_text[:15000]
    
    # ONE Claude call for everything
    client = Anthropic(api_key=''YOUR_ANTHROPIC_API_KEY_HERE'')
    
    prompt = f"""Extract and format this Itau Daily macro report, then analyze it.

RAW EMAIL TEXT (has noise and formatting issues):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{raw_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK 1 - FORMAT CONTENT:
• REMOVE: Footers ("Corporativo"), disclaimers ("Esta mensagem é reservada", "This message is reserved"), signatures ("Pedro Renault"), addresses ("Faria Lima"), URLs, chart noise
• PRESERVE: "October 22 Macro Wrap" opening, complete analysis, "Key Points:" section with all subsections
• FIX: Line breaks (join mid-sentence breaks), create smooth paragraph flow
• KEEP: Original language (don't translate!)

CRITICAL - BULLET POINT FORMATTING:
• When you see bullet points or list items, put EACH ONE ON ITS OWN LINE
• NEVER format like: "• Point 1 • Point 2 • Point 3" (horizontal)
• ALWAYS format like:
  • Point 1
  • Point 2
  • Point 3
• Each bullet should be on a separate line with a line break after it
• This makes lists easy to read and scan

TASK 2 - EXTRACT ACTORS (from the content you formatted):
• Identify 1-7 people, institutions, companies, or government bodies actually mentioned
• Examples: "Finance Minister", "Central Bank of Brazil", "TCU", "Senate", "Trump", "PBOC"
• Only include entities explicitly mentioned in the text
• If fewer than 7, that's fine - quality over quantity

TASK 3 - EXTRACT THEMES (from the content you formatted):
• Identify 1-7 key topics or subjects actually discussed
• Examples: "Fiscal Package", "Tax Reform", "US-Brazil Relations", "Budget Dispute"
• Only themes that are substantively covered in the text
• If fewer than 7, that's fine

OUTPUT FORMAT (JSON only):
{{
  "rule_label": "Rule: Itau Daily",
             "formatted_content": "October 22 Macro Wrap - daily podcast...\\n\\nOpening paragraph...\\n\\nKey Points:\\n\\nSection 1...",
  "actors": ["Finance Minister", "Central Bank of Brazil", "TCU", "Senate", "US President"],
  "themes": ["Fiscal Package", "Tax Reform", "Budget Dispute", "US-Brazil Meeting", "Income Tax Reform"]
}}

Return ONLY valid JSON. No commentary before or after."""

    try:
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        response_text = message.content[0].text.strip()
        
        # Parse JSON response
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        
        result = json.loads(response_text)
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parse error: {e}")
        print(f"   Response: {response_text[:200]}")
        return None
    except Exception as e:
        print(f"⚠️ Claude extraction failed: {e}")
        return None


def enrich_itau_daily(title, content_text, content_html, sender_tag, api_key):
    """
    SCRAPEX 2.6: AI-extracted actors/themes from content
    """
    
    country, flag = detect_country(title, content_text)
    
    # ONE Claude call for formatted_content + actors + themes
    result = extract_with_claude_v26(content_html, content_text, api_key)
    
    if not result:
        print("⚠️ Falling back to hardcoded actors/themes")
        # Fallback to old approach
        return None
    
    # Extract from JSON
    formatted_content = result.get('formatted_content', '')
    actors = result.get('actors', [])
    themes = result.get('themes', [])
    
    # Validate
    if not formatted_content or len(formatted_content) < 200:
        print("⚠️ Formatted content too short, fallback needed")
        return None
    
    # Ensure actors and themes are lists with 1-7 items
    if not isinstance(actors, list):
        actors = []
    if not isinstance(themes, list):
        themes = []
    
    actors = actors[:7]  # Max 7
    themes = themes[:7]  # Max 7
    
    # Create final summary with header
    summary = f"""# {flag} {title}

{formatted_content}

---
📊 **Itau {country} Macro Daily** - Full content preserved
🎧 Available in English and Portuguese"""
    
    return {
        'smart_summary': summary,
        'ai_relevance_score': 9.0,
        'actors': actors,  # AI-extracted!
        'themes': themes   # AI-extracted!
    }
