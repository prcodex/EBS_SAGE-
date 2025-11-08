"""
GS Rates Research Handler
Deep, detailed analysis written in the author's voice
October 2025
"""

import re
from typing import Dict, Optional
from bs4 import BeautifulSoup
import anthropic


def is_gs_rates(sender_email: str, sender_display_name: str, title: str, content_text: str) -> bool:
    """Detect GS Rates Research emails"""
    sender_lower = (sender_email or '').lower()
    name_lower = (sender_display_name or '').lower()
    
    # Check for GS Rates indicators
    if 'george.cole@alerts.publishing.gs.com' in sender_lower:
        return True
    
    if 'gs rates' in name_lower or 'goldman sachs rates' in name_lower:
        return True
    
    # Check for rates content in GS emails
    if ('goldman' in name_lower or '@gs.com' in sender_lower) and \
       ('rates' in title.lower() or 'fixed income' in title.lower() or 'bonds' in title.lower()):
        return True
    
    return False


def extract_clean_text(content_html: str, content_text: str) -> str:
    """Extract clean text from HTML, prioritizing main content"""
    if content_html and len(content_html) > len(content_text):
        soup = BeautifulSoup(content_html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "meta", "link"]):
            script.decompose()
        
        # Get text with proper spacing
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(line for line in lines if line)
        
        return text[:20000]  # Take first 20k chars for comprehensive analysis
    
    return content_text[:20000]


def enrich_gs_rates(title: str, content_text: str, content_html: str, api_key: str) -> Dict:
    """
    GS Rates Rule:
    Deep, detailed analysis in the author's voice
    """
    print("   📊 Processing GS Rates Research...")
    
    # Extract clean text
    full_text = extract_clean_text(content_html, content_text)
    
    if len(full_text) < 500:
        return {
            'smart_summary': f"Rule: GS Rates\n\n# 📊 {title}\n\n[Content too short for analysis]",
            'actors': ['Goldman Sachs'],
            'themes': ['Rates Research'],
            'smart_category': 'RATES_RESEARCH',
            'ai_relevance_score': 7.0
        }
    
    # Create comprehensive prompt for deep analysis
    prompt = f"""You are analyzing a Goldman Sachs Rates Research report. Your task is to write a comprehensive, detailed summary AS IF YOU WERE THE AUTHOR of the report.

TITLE: {title}

CONTENT:
{full_text}

Write a deep, detailed analysis following these guidelines:

1. **Write in the author's voice** - Use "we", "our analysis shows", "we believe", "our view is" etc.
2. **Capture the main thesis comprehensively** - Don't just summarize, explain the reasoning
3. **Include ALL key data points** - rates, spreads, basis points, percentages, dates, levels
4. **Preserve the analytical framework** - how the author thinks about the problem
5. **Include technical details** - curve dynamics, carry, roll, relative value, positioning
6. **Extract specific trade recommendations** if any
7. **Include risk scenarios and caveats** mentioned
8. **Preserve market color and flow information**

Format as:

Rule: GS Rates

# 📊 Goldman Sachs Rates Research
## [Title]

### 🎯 Our Core View
[2-3 sentences capturing the main thesis in first person]

### 📈 The Analysis

**Market Context:**
[Current market situation and why it matters]

**Our Framework:**
[How we're thinking about this - the analytical approach]

**Key Points:**
[Detailed points with ALL specific numbers, levels, dates]
• [Point 1 with data]
• [Point 2 with data]
• [Continue for all major points]

**Technical Dynamics:**
[Curve analysis, carry/roll, spreads, basis, etc.]

**Positioning & Flow:**
[What we're seeing in terms of positioning and flows]

### 💡 Trade Ideas & Recommendations
[Specific recommendations with entry levels, targets, stops if provided]

### ⚠️ Risks to Our View
[Key risks and alternative scenarios]

### 📊 Bottom Line
[Concluding perspective in author's voice - "We believe...", "Our view remains..."]

CRITICAL: 
- Write AS IF you are the Goldman Sachs analyst
- Include EVERY important number, level, and data point
- Preserve technical terminology
- Make it feel like the reader is getting the full depth of the original analysis"""
    
    try:
        # Use Claude 3.7 Sonnet with high tokens for comprehensive analysis
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        summary = message.content[0].text
        
        # Extract key entities for actors
        actors = ['Goldman Sachs', 'GS Rates Research']
        
        # Look for specific names mentioned
        import re
        names = re.findall(r'[A-Z][a-z]+ [A-Z][a-z]+', full_text[:2000])
        for name in names[:3]:
            if len(name.split()) == 2 and name not in actors:
                actors.append(name)
        
        # Extract themes
        themes = ['Rates Research', 'Fixed Income']
        
        # Add specific themes based on content
        if 'fed' in full_text.lower() or 'fomc' in full_text.lower():
            themes.append('Fed Policy')
        if 'treasury' in full_text.lower() or 'treasuries' in full_text.lower():
            themes.append('Treasuries')
        if 'curve' in full_text.lower():
            themes.append('Yield Curve')
        if 'inflation' in full_text.lower():
            themes.append('Inflation')
        if 'swap' in full_text.lower():
            themes.append('Swaps')
        
        return {
            'smart_summary': summary,
            'actors': actors[:7],
            'themes': themes[:7],
            'smart_category': 'RATES_RESEARCH',
            'ai_relevance_score': 9.5
        }
        
    except Exception as e:
        print(f"   ❌ Error in GS Rates enrichment: {e}")
        return {
            'smart_summary': f"Rule: GS Rates\n\n# 📊 {title}\n\n[Processing error: {str(e)}]",
            'actors': ['Goldman Sachs'],
            'themes': ['Rates Research'],
            'smart_category': 'RATES_RESEARCH',
            'ai_relevance_score': 7.0
        }
