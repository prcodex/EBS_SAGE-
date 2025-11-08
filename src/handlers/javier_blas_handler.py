"""
Javier Rule - Javier Blas Articles
Focused extraction using Javier's actual words about the topic
Always applied to Javier Blas author alerts from Bloomberg
"""

from anthropic import Anthropic

def is_javier_blas_article(sender_email, sender_display_name, content_text):
    """
    Detect Javier Blas articles from Bloomberg author alerts
    
    Pattern:
    - Sender: Bloomberg
    - Content contains: "Javier Blas, just published a story"
    """
    
    sender_lower = (sender_display_name or '').lower()
    content_lower = (content_text or '')[:500].lower()
    
    # Check for Javier Blas author alert
    is_javier = (
        'bloomberg' in sender_lower and
        ('javier blas' in content_lower and 'just published' in content_lower)
    )
    
    return is_javier


def enrich_javier_blas(title, content_text, api_key):
    """
    Javier Rule:
    - Extract the full text about the topic
    - Use Javier's actual words and voice
    - Focus on his main argument/analysis
    - Preserve his style and phrases
    - Target: 1,000-1,500 characters
    - Uses Claude 3.7 Sonnet with 4K tokens
    """
    
    client = Anthropic(api_key=api_key)
    
    # Clean the content - remove the intro line
    cleaned_content = content_text
    if 'Javier Blas, just published a story' in content_text:
        # Split and take everything after the intro
        parts = content_text.split('just published a story.', 1)
        if len(parts) > 1:
            cleaned_content = parts[1].strip()
    
    # Limit content
    content_for_analysis = cleaned_content[:10000]
    
    prompt = f"""Extract and format this Javier Blas article using his ACTUAL WORDS and VOICE.

ARTICLE CONTENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{content_for_analysis}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FORMAT REQUIREMENTS:

1. Start with: "Rule: Javier\\n\\n# 🛢️ Javier Blas: [Topic]"

2. "## 💡 His Take" (2-3 sentences capturing his main argument)

3. "## 📊 The Analysis" 
   • Extract the FULL narrative using his actual phrases
   • Include ALL specific examples he provides
   • Include ALL data points and numbers mentioned
   • Preserve his writing style and voice
   • Use his ACTUAL WORDS in quotes for key points
   • Show his comparisons and observations
   • 5-8 rich bullets covering his complete analysis

CRITICAL RULES - Javier:
• Use Javier's ACTUAL PHRASES (put key ones in quotes)
• Include ALL specific examples (Ford Explorer, Honda, 26.4 mpg, 45+ miles)
• Include ALL data and numbers he mentions
• Preserve his conversational, observational style
• Extract the FULL topic discussion
• Use vertical bullets
• Target: 1,000-1,500 characters (focused but complete)

Example quality:
Instead of: "Javier discusses US fuel consumption"
Use: "Javier admits 'I'm slightly embarrassed' that his rental Ford Explorer achieved 'a ludicrously low average fuel economy of 26.4 miles per gallon' vs his UK Honda's '45-plus miles'"

OUTPUT ONLY the formatted summary, starting with "Rule: Javier"."""

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
            'actors': ['Javier Blas', 'Bloomberg'],
            'themes': ['Energy', 'Commodities', 'Markets'],
            'smart_category': 'AUTHOR_ANALYSIS',
            'ai_relevance_score': 8.5
        }
        
    except Exception as e:
        print(f"⚠️ Javier enrichment failed: {e}")
        return None
