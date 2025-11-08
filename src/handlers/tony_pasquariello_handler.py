"""
Tony Pasquariello Handler - Goldman Sachs Special
Preserves original numbered structure and conversational style
Tony is Head of Global Markets at Goldman Sachs
"""

from anthropic import Anthropic

def enrich_tony_pasquariello(title, content_text, api_key):
    """
    Tony Pasquariello Rule:
    - Preserves his ORIGINAL NUMBERED STRUCTURE (1. 2. 3. etc.)
    - Maintains conversational, direct tone
    - Includes ALL data points and market levels
    - Keeps his personal observations and "I think..." statements
    - Uses his actual phrases in quotes
    - Target: 1,500-2,500 characters (comprehensive but natural)
    """
    
    # Validation
    if not content_text or len(content_text.strip()) < 100:
        return {
            'smart_summary': "Rule: Error\n\n❌ Cannot enrich: No content available",
            'actors': [],
            'themes': [],
            'smart_category': 'MARKETS',
            'ai_relevance_score': 0.0
        }
    
    client = Anthropic(api_key=api_key)
    
    # Extract content
    content_for_analysis = content_text[:15000]
    
    prompt = f"""You are analyzing an email from Tony Pasquariello, Head of Global Markets at Goldman Sachs.

Tony writes in a NUMBERED, CONVERSATIONAL style. Your job is to preserve his structure and voice.

Title: {title}

Content:
{content_for_analysis}

Create a summary following these rules:

1. START with "Rule: Tony Pasquariello (Goldman Sachs)"

2. PRESERVE HIS NUMBERED STRUCTURE:
   - If he writes "1. Markets... 2. Rates... 3. FX..." → Keep that exact structure!
   - Each numbered point on its own section
   - Use his original numbering system

3. MAINTAIN HIS CONVERSATIONAL TONE:
   - Keep phrases like "I think...", "My view...", "Here's what matters..."
   - Preserve his direct, personal style
   - Include his market observations in his words

4. INCLUDE ALL DATA POINTS:
   - Market levels (S&P 500 at X, yields at Y%)
   - Specific numbers and percentages
   - Price targets and ranges
   - Historical comparisons

5. FORMAT:
   ```
   Rule: Tony Pasquariello (Goldman Sachs)
   
   1. [First Topic - Using his words]
   • Key point with "his actual phrase in quotes"
   • Specific data: S&P at X, yields at Y%
   • His observation or view
   
   2. [Second Topic]
   • Key point...
   
   3. [Third Topic]
   • Key point...
   ```

6. LENGTH: 1,500-2,500 characters
   - Comprehensive but not bloated
   - All numbered sections included
   - Conversational flow preserved

CRITICAL:
• Preserve his NUMBERED STRUCTURE (most important!)
• Use HIS ACTUAL WORDS for key points (in quotes)
• Keep conversational tone (I think, my view, here's...)
• Include ALL specific market levels and data
• Don't reorganize - follow his structure

OUTPUT ONLY the formatted summary, starting with "Rule: Tony Pasquariello (Goldman Sachs)"."""

    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        summary = response.content[0].text
        
        return {
            'smart_summary': summary,
            'actors': [],  # Could extract if needed
            'themes': ['Markets', 'Trading', 'Goldman Sachs Views'],
            'smart_category': 'MARKETS',
            'ai_relevance_score': 9.0
        }
        
    except Exception as e:
        return {
            'smart_summary': f"Rule: Tony Pasquariello (Goldman Sachs)\n\n❌ Enrichment error: {str(e)[:200]}",
            'actors': [],
            'themes': [],
            'smart_category': 'ERROR',
            'ai_relevance_score': 5.0
        }

