"""
Pílula Rule - Estadão News Capsules
Separate themes + extract details for each story
Applies to: Pílula, Manchetes, and other Estadão news capsules
"""

from anthropic import Anthropic

def is_estadao_pilula(sender_email, sender_display_name, title):
    """
    Detect Estadão news capsule emails
    
    Patterns:
    - Pílula (political capsule)
    - Manchetes (general headlines)
    - Política (politics newsletter)
    - Economia & Negócios (economy & business)
    """
    
    sender_lower = (sender_display_name or '').lower()
    title_lower = (title or '').lower()
    
    # Must be from Estadão
    if 'estadao' not in sender_lower and 'estadão' not in sender_lower:
        return False
    
    # Check for capsule formats
    capsule_indicators = [
        'pílula', 'pilula',
        'manchetes',
        '💊', '📰',  # Emojis used
        'política |',  # Section format
        'economia & negócios |'
    ]
    
    for indicator in capsule_indicators:
        if indicator in title_lower:
            return True
    
    return False


def enrich_pilula(title, content_text, api_key):
    """
    Pílula Rule:
    - Separate each story with bold headers
    - Extract ALL details per story
    - Keep stories independent
    - Preserve Portuguese
    - Target: 1,200-1,800 characters
    - Uses Claude 3.7 Sonnet with 2K tokens
    """
    
    client = Anthropic(api_key=api_key)
    
    # Limit content
    content_for_analysis = content_text[:12000]
    
    prompt = f"""Format this Estadão news capsule with SEPARATED THEMES and ALL DETAILS.

This is a Portuguese news digest with MULTIPLE independent stories. Your goal:
1. Identify EACH separate story/theme
2. Extract ALL details available for each story
3. Keep stories independent and scannable
4. Preserve Portuguese language

CONTENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{content_for_analysis}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FORMAT REQUIREMENTS:

1. Start with: "Rule: Pílula\\n\\n# 💊 Estadão - [Date or Main Topic]"

2. List EACH story with numbered structure:
   <strong style="font-size: 17px; display: block; margin-top: 10px; margin-bottom: 4px;">Story #: [Theme/Topic]</strong>
   • Detail with specific names, dates, context
   • Detail with quotes or specific actions
   • Detail with implications or numbers
   [2-4 bullets per story with ALL available details]

CRITICAL RULES - Pílula:
• Identify EVERY separate story/theme (usually 3-6 stories)
• Each story gets: numbered bold headline + 2-4 detail bullets
• Extract ALL details: names, dates, quotes, numbers, context, locations
• Keep each story INDEPENDENT and clear
• Use Portuguese language (preserve original text)
• Use vertical bullets (each on own line)
• Put EACH bullet on its OWN LINE
• Target: 1,200-1,800 characters total
• Make it SCANNABLE with story separation

Example format:
<strong style="font-size: 17px; display: block; margin-top: 10px; margin-bottom: 4px;">1: Governo Busca Afastar Regra do Arcabouço</strong>
• Governo federal quer afastar regra do arcabouço fiscal para aumentar gastos com pessoal
• TCU e consultores do Congresso apontam que mudança é ilegal
• Foco em ano eleitoral (2026) para elevar gastos

<strong style="font-size: 17px; display: block; margin-top: 10px; margin-bottom: 4px;">2: Next Story Theme</strong>
• Detail with names and context
• Detail with specific data

OUTPUT ONLY the formatted summary in Portuguese, starting with "Rule: Pílula"."""

    try:
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        formatted_summary = message.content[0].text.strip()
        
        return {
            'smart_summary': formatted_summary,
            'actors': ['Estadão'],
            'themes': ['Brazilian News', 'Political Updates'],
            'smart_category': 'NEWS_CAPSULE',
            'ai_relevance_score': 7.5
        }
        
    except Exception as e:
        print(f"⚠️ Pílula enrichment failed: {e}")
        return None
