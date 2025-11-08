"""
El-Erian REP (Replication) Handler
Preserves author's voice and message at ~80% original length
October 2025
"""

from typing import Dict
from bs4 import BeautifulSoup
import anthropic
import re


def is_elerian_email(sender_email: str, sender_display_name: str, title: str, content_text: str) -> bool:
    """Detect Mohamed El-Erian emails"""
    sender_lower = (sender_email or '').lower()
    name_lower = (sender_display_name or '').lower()
    
    # Check for El-Erian identifiers
    elerian_indicators = [
        'mohamedelerian@substack.com' in sender_lower,
        'mohamed el-erian' in name_lower,
        'el-erian' in name_lower
    ]
    
    return any(elerian_indicators)


def extract_clean_content(content_html: str, content_text: str) -> str:
    """Extract clean content from email"""
    # Prefer HTML for better structure
    if content_html and len(content_html) > len(content_text):
        soup = BeautifulSoup(content_html, 'html.parser')
        
        # Remove scripts, styles, footers
        for element in soup(['script', 'style', 'footer', 'nav']):
            element.decompose()
        
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(line for line in lines if line)
        
        return text[:35000]  # Up to 35K chars for comprehensive analysis
    
    return content_text[:35000]


def enrich_elerian_rep(title: str, content_text: str, content_html: str, api_key: str) -> Dict:
    """
    REP Rule for El-Erian:
    Preserve his voice, style, and message at ~80% original length
    Extract all arguments, data, and insights
    """
    print(f"   ✍️  EL-ERIAN REP Processing: {title[:50]}...")
    
    # Extract clean content
    clean_content = extract_clean_content(content_html, content_text)
    
    if len(clean_content) < 200:
        return {
            'smart_summary': f"Rule: Rep\n\n# Mohamed El-Erian\n## {title}\n\n[Content too short for analysis]",
            'actors': ['Mohamed El-Erian'],
            'themes': ['Economics'],
            'smart_category': 'ECONOMIC_COMMENTARY',
            'ai_relevance_score': 7.0
        }
    
    # Create comprehensive prompt that preserves voice
    prompt = f"""You are analyzing Mohamed El-Erian's economic commentary. Your task is to preserve his voice, style, and complete message while creating a slightly condensed version (~80% of original length).

ORIGINAL CONTENT:
{clean_content}

MOHAMED EL-ERIAN'S STYLE:
• Accessible yet sophisticated economic analysis
• Clear frameworks (3-part structures, numbered points)
• Bridges theory and practice
• Data-driven but human-focused
• Policy implications emphasized
• Historical context woven in
• Measured, balanced tone

YOUR TASK - PRESERVE 80% VERSION:

1. PRESERVE STRUCTURE:
   • Keep his organizational framework (if 3 parts, keep 3 parts)
   • Maintain his numbered points/sections
   • Preserve opening and closing

2. EXTRACT ALL KEY ELEMENTS:
   • Main thesis and argument
   • ALL data points, numbers, percentages
   • His specific phrases and terminology
   • Policy implications
   • Historical references
   • Market analysis
   • Recommendations or conclusions

3. PRESERVE VOICE:
   • Use his exact phrasing for key points (in "quotes")
   • Maintain his analytical style
   • Keep his frameworks and structures
   • Preserve his tone (accessible sophistication)

4. SLIGHT CONDENSATION (aim for ~80% length):
   • Remove redundant phrasing
   • Condense examples slightly
   • Streamline transitions
   • BUT keep all substance, data, and arguments

5. OUTPUT FORMAT:

Rule: Rep

# Mohamed El-Erian
## {title}

[If he has an opening framework or structure, preserve it]

**[His Main Argument/Framework]**

[Extract his complete argument with all data points, using his exact phrases in "quotes" for key insights]

**[Section 2]**

[Continue preserving structure and voice]

[Continue for ALL his sections - don't skip]

**Policy Implications**

[If he discusses policy, extract completely]

**Market/Economic Outlook**

[His views on markets/economy with all data]

**Bottom Line**

[His conclusion - use his exact closing thoughts]

────────────────────────────────────────────────────────────

CRITICAL INSTRUCTIONS:
• Target: 80% of original length (if original is 5000 chars, aim for 4000)
• Extract ALL data points and specific numbers
• Use extensive direct quotes for his key insights
• Preserve his analytical frameworks
• Maintain his measured, balanced tone
• Cover ALL sections he discusses
• Don't summarize his examples - keep them with slight condensation
• Ensure NOTHING important is lost

Provide a JSON response with:
{{
  "summary": "The complete Rep rule output",
  "actors": ["People, institutions, organizations mentioned"],
  "themes": ["Key topics covered"],
  "word_count_estimate": estimated character count
}}"""
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Use Claude 3.7 Sonnet with 12K tokens for comprehensive extraction
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=12288,  # 12K for 80% preservation
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        response_text = message.content[0].text
        
        # Parse JSON
        try:
            import json
            # Try direct JSON parse
            result = json.loads(response_text)
        except:
            # Try regex extraction
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                # Fallback: use raw response
                result = {
                    'summary': response_text,
                    'actors': ['Mohamed El-Erian'],
                    'themes': ['Economics', 'Policy']
                }
        
        summary = result.get('summary', response_text)
        actors = result.get('actors', ['Mohamed El-Erian'])
        themes = result.get('themes', ['Economics'])
        
        print(f"   ✅ Generated {len(summary)} chars preserving El-Erian's voice")
        
        return {
            'smart_summary': summary,
            'actors': actors[:7],
            'themes': themes[:7],
            'smart_category': 'ELERIAN_COMMENTARY',
            'ai_relevance_score': 9.0
        }
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            'smart_summary': f"Rule: Rep\n\n# Mohamed El-Erian\n## {title}\n\n[Processing error]",
            'actors': ['Mohamed El-Erian'],
            'themes': ['Economics'],
            'smart_category': 'ELERIAN_COMMENTARY',
            'ai_relevance_score': 7.0
        }
