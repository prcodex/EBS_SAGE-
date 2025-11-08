"""
Joe Rule - Joe Weisenthal / Odd Lots Commentary
Captures full argument with thesis → evidence → conclusion
"""

from anthropic import Anthropic

def is_joe_odd_lots(sender_email, sender_display_name, title, content_text):
    """
    Detect Joe Weisenthal / Odd Lots commentary emails
    """
    sender_lower = (sender_email or '').lower()
    name_lower = (sender_display_name or '').lower()
    title_lower = (title or '').lower()
    content_lower = (content_text or '').lower()
    
    # Check for Odd Lots indicators
    odd_lots_indicators = [
        'odd lots' in title_lower,
        'odd lots' in content_lower[:500],
        'joe weisenthal' in content_lower[:500],
        'tracy alloway' in content_lower[:500],
        'oddlots@bloomberg.net' in sender_lower
    ]
    
    # Check for Bloomberg sender
    is_bloomberg = 'bloomberg' in name_lower or 'bloomberg' in sender_lower
    
    # Must be Bloomberg + have Odd Lots indicators
    if is_bloomberg and any(odd_lots_indicators):
        return True
    
    return False


def enrich_joe(title, content_text, api_key):
    """
    Joe Rule:
    - Extract the main thesis/argument
    - Organize as: Setup → Evidence → Conclusion
    - Preserve Joe's conversational style
    - Include ALL specific data
    - Target: 1,200-1,800 characters
    - Uses Claude 3.7 Sonnet with 4K tokens
    """
    
    client = Anthropic(api_key=api_key)
    
    # Use substantial content for full context
    content_for_analysis = content_text[:15000]
    
    prompt = f"""Format this Bloomberg Odd Lots commentary by Joe Weisenthal with COMPLETE coverage.

This is an ESSAY/COMMENTARY, not a news briefing. Joe makes ONE focused argument with supporting evidence.

CONTENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{content_for_analysis}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FORMAT REQUIREMENTS:

Start with: "Rule: Joe\\n\\n# 🎙️ Odd Lots - [Main Topic]"

Then organize as:

## 💡 Joe's Thesis
[2-3 sentences capturing his main argument]

## 📊 The Setup
• Context and background
• Why this matters now
• The problem being discussed

## 📈 The Evidence
**[Evidence Point 1]**
• All specific data (numbers, percentages)
• The comparison or observation
• What it shows

**[Evidence Point 2 if exists]**
• Specific observations
• Differences noted
• Implications

## 💭 The Conclusion
• Joe's takeaway and recommendation
• His conversational wrap-up

CRITICAL RULES - Joe:
• This is COMMENTARY, not news - capture the ARGUMENT
• Preserve Joe's conversational style and tone ("I do think", "It's not crazy", "from my seat")
• Include ALL specific data (percentages, comparisons, names)
• Organize by logical flow (thesis → evidence → conclusion)
• Keep it cohesive and readable
• Target: 1,200-1,800 characters
• Make it detailed but tight
• Each bullet on its OWN LINE (vertical format)

Output the formatted commentary, starting with "Rule: Joe"."""

    try:
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        formatted_summary = message.content[0].text.strip()
        
        return {
            'smart_summary': formatted_summary,
            'actors': ['Joe Weisenthal', 'Bloomberg Odd Lots'],
            'themes': ['Market Commentary', 'Economic Analysis'],
            'smart_category': 'COMMENTARY',
            'ai_relevance_score': 8.5
        }
        
    except Exception as e:
        print(f"⚠️ Joe enrichment failed: {e}")
        return None
