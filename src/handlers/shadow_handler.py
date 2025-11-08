"""
Shadow Price Macro Handler v2
More detailed economic analysis with comprehensive chart understanding
October 2025
"""

import re
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
import anthropic
import base64
from PIL import Image
import io


def is_shadow_price(sender_email: str, sender_display_name: str, title: str, content_text: str) -> bool:
    """Detect Shadow Price Macro emails from Robin Brooks"""
    sender_lower = (sender_email or '').lower()
    name_lower = (sender_display_name or '').lower()
    
    if 'robinjbrooks@substack.com' in sender_lower:
        return True
    
    if 'shadow price' in name_lower or 'robin brooks' in name_lower:
        return True
    
    if 'shadow price macro' in content_text.lower()[:500]:
        return True
    
    return False


def extract_images_from_html(content_html: str) -> List[Tuple[str, str]]:
    """Extract embedded images from email HTML"""
    images = []
    
    if not content_html:
        return images
    
    soup = BeautifulSoup(content_html, 'html.parser')
    
    img_tags = soup.find_all('img')
    for i, img in enumerate(img_tags):
        src = img.get('src', '')
        if 'data:image' in src:
            try:
                base64_str = src.split(',')[1] if ',' in src else ''
                if base64_str:
                    images.append((f"Chart {i+1}", base64_str))
            except:
                pass
        
        alt_text = img.get('alt', f'Chart {i+1}')
        if alt_text and i < len(images):
            images[i] = (alt_text, images[i][1])
    
    return images


def extract_clean_text(content_html: str, content_text: str) -> str:
    """Extract clean text preserving structure"""
    if content_html and len(content_html) > len(content_text):
        soup = BeautifulSoup(content_html, 'html.parser')
        
        for script in soup(["script", "style", "meta", "link"]):
            script.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(line for line in lines if line)
        
        return text[:25000]  # Increased to 25k chars for more detail
    
    return content_text[:25000]


