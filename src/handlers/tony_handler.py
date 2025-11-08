"""
Tony Rule - Tony Pasquariello (Goldman Sachs) Market Commentary
Preserves his numbered structure, sub-points, and conversational style
"""

from anthropic import Anthropic

def is_tony_email(sender_email, sender_display_name):
    """
    Detect Tony Pasquariello emails from Goldman Sachs
    """
    sender_lower = (sender_email or '').lower()
    name_lower = (sender_display_name or '').lower()
    
    # Check for Tony Pasquariello
    if 'tony.pasquariello@mail.marquee.gs.com' in sender_lower:
        return True
    
    if 'tony' in name_lower and 'pasquariello' in name_lower:
        return True
    
    return False


def enrich_tony(title, content_text, api_key):
    """
    Tony Rule:
    - Preserve his numbered structure (1, 2, 3...)
    - Preserve his sub-points (i, ii, iii...)
    - Preserve his conversational style
    - Keep ALL data points and colleague quotes
    - Only marginally condense if needed
    - Target: 2,500-4,000 characters
    - Uses Claude 3.7 Sonnet with 8K tokens
    """
    
    client = Anthropic(api_key=api_key)
    
    # Use substantial content (Tony's emails are already concise)
    content_for_analysis = content_text[:25000]
    
    prompt = f"""Format this Tony Pasquariello (Goldman Sachs) market commentary preserving HIS STRUCTURE and STYLE.

Tony's emails are already well-organized summaries with numbered points. Your job:
- PRESERVE his numbered structure (1. 2. 3. etc.)
- PRESERVE his sub-points (i. ii. iii. etc.)
- PRESERVE his conversational style ("from my seat", "to my eye", "for good order's sake")
- PRESERVE his specific phrases and tone
- Keep ALL key data points, names, percentages
- Keep colleague quotes intact (Pete Callahan, Will Marshall, etc.)
- Only marginally condense if truly redundant
- This is NOT a summary - it's a PRESERVATION with minor cleanup

CONTENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{content_for_analysis}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FORMAT REQUIREMENTS:

Start with: "Rule: Tony\\n\\n# 💼 Tony Pasquariello (GS) - Market Commentary"

Then preserve his structure:
**1. [Topic]**
His analysis with specific data...

**2. [Topic]**  
His follow-on point...

For sub-points, use:
  i. First sub-point
  ii. Second sub-point

CRITICAL RULES - Tony:
• MAINTAIN his numbered structure (1, 2, 3...)
• MAINTAIN his sub-points (i, ii, iii...)
• PRESERVE his conversational tone and phrases
• Keep ALL data: percentages, names, forecasts
• Keep colleague quotes verbatim
• Only condense if truly redundant
• Target: 2,500-4,000 characters (maintain most content)
• Make numbered topics bold: **1. Topic**

Output the formatted commentary, starting with "Rule: Tony"."""

    try:
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=8192,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        formatted_summary = message.content[0].text.strip()
        
        return {
            'smart_summary': formatted_summary,
            'actors': ['Tony Pasquariello', 'Goldman Sachs'],
            'themes': ['Market Commentary', 'Trading Insights'],
            'smart_category': 'MARKETS',
            'ai_relevance_score': 9.0
        }
        
    except Exception as e:
        print(f"⚠️ Tony enrichment failed: {e}")
        return None
