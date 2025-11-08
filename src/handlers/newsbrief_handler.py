"""
NewsBrief Handler - Extracts individual stories from newsletter briefings
Version 1.4 - October 31, 2025
"""

from anthropic import Anthropic
import re

def enrich_newsbrief_with_links(title, content_text, sender_tag, api_key):
    """
    Enhanced NewsBrief handler that extracts individual stories with proper formatting
    """
    client = Anthropic(api_key=api_key)
    
    # Clean the content
    content_text = re.sub(r'\s+', ' ', content_text).strip()
    if len(content_text) > 12000:
        content_text = content_text[:12000]
    
    prompt = f"""Extract the individual news stories from this newsletter briefing.

RULES:
1. Extract ONLY actual news stories (no market snapshots or meta content)
2. Number each story clearly (1, 2, 3...)
3. Use the EXACT headlines from the newsletter
4. Add 2-4 bullet points per story with specific details

Format each story EXACTLY like this:

<strong style="font-size: 19px; display: block; margin-top: 15px; margin-bottom: 6px; color: #202124;">1. [Exact Story Headline]</strong>
• [Specific fact or detail from the story]
• [Another key point with numbers/names if available]
• [Additional context from the story]

Newsletter title: {title}
Newsletter content:
{content_text}

Extract between 6-12 stories. Focus on the main news items."""
    
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",  # Using Haiku which we know works
            max_tokens=2500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        enriched = response.content[0].text.strip()
        
        # Add the rule label
        enriched = f"Rule: NewsBrief\n\n{enriched}"
        
        # Clean up extra newlines
        enriched = re.sub(r'\n{3,}', '\n\n', enriched)
        
        return enriched
        
    except Exception as e:
        print(f"Error in NewsBrief handler: {e}")
        # Fallback formatting
        return f"""Rule: NewsBrief

<strong style="font-size: 19px; display: block; margin-top: 15px; margin-bottom: 6px;">{title}</strong>
• Newsletter briefing from {sender_tag}
• Contains multiple news stories and updates
• Check full email for complete details"""


def extract_links_from_html(html_content):
    """Extract article links from newsletter HTML"""
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        text = a_tag.get_text(strip=True)
        
        # Skip junk
        if not href.startswith('http'):
            continue
        
        skip = ['unsubscribe', 'subscribe', 'preference', 'settings',
                'facebook', 'twitter', 'linkedin', 'instagram']
        
        if any(s in href.lower() for s in skip):
            continue
        
        if len(text) > 15:  # Article-length text
            links.append(href)
    
    return links
