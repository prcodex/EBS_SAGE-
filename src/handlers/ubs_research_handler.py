"""
UBS Adaptive Research Handler v3.0 - Beautiful Edition
Enhanced aesthetics with clean, organized output
October 2025 - Using Claude 3.7 Sonnet with expanded tokens
"""

import os
import re
import base64
import json
from typing import Dict, List, Optional, Tuple
import anthropic
from PIL import Image
import io
import fitz  # PyMuPDF

def is_ubs_research(sender_email: str, title: str, content_html: str) -> bool:
    """Detect UBS research emails from pribeirojr@me.com"""
    sender_lower = (sender_email or '').lower()
    title_lower = (title or '').lower()
    
    if 'pribeirojr@me.com' not in sender_lower:
        return False
    
    if 'ubs' in title_lower:
        return True
    
    return False


def extract_pdf_from_email(content_html: str) -> Optional[bytes]:
    """Extract PDF attachment from email HTML"""
    pdf_pattern = r'data:application/pdf;base64,([A-Za-z0-9+/=]+)'
    matches = re.findall(pdf_pattern, content_html)
    
    if matches:
        try:
            pdf_data = base64.b64decode(matches[0])
            return pdf_data
        except Exception as e:
            print(f"Error decoding PDF: {e}")
    
    return None


def pdf_to_images(pdf_data: bytes, max_pages: int = 20) -> List[Tuple[Image.Image, int]]:
    """Convert PDF pages to images for Claude Vision"""
    images = []
    
    try:
        pdf_doc = fitz.open(stream=pdf_data, filetype="pdf")
        
        for page_num in range(min(len(pdf_doc), max_pages)):
            page = pdf_doc[page_num]
            mat = fitz.Matrix(2.0, 2.0)  # 2x resolution
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.pil_tobytes(format="PNG")
            img = Image.open(io.BytesIO(img_data))
            images.append((img, page_num + 1))
        
        pdf_doc.close()
        
    except Exception as e:
        print(f"Error converting PDF: {e}")
    
    return images


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def process_with_beautiful_claude(images: List[Tuple[Image.Image, int]], api_key: str) -> Dict:
    """
    Process with Claude 3.7 - MAXIMUM TOKENS & BEAUTIFUL OUTPUT
    """
    client = anthropic.Anthropic(api_key=api_key)
    
    # Prepare images
    image_messages = []
    for img, page_num in images[:15]:  # Increased to 15 pages
        img_b64 = image_to_base64(img)
        image_messages.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": img_b64
            }
        })
    
    # Enhanced prompt for BEAUTIFUL, ORGANIZED output
    beautiful_prompt = """You are an elite financial analyst creating a BEAUTIFUL, CLEAN research summary.

AESTHETIC REQUIREMENTS:
- Use GENEROUS spacing between sections
- Create VISUAL hierarchy with clear headers
- Keep paragraphs SHORT and punchy (2-3 sentences max)
- Use bullet points sparingly but effectively
- Include WHITESPACE for breathing room

DOCUMENT ANALYSIS:

1. **IDENTIFY & ADAPT** (5 seconds)
   Detect the document type and adjust your entire approach:
   - Economic/Macro → Policy focus, indicators, forecasts
   - Equity Research → Valuations, ratings, catalysts
   - Strategy → Positioning, allocations, themes
   - Technical → Levels, signals, probabilities
   - Commentary → Narrative, context, sentiment

2. **EXTRACT ELEGANTLY**
   Pull out the essence without clutter:
   - Core thesis (1-2 sentences MAX)
   - Key insights (3-5 MAJOR points only)
   - Critical data (numbers that MATTER)
   - Visual findings (what charts REVEAL)

3. **BEAUTIFUL STRUCTURE**
   Create output that's a pleasure to read:
   - Clear visual breaks between sections
   - Logical flow from thesis to conclusion
   - Highlight what's TRULY important
   - Remove redundancy and noise

Return this BEAUTIFUL JSON:
{
  "document_type": "Type detected",
  "elegance": {
    "title": "Clean, professional title",
    "author": "Name(s) - Title",
    "date": "Date",
    "institution": "UBS or specific division"
  },
  "core_thesis": "The ONE key message in 1-2 powerful sentences",
  "key_insights": [
    {
      "point": "Major insight",
      "evidence": "Supporting data/fact",
      "importance": "Why this matters"
    }
  ],
  "visual_intelligence": [
    {
      "chart": "What it shows",
      "finding": "Key takeaway",
      "data": "Specific numbers if critical"
    }
  ],
  "market_impact": {
    "immediate": "What happens now",
    "medium_term": "3-6 month view",
    "risks": "What could go wrong"
  },
  "action_items": ["Clear, specific recommendations"],
  "memorable_quotes": ["Distinctive phrases worth preserving"],
  "bottom_line": "The SO WHAT - why reader should care"
}"""
    
    try:
        # Use Claude 3.7 Sonnet with MAXIMUM tokens
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",  # Latest Feb 2025 model
            max_tokens=16384,  # DOUBLED from 8192 to 16384!
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": beautiful_prompt},
                        *image_messages
                    ]
                }
            ]
        )
        
        response_text = response.content[0].text
        
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = {"error": "Could not parse response"}
        
        return result
        
    except Exception as e:
        print(f"Error with Claude API: {e}")
        return None