def analyze_with_vlm(text: str, images: List[Tuple[str, str]], api_key: str) -> str:
    """Use Claude 3.7 Sonnet with VLM for comprehensive analysis"""
    client = anthropic.Anthropic(api_key=api_key)
    
    message_content = []
    
    # Enhanced prompt for more detailed analysis
    prompt = f"""You are analyzing an economic analysis from Robin J Brooks' Shadow Price Macro newsletter. 
Your task is to write a COMPREHENSIVE, DETAILED analysis AS IF YOU ARE Robin Brooks, using "I" and maintaining his analytical style.

TEXT CONTENT:
{text}

CHARTS IN THIS ANALYSIS: {len(images)} charts detected

Write an EXTENSIVE, DETAILED analysis following Robin's style. DO NOT BE BRIEF - provide rich, comprehensive coverage:

CRITICAL INSTRUCTIONS:
1. **Length**: Aim for 8,000-12,000 characters (not brief summaries)
2. **Write in first person throughout** - "I argue", "I've found", "my analysis", "I believe"
3. **Reference charts extensively** - "The first chart reveals...", "As the second chart demonstrates...", "The Venn diagram makes clear..."
4. **Include ALL data points with context** - Don't just mention numbers, explain what they mean
5. **Deep analytical reasoning** - Explain WHY things matter, not just what they are
6. **Multiple paragraphs per section** - Each point needs full development
7. **Rich policy discussion** - Elaborate on recommendations and implications
8. **Historical context** - Reference past events and comparisons
9. **Detailed counterfactuals** - Fully develop alternative scenarios

Format as:

Rule: Shadow

# 📊 Shadow Price Macro
## [Title]

### 📈 The Core Thesis
[3-4 sentences capturing the main argument in first person, setting up the entire analysis]

### 📊 Chart Analysis & Data Deep Dive

**What the first chart reveals:**
[2-3 paragraphs analyzing the first chart in detail]
The chart above clearly demonstrates... [specific description of what's shown]
What's particularly striking is... [key insight from the data]
The numbers tell a compelling story: [list specific data points with context]
• [Detailed data point 1 with explanation of significance]
• [Detailed data point 2 with what it means for the analysis]
• [Detailed data point 3 with implications]

**The second visualization's critical insights:**
[2-3 paragraphs on the second chart if present]
As the Venn diagram illustrates... [describe overlaps and gaps]
The magnitude of the disconnect becomes apparent when we see...
This visualization is crucial because it shows...

**Hidden patterns in the data:**
[1-2 paragraphs on less obvious insights]
What many observers miss is...
Digging deeper into the numbers reveals...

### 🌍 Geopolitical & Economic Analysis

**The transatlantic rift explained:**
[3-4 paragraphs of detailed analysis]
I've been tracking this divergence for months, and what we're seeing is...
The EU's approach, while admirable in its scope, suffers from...
The UK has taken a middle ground that...
The US position, particularly under [administration], reflects...

**Why sanctions effectiveness varies:**
[2-3 paragraphs on enforcement mechanisms]
The fundamental issue with sanctions enforcement is...
My research with Ben Harris has shown definitively that...
The "fear factor" I often discuss operates through...

**Market dynamics and price impacts:**
[2-3 paragraphs on economic effects]
The Urals oil price discount currently sits at...
What traders are telling me is...
The shadow fleet has evolved in ways that...

### 💡 Strategic Policy Recommendations

**Immediate actions required:**
[2-3 paragraphs of specific recommendations]
European policymakers must understand that...
I propose the following concrete steps:
• [Detailed recommendation 1 with implementation path]
• [Detailed recommendation 2 with expected outcomes]
• [Detailed recommendation 3 with timeline]
• [Detailed recommendation 4 with stakeholder analysis]

**The "whatever it takes" moment:**
[2 paragraphs on critical junctures]
We are at a pivotal moment where...
History will judge harshly if...

**Secondary measures and contingencies:**
[1-2 paragraphs on additional steps]
Beyond the primary sanctions, we should consider...
If the first approach fails, the backup plan should be...

### 🔮 The Counterfactual Analysis

**What could have been:**
[2-3 paragraphs developing alternative history]
Imagine if, immediately after February 2022, the West had...
The economic impact would have been devastating for Russia:...
We can estimate based on historical precedents that...

**Lessons from missed opportunities:**
[1-2 paragraphs on what we can learn]
The failure to act decisively teaches us...
Going forward, this means...

### 📈 Technical Market Analysis

**Current positioning and flows:**
[2 paragraphs on market technicals]
Looking at current positioning data...
The flow patterns I'm observing suggest...

**Price targets and scenarios:**
[1-2 paragraphs on specific levels]
If sanctions are fully enforced, I expect...
The downside scenario would see...

### 🌐 Broader Implications

**For global energy markets:**
[2 paragraphs on wider effects]
The ripple effects extend far beyond Russia...
Asian buyers, particularly [countries], are...

**For the future of economic statecraft:**
[1-2 paragraphs on long-term implications]
This episode is rewriting the playbook for...
Future conflicts will likely see...

### 📊 The Bottom Line

[3-4 paragraphs of concluding analysis in first person]
My fundamental view is that...
The data overwhelmingly supports...
I remain convinced that...
The path forward requires...

---
*Note: Analysis references [X] charts that illustrate these dynamics. The data speaks volumes about the urgency of coordinated action.*

REMEMBER: 
- This should be 8,000-12,000 characters of rich, detailed analysis
- Write entirely as Robin Brooks in first person
- Reference charts as if the reader can see them
- Include ALL specific numbers with context
- Develop each point fully - no brief summaries
- Maintain analytical rigor while being accessible"""
    
    message_content.append({
        "type": "text",
        "text": prompt
    })
    
    # Add detected images for VLM analysis
    for chart_name, img_base64 in images[:4]:  # Increased to 4 charts
        try:
            message_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_base64
                }
            })
        except:
            pass
    
    try:
        # Use Claude 3.7 Sonnet with increased tokens for detailed output
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=12000,  # Increased from 8192
            messages=[
                {
                    "role": "user",
                    "content": message_content
                }
            ]
        )
        
        return message.content[0].text
        
    except Exception as e:
        print(f"   ❌ VLM analysis error: {e}")
        return analyze_text_only(text, api_key)


