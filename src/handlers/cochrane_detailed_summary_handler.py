"""
DetailedSummary1 Rule - John Cochrane Handler
Rich extraction with direct quotes, citations, and extracted phrases
Always applied to The Grumpy Economist emails
"""

from anthropic import Anthropic

def is_cochrane_email(sender_email, sender_display_name, title):
    """
    Detect John Cochrane / Grumpy Economist emails
    """
    sender_lower = (sender_display_name or '').lower()
    email_lower = (sender_email or '').lower()
    title_lower = (title or '').lower()
    
    # Check for Cochrane indicators
    is_cochrane = (
        'cochrane' in sender_lower or
        'grumpy economist' in sender_lower or
        'grumpy economist' in title_lower or
        'johnhcochrane@substack.com' in email_lower
    )
    
    return is_cochrane


def enrich_cochrane_detailed(title, content_text, api_key):
    """
    DetailedSummary1 Rule:
    - Rich extraction with direct quotes
    - Organized sections with headers
    - Vertical bullets
    - Extracted phrases and citations
    - Target: 1,200-2,000 characters
    - Uses Claude 3.7 Sonnet with 4K tokens
    """
    
    client = Anthropic(api_key=api_key)
    
    # Limit content to avoid token limits
    content_for_analysis = content_text[:15000]
    
    prompt = f"""Format this John Cochrane "Grumpy Economist" article with RICH DETAIL and EXTRACTED PHRASES.

ARTICLE CONTENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{content_for_analysis}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FORMAT REQUIREMENTS:

1. Start with: "Rule: DetailedSummary1\n\n# 📝 The Grumpy Economist: [Title]"

2. "## 🎯 Main Argument" (3-4 sentences with Cochrane's actual framing)

3. "## 💡 Detailed Analysis" with subsections:
   • Use **bold headers** for each topic
   • Include DIRECT QUOTES from Cochrane (use "..." for his exact words)
   • Include SPECIFIC DATA and numbers mentioned
   • Include authors/research cited with full context
   • Each section should be RICH with detail and extracted phrases

4. "## 📊 Key Evidence" with specific citations and what they show

5. "## 💭 Bottom Line" (Cochrane's conclusion, preferably with direct quote)

CRITICAL RULES - DetailedSummary1:
• Use vertical bullets (each on own line)
• Extract Cochrane's ACTUAL PHRASES and put in quotes
• Include SPECIFIC citations (author + paper/book title if mentioned)
• Include SPECIFIC data points and numbers
• Include SPECIFIC examples and historical cases
• Make it DETAILED but organized
• Target: 1,500-2,500 characters (rich extraction)
• Preserve his arguments in his own words
• Make it easy to scan with clear section headers

Example quality:
Instead of: "Cochrane says rates don't cause inflation"
Use: "Cochrane notes 'we really don't know if, how much, or how soon' lower rates cause inflation, citing Valerie Ramey's research showing 'the price level goes nowhere for a year'"

OUTPUT ONLY the formatted summary, nothing else."""

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
            'actors': ['John Cochrane', 'The Grumpy Economist'],
            'themes': ['Economic Analysis', 'Monetary Policy', 'Economic Theory'],
            'ai_relevance_score': 9.0
        }
        
    except Exception as e:
        print(f"⚠️ Cochrane enrichment failed: {e}")
        return None