def format_beautiful_output(vision_result: Dict, title: str) -> Dict:
    """
    Create BEAUTIFUL, ORGANIZED output with proper spacing
    """
    if not vision_result or "error" in vision_result:
        return {
            'smart_summary': f"Rule: UBS Research\n\n📄 {title}\n\n[Processing error]",
            'actors': ['UBS'],
            'themes': ['Research'],
            'smart_category': 'RESEARCH',
            'ai_relevance_score': 8.0
        }
    
    # Extract elegantly
    doc_type = vision_result.get('document_type', 'Research')
    elegance = vision_result.get('elegance', {})
    thesis = vision_result.get('core_thesis', '')
    insights = vision_result.get('key_insights', [])
    visuals = vision_result.get('visual_intelligence', [])
    impact = vision_result.get('market_impact', {})
    actions = vision_result.get('action_items', [])
    quotes = vision_result.get('memorable_quotes', [])
    bottom_line = vision_result.get('bottom_line', '')
    
    # Build BEAUTIFUL summary with generous spacing
    summary_parts = [
        "Rule: UBS Research",
        "",
        "─" * 60,
        ""
    ]
    
    # Elegant header
    icon = {
        'Economic': '📊', 'Equity': '📈', 'Strategy': '🎯',
        'Technical': '📉', 'Commentary': '💬', 'Policy': '🏛️'
    }.get(doc_type.split('/')[0], '📄')
    
    summary_parts.extend([
        f"# {icon} {elegance.get('institution', 'UBS')}",
        f"## {elegance.get('title', title)}",
        "",
        f"**Author:** {elegance.get('author', 'UBS Research')}",
        f"**Date:** {elegance.get('date', '')}",
        f"**Type:** {doc_type}",
        "",
        "─" * 60,
        ""
    ])
    
    # Core thesis - the heart of the message
    if thesis:
        summary_parts.extend([
            "### 🎯 THE KEY MESSAGE",
            "",
            f"*{thesis}*",
            "",
            "─" * 40,
            ""
        ])
    
    # Key insights - clean and organized
    if insights:
        summary_parts.extend([
            "### 💡 CRITICAL INSIGHTS",
            ""
        ])
        
        for i, insight in enumerate(insights[:5], 1):
            summary_parts.append(f"**{i}.** {insight.get('point', '')}")
            
            if insight.get('evidence'):
                summary_parts.append(f"   → {insight['evidence']}")
            
            if insight.get('importance'):
                summary_parts.append(f"   ⚡ {insight['importance']}")
            
            summary_parts.append("")  # Space between insights
        
        summary_parts.extend(["─" * 40, ""])
    
    # Visual intelligence - what the charts reveal
    if visuals:
        summary_parts.extend([
            "### 📊 CHART ANALYSIS",
            ""
        ])
        
        for visual in visuals[:3]:
            chart = visual.get('chart', 'Chart')
            finding = visual.get('finding', '')
            data = visual.get('data', '')
            
            summary_parts.append(f"**{chart}**")
            if finding:
                summary_parts.append(f"• {finding}")
            if data:
                summary_parts.append(f"• Data: {data}")
            summary_parts.append("")
        
        summary_parts.extend(["─" * 40, ""])
    
    # Market impact - what it means
    if impact:
        summary_parts.extend([
            "### 🌍 MARKET IMPLICATIONS",
            ""
        ])
        
        if impact.get('immediate'):
            summary_parts.extend([
                f"**Now:** {impact['immediate']}",
                ""
            ])
        
        if impact.get('medium_term'):
            summary_parts.extend([
                f"**3-6 Months:** {impact['medium_term']}",
                ""
            ])
        
        if impact.get('risks'):
            summary_parts.extend([
                f"**Risks:** {impact['risks']}",
                ""
            ])
        
        summary_parts.extend(["─" * 40, ""])
    
    # Action items - what to do
    if actions:
        summary_parts.extend([
            "### ✅ RECOMMENDATIONS",
            ""
        ])
        
        for action in actions[:4]:
            summary_parts.append(f"• {action}")
        
        summary_parts.extend(["", "─" * 40, ""])
    
    # Bottom line - why it matters
    if bottom_line:
        summary_parts.extend([
            "### 💭 BOTTOM LINE",
            "",
            f"**{bottom_line}**",
            ""
        ])
    
    # Memorable quotes
    if quotes:
        summary_parts.extend([
            "─" * 40,
            "",
            "*Notable quotes:* " + " | ".join(f'"{q}"' for q in quotes[:2]),
            ""
        ])
    
    # Join with proper spacing
    smart_summary = '\n'.join(summary_parts)
    
    # Extract clean actors and themes
    actors = ['UBS']
    if elegance.get('author'):
        author_name = elegance['author'].split(',')[0].split('-')[0].strip()
        if author_name and author_name != 'UBS':
            actors.append(author_name)
    
    # Dynamic themes based on content
    themes = [doc_type]
    content_lower = smart_summary.lower()
    
    theme_keywords = {
        'inflation': 'Inflation', 'cpi': 'CPI Analysis',
        'earnings': 'Earnings', 'valuation': 'Valuation',
        'fed': 'Federal Reserve', 'rates': 'Interest Rates',
        'technology': 'Technology', 'ai': 'Artificial Intelligence',
        'equity': 'Equities', 'growth': 'Growth'
    }
    
    for keyword, theme in theme_keywords.items():
        if keyword in content_lower and theme not in themes and len(themes) < 7:
            themes.append(theme)
    
    return {
        'smart_summary': smart_summary,
        'actors': actors[:7],
        'themes': themes[:7],
        'smart_category': doc_type.upper()[:20],
        'ai_relevance_score': 9.5
    }


