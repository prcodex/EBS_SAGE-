"""
Gold Standard Enhanced Rule - Thematic Newsletters
Deep dive on main theme + quick hits for supporting stories
Applies to: Bloomberg Economics Daily, similar thematic content
"""

from anthropic import Anthropic

def is_gold_standard_enhanced(sender_email, sender_display_name, title, content_text):
    """
    Detect thematic newsletters that deserve deep analysis
    
    Criteria:
    - Bloomberg Economics Daily
    - Other thematic Bloomberg content with main deep dive
    - Content length > 3000 chars (substantial)
    - Has clear main theme + supporting stories
    """
    
    sender_lower = (sender_display_name or '').lower()
    title_lower = (title or '').lower()
    content_lower = (content_text or '')[:1000].lower()
    
    # Bloomberg Economics Daily
    if 'bloomberg' in sender_lower:
        if 'economics daily' in title_lower or 'economics daily' in content_lower:
            return True, 'Bloomberg Economics Daily'
    
    # Business Insider Today: series (thematic articles)
    if 'business insider' in sender_lower:
        if 'today:' in title_lower:
            return True, 'Business Insider Today'
    
    # Add other thematic newsletters here in future
    # (Money Stuff, Supply Lines, etc. if they have main theme + supporting stories)
    
    return False, None


def enrich_gold_standard_enhanced(title, content_text, newsletter_type, api_key):
    print(f"DEBUG HANDLER: title={title[:60]}, content_len={len(content_text)}, first_200={content_text[:200]}")
    
    # CRITICAL VALIDATION (Oct 29): Prevent hallucination from empty content
    if not content_text or len(content_text.strip()) < 100:
        print(f"   ❌ ERROR: Empty content_text ({len(content_text)} chars) - Cannot enrich without content!")
        return {
            'smart_summary': f"Rule: Error\n\n❌ Cannot enrich: No content available (content_text empty)",
            'actors': [],
            'themes': [],
            'smart_category': 'ERROR',
            'ai_relevance_score': 0.0
        }
    
    """
    Gold Standard Enhanced Rule:
    - Deep dive on main theme (6-10 bullets)
    - Author's actual phrases and voice
    - Complete argument chain
    - ALL citations and data
    - Quick hits for supporting stories
    - Research notes expanded
    - Target: 2,500-3,500 characters
    - Uses Claude 3.7 Sonnet with 8K tokens
    """
    
    client = Anthropic(api_key=''YOUR_ANTHROPIC_API_KEY_HERE'')
    
    # Use full content for analysis
    content_for_analysis = content_text[:15000]
    
    prompt = f"""Format this {newsletter_type} email using the GOLD STANDARD ENHANCED approach.

This is a THEMATIC newsletter with a main deep dive + supporting stories. Your goal is to:
1. Follow the author's narrative arc
2. Go DEEPER where the author goes deep
3. Use the author's actual phrases and voice
4. Preserve the analytical flow

CONTENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{content_for_analysis}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FORMAT REQUIREMENTS:

1. Start with: "Rule: Gold Standard Enhanced\\n\\n# 📊 {newsletter_type} - [Main Theme]"

2. "## 🎯 Today's Focus" (1-2 sentences setting context)

3. "## 💡 Main Analysis: [Topic Name]" (The DEEP DIVE)
   • Use the author's ACTUAL PHRASES in quotes where key
   • Include ALL specific arguments presented
   • Preserve the analytical narrative
   • Include ALL data points, percentages, years, levels
   • Capture the author's reasoning chain
   • Show comparisons and historical context
   • Include ALL citations (authors, institutions, reports)
   • 6-10 rich bullets for the main theme
   • Put EACH bullet on its OWN LINE (vertical format)

4. "## 📰 Quick Hits" (Other stories briefly, if present)
   • List top stories concisely (3-6 bullets)
   • Just enough detail to understand each story
   • Put EACH bullet on its OWN LINE

5. "## 📊 Research Note" or "## 📈 Data Point" (If present - expand if substantive)
   • Include forecasts, specific predictions
   • Author reasoning and evidence

CRITICAL RULES - Gold Standard Enhanced:
• START with "Rule: Gold Standard Enhanced" label
• Go DEEP on the main theme (6-10 bullets minimum)
• Use author's ACTUAL PHRASES for key arguments (put in "quotes")
• Include SPECIFIC citations (names, institutions, papers)
• Preserve the narrative flow and analytical voice
• Extract ALL data: percentages, years, levels, comparisons
• Show the author's complete reasoning chain
• Use vertical bullets (each on own line)
• Target: 2,500-3,500 characters (detailed but structured)
• Make main analysis COMPREHENSIVE

Example quality for main theme:
Instead of: "QE caused fiscal problems"
Use: "Stephen Jen argues QE 'spoilt fiscal authorities' like 'children of wealthy parents can be spoilt by parents' good intentions,' noting that 'in all cases where central banks engaged in money printing,' the fiscal situation has 'deteriorated sharply'"

OUTPUT ONLY the formatted summary, starting with "Rule: Gold Standard Enhanced"."""

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
        
        # Extract actors and themes from content
        actors = []
        themes = []
        
        # Simple entity extraction
        content_lower = content_for_analysis.lower()
        
        # Common actors in economics content
        if 'trump' in content_lower: actors.append('Trump')
        if 'fed' in content_lower or 'federal reserve' in content_lower: actors.append('Federal Reserve')
        if 'imf' in content_lower: actors.append('IMF')
        if 'ecb' in content_lower: actors.append('ECB')
        if 'boj' in content_lower or 'bank of japan' in content_lower: actors.append('Bank of Japan')
        
        # Common themes
        if 'fiscal' in content_lower or 'debt' in content_lower: themes.append('Fiscal Policy')
        if 'qe' in content_lower or 'quantitative easing' in content_lower: themes.append('Quantitative Easing')
        if 'inflation' in content_lower: themes.append('Inflation')
        if 'rate' in content_lower: themes.append('Interest Rates')
        if 'central bank' in content_lower: themes.append('Central Banking')
        
        # Limit to 5 each
        actors = actors[:5] if actors else ['Bloomberg Economics']
        themes = themes[:5] if themes else ['Economics Analysis']
        
        return {
            'smart_summary': formatted_summary,
            'actors': actors,
            'themes': themes,
            'smart_category': 'THEMATIC_ANALYSIS',
            'ai_relevance_score': 9.0
        }
        
    except Exception as e:
        print(f"⚠️ Gold Standard Enhanced enrichment failed: {e}")
        return None