def analyze_text_only(text: str, api_key: str) -> str:
    """Fallback text-only analysis if VLM fails"""
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""Analyze this Shadow Price Macro content AS Robin Brooks. 
    
PROVIDE COMPREHENSIVE, DETAILED ANALYSIS (8,000-12,000 characters):

{text}

Write entirely in first person ("I argue", "my analysis", "I've found") following the Rule: Shadow format.
Include ALL data points with extensive context and explanation.
Develop each section fully - this should be a detailed analytical piece, not a summary.
Reference charts as if visible ("the chart above shows", "as illustrated").
Provide rich policy recommendations and counterfactual analysis."""
    
    try:
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=12000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    except:
        return f"Rule: Shadow\n\n# 📊 Shadow Price Macro\n\n[Processing error]"


def enrich_shadow_price(title: str, content_text: str, content_html: str, api_key: str) -> Dict:
    """
    Shadow Rule v2:
    Comprehensive economic analysis with detailed chart understanding
    """
    print("   📊 Processing Shadow Price Macro with VLM (detailed mode)...")
    
    # Extract clean text
    full_text = extract_clean_text(content_html, content_text)
    
    if len(full_text) < 500:
        return {
            'smart_summary': f"Rule: Shadow\n\n# 📊 {title}\n\n[Content too short for analysis]",
            'actors': ['Robin Brooks'],
            'themes': ['Economic Analysis'],
            'smart_category': 'ECONOMIC_ANALYSIS',
            'ai_relevance_score': 7.0
        }
    
    # Extract images/charts if present
    images = extract_images_from_html(content_html)
    print(f"   📈 Found {len(images)} charts for detailed VLM analysis")
    
    # Analyze with VLM for comprehensive output
    summary = analyze_with_vlm(full_text, images, api_key)
    
    # Extract comprehensive actors list
    actors = ['Robin Brooks', 'Shadow Price Macro']
    
    # Extended entity extraction
    entities_to_find = ['Putin', 'Biden', 'Trump', 'EU', 'UK', 'US', 
                       'Rosneft', 'Lukoil', 'Russia', 'Ukraine', 'China',
                       'India', 'Urals', 'OPEC', 'Fed', 'ECB', 'Xi',
                       'Zelensky', 'NATO', 'G7', 'IMF', 'World Bank']
    
    for entity in entities_to_find:
        if entity in full_text and entity not in actors:
            actors.append(entity)
    
    # Extract comprehensive themes
    themes = ['Sanctions', 'Economic Analysis']
    
    theme_keywords = {
        'Oil Markets': ['oil', 'urals', 'energy', 'crude', 'petroleum'],
        'Geopolitics': ['sanctions', 'war', 'invasion', 'conflict'],
        'Policy Analysis': ['policy', 'embargo', 'tariffs', 'enforcement'],
        'Financial Markets': ['price', 'market', 'trading', 'flows'],
        'Shadow Fleet': ['shadow fleet', 'tankers', 'vessels', 'shipping'],
        'Central Banks': ['rates', 'monetary', 'inflation', 'ruble'],
        'Trade': ['exports', 'imports', 'trade', 'commerce']
    }
    
    for theme, keywords in theme_keywords.items():
        if any(kw in full_text.lower() for kw in keywords):
            themes.append(theme)
    
    return {
        'smart_summary': summary,
        'actors': actors[:10],  # Increased from 7
        'themes': themes[:10],   # Increased from 7
        'smart_category': 'ECONOMIC_ANALYSIS',
        'ai_relevance_score': 9.5
    }