def enrich_ubs_research(title: str, content_html: str, api_key: str) -> Dict:
    """Main enrichment with BEAUTIFUL output"""
    print(f"   🎨 BEAUTIFUL Processing: {title[:50]}...")
    
    # Extract PDF
    pdf_data = extract_pdf_from_email(content_html)
    
    if not pdf_data:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content_html, 'html.parser')
        text_content = soup.get_text()
        
        if len(text_content) > 1000:
            return {
                'smart_summary': f"Rule: UBS Research\n\n# 📝 UBS - {title}\n\n{text_content[:2000]}...",
                'actors': ['UBS'],
                'themes': ['Text Analysis'],
                'smart_category': 'RESEARCH',
                'ai_relevance_score': 8.0
            }
        else:
            return {
                'smart_summary': f"Rule: UBS Research\n\n📄 {title}\n\n[Awaiting content]",
                'actors': ['UBS'],
                'themes': ['Pending'],
                'smart_category': 'RESEARCH',
                'ai_relevance_score': 7.0
            }
    
    print(f"   ✅ PDF found ({len(pdf_data)} bytes)")
    
    # Convert to images
    images = pdf_to_images(pdf_data, max_pages=15)  # More pages
    
    if not images:
        return {
            'smart_summary': f"Rule: UBS Research\n\n📄 {title}\n\n[Conversion failed]",
            'actors': ['UBS'],
            'themes': ['Error'],
            'smart_category': 'RESEARCH',
            'ai_relevance_score': 7.0
        }
    
    print(f"   📸 {len(images)} pages ready")
    print(f"   🎨 Creating BEAUTIFUL summary with Claude 3.7...")
    
    # Process with BEAUTIFUL Claude
    vision_result = process_with_beautiful_claude(images, api_key)
    
    # Format beautifully
    result = format_beautiful_output(vision_result, title)
    
    print(f"   ✨ Generated beautiful {len(result['smart_summary'])} char summary")
    
    return result


if __name__ == "__main__":
    print("UBS Research Handler v3.0 - BEAUTIFUL Edition")
    print("✨ Features:")
    print("  • Claude 3.7 Sonnet (Latest - Feb 2025)")
    print("  • 16,384 max tokens (2x previous)")
    print("  • Beautiful, organized output")
    print("  • Clean visual hierarchy")
    print("  • Generous spacing")

