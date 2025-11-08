"""
AAA Universal Research Handler v2
Now updates sender tag to detected source
October 2025
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

def is_aaa_research(sender_email: str, title: str, content_html: str) -> bool:
    """Detect AAA research emails - any email with AAA in subject"""
    title_lower = (title or '').lower()
    if 'aaa' in title_lower:
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
            mat = fitz.Matrix(2.0, 2.0)
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


def process_with_source_detection(images: List[Tuple[Image.Image, int]], api_key: str) -> Dict:
    """Process PDF with SOURCE DETECTION + Beautiful Analysis"""
    client = anthropic.Anthropic(api_key=api_key)
    
    # Prepare images
    image_messages = []
    for img, page_num in images[:20]:
        img_b64 = image_to_base64(img)
        image_messages.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": img_b64
            }
        })
    
    # Universal prompt with SOURCE DETECTION
    universal_prompt = """You are analyzing a research document. Provide COMPREHENSIVE, DETAILED analysis.

STEP 1 - IDENTIFY SOURCE:
Look for: logos, headers, footers, email domains (@ubs.com, @gs.com), legal text, format patterns

STEP 2 - COMPREHENSIVE EXTRACTION (Use ALL 16K tokens!):

Extract EVERYTHING important:
• ALL data points, numbers, percentages, basis points
• ALL direct quotes and author's specific phrases
• ALL sections and sub-sections (not just highlights)
• EVERY chart - describe what it shows with specific data
• ALL arguments, reasoning, and implications
• Author's views, interpretations, warnings

TARGET: 3,000-5,000 characters of rich, detailed content

CHART ANALYSIS CRITICAL:
• For EACH chart/graph you see:
  - What type of chart (line, bar, scatter, etc.)
  - What the axes show
  - Key data points visible
  - Trends and patterns
  - What the author emphasizes
• Example: "Chart on page 3 shows 10-year yield curve with inversion at 2-year mark, indicating recession probability of 65% based on historical correlation shown in secondary panel"

Return JSON:
{
  "source_detection": {
    "institution": "Detected name",
    "confidence": "High/Medium/Low",
    "evidence": ["Logo", "Domain", "Format"]
  },
  "document_info": {
    "title": "Full title",
    "authors": ["Names"],
    "date": "Date",
    "document_type": "Economic/Equity/Strategy/Tech"
  },
  "comprehensive_analysis": {
    "key_message": "2-3 sentence thesis",
    "detailed_sections": [
      {
        "topic": "Section name",
        "content": "COMPLETE extraction with ALL data, quotes, reasoning (200-400 chars per section)",
        "data_points": ["Specific numbers from this section"],
        "quotes": ["Direct author phrases"]
      }
    ],
    "charts_detailed": [
      {
        "page": 3,
        "type": "Line graph",
        "description": "Complete description with data points",
        "insight": "What it proves/shows"
      }
    ],
    "all_data": ["Every number mentioned"],
    "implications": "Market/policy impact with author's views",
    "recommendations": "Trade ideas/positioning with levels"
  },
  "metadata": {
    "actors": ["People/Companies/Institutions"],
    "themes": ["Topics covered"]
  }
}

CRITICAL: Use ALL 16K output tokens - aim for maximum comprehensive detail!"""
    
    try:
        # Use Claude 3.7 Sonnet with high tokens
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=16384,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": universal_prompt},
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


def format_universal_output(vision_result: Dict, title: str) -> Dict:
    """Format comprehensive output with ALL details extracted"""
    if not vision_result or "error" in vision_result:
        return {
            'smart_summary': f"Rule: AAA Research\n\n📄 {title}\n\n[Processing error]",
            'actors': ['Unknown'],
            'themes': ['Research'],
            'smart_category': 'RESEARCH',
            'ai_relevance_score': 6.0,
            'detected_source': None
        }
    
    # Extract source
    source = vision_result.get('source_detection', {})
    institution = source.get('institution', 'Unknown')
    confidence = source.get('confidence', 'Low')
    evidence = source.get('evidence', [])
    
    # Extract document info
    doc_info = vision_result.get('document_info', {})
    doc_type = doc_info.get('document_type', 'Research')
    authors = doc_info.get('authors', [])
    date = doc_info.get('date', '')
    doc_title = doc_info.get('title', title)
    
    # Extract COMPREHENSIVE analysis
    analysis = vision_result.get('comprehensive_analysis', vision_result.get('core_analysis', {}))
    key_message = analysis.get('key_message', '')
    detailed_sections = analysis.get('detailed_sections', analysis.get('key_insights', []))
    charts = analysis.get('charts_detailed', analysis.get('charts_analysis', []))
    all_data = analysis.get('all_data', analysis.get('data_points', []))
    implications = analysis.get('implications', '')
    recommendations = analysis.get('recommendations', '')
    
    # Build COMPREHENSIVE summary (3K-5K chars target)
    summary_parts = []
    
    # Header
    summary_parts.append("Rule: AAA Research")
    summary_parts.append("")
    summary_parts.append(f"**Source Detected:** {institution} ({confidence} confidence)")
    if evidence:
        summary_parts.append(f"**Evidence:** {', '.join(evidence[:3])}")
    summary_parts.append("")
    summary_parts.append("─" * 60)
    summary_parts.append("")
    
    # Institution and document header
    summary_parts.append(f"# 🏦 {institution}")
    summary_parts.append(f"## {doc_title}")
    summary_parts.append("")
    if authors:
        summary_parts.append(f"**Authors:** {', '.join(authors[:5])}")
    if date:
        summary_parts.append(f"**Date:** {date}")
    summary_parts.append(f"**Type:** {doc_type}")
    summary_parts.append("")
    summary_parts.append("─" * 60)
    summary_parts.append("")
    
    # Key Message
    if key_message:
        summary_parts.append("### 💡 KEY MESSAGE")
        summary_parts.append("")
        summary_parts.append(key_message)
        summary_parts.append("")
        summary_parts.append("─" * 60)
        summary_parts.append("")
    
    # Comprehensive Insights (THE MAIN CONTENT)
    if detailed_sections:
        summary_parts.append("### 📊 COMPREHENSIVE ANALYSIS")
        summary_parts.append("")
        
        for i, section in enumerate(detailed_sections, 1):
            if isinstance(section, dict):
                topic = section.get('topic', f'Section {i}')
                content = section.get('content', '')
                data_points = section.get('data_points', [])
                quotes = section.get('quotes', [])
                
                summary_parts.append(f"**{i}. {topic}**")
                summary_parts.append("")
                
                # Full content
                if content:
                    summary_parts.append(content)
                    summary_parts.append("")
                
                # Data points if present
                if data_points:
                    for dp in data_points[:5]:
                        summary_parts.append(f"• {dp}")
                    summary_parts.append("")
                
                # Quotes if present
                if quotes:
                    for q in quotes[:3]:
                        summary_parts.append(f'  "{q}"')
                    summary_parts.append("")
                
            elif isinstance(section, str):
                # Simple string format
                summary_parts.append(f"**{i}.** {section}")
                summary_parts.append("")
        
        summary_parts.append("─" * 60)
        summary_parts.append("")
    
    # Chart Analysis (VLM ADVANTAGE!)
    if charts:
        summary_parts.append("### 📈 CHART ANALYSIS")
        summary_parts.append("")
        
        for chart in charts:
            if isinstance(chart, dict):
                page = chart.get('page', '?')
                chart_type = chart.get('type', 'Chart')
                description = chart.get('description', '')
                insight = chart.get('insight', '')
                
                summary_parts.append(f"**Chart (Page {page}):** {description}")
                if insight:
                    summary_parts.append(f"  → {insight}")
                summary_parts.append("")
            elif isinstance(chart, str):
                summary_parts.append(f"• {chart}")
                summary_parts.append("")
        
        summary_parts.append("─" * 60)
        summary_parts.append("")
    
    # Market Implications
    if implications:
        summary_parts.append("### 🌍 MARKET IMPLICATIONS")
        summary_parts.append("")
        summary_parts.append(implications)
        summary_parts.append("")
        summary_parts.append("─" * 60)
        summary_parts.append("")
    
    # Recommendations
    if recommendations:
        summary_parts.append("### 🎯 RECOMMENDATIONS")
        summary_parts.append("")
        if isinstance(recommendations, dict):
            if recommendations.get('immediate_actions'):
                summary_parts.append("**Immediate Actions:**")
                for action in recommendations['immediate_actions']:
                    summary_parts.append(f"• {action}")
                summary_parts.append("")
            if recommendations.get('positioning'):
                summary_parts.append(f"**Positioning:** {recommendations['positioning']}")
                summary_parts.append("")
        else:
            summary_parts.append(recommendations)
            summary_parts.append("")
        
        summary_parts.append("─" * 60)
        summary_parts.append("")
    
    # Data Summary
    if all_data:
        summary_parts.append("### 📊 KEY DATA POINTS")
        summary_parts.append("")
        for dp in all_data[:15]:
            summary_parts.append(f"• {dp}")
        summary_parts.append("")
    
    # Build final summary
    smart_summary = '\n'.join(summary_parts)
    
    # Extract actors and themes
    actors = [institution]
    if authors:
        for author in authors[:3]:
            name = author.split(',')[0].strip()
            if name and name != institution:
                actors.append(name)
    
    themes = [doc_type, f"{institution} Research"]
    metadata = vision_result.get('metadata', {})
    if metadata.get('themes'):
        themes.extend(metadata['themes'][:5])
    
    return {
        'smart_summary': smart_summary,
        'actors': actors[:7],
        'themes': list(set(themes))[:7],
        'smart_category': f"{institution[:10].upper()}_RESEARCH",
        'ai_relevance_score': 9.5 if confidence == 'High' else 8.5,
        'detected_source': institution
    }


def enrich_aaa_research(title: str, content_html: str, api_key: str, pdf_base64: str = None) -> Dict:
    """Main enrichment for AAA rule - returns detected source"""
    print(f"   🔍 AAA UNIVERSAL Processing: {title[:50]}...")
    
    # Extract PDF
    if pdf_base64:
        # PDF provided directly as base64 string
        import base64
        pdf_data = base64.b64decode(pdf_base64)
    else:
        # Try to extract from HTML (legacy method)
        pdf_data = extract_pdf_from_email(content_html)
    
    if not pdf_data:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content_html, 'html.parser')
        text_content = soup.get_text()
        
        if len(text_content) > 1000:
            return {
                'smart_summary': f"Rule: AAA Research\n\n# 📝 {title}\n\n[Text analysis - no PDF found]\n\n{text_content[:2000]}...",
                'actors': ['Unknown Source'],
                'themes': ['Text Analysis'],
                'smart_category': 'RESEARCH',
                'ai_relevance_score': 7.0,
                'detected_source': None
            }
        else:
            return {
                'smart_summary': f"Rule: AAA Research\n\n📄 {title}\n\n[Awaiting PDF attachment]",
                'actors': ['Pending'],
                'themes': ['Pending'],
                'smart_category': 'RESEARCH',
                'ai_relevance_score': 6.0,
                'detected_source': None
            }
    
    print(f"   ✅ PDF found ({len(pdf_data)} bytes)")
    print(f"   🔍 Auto-detecting source institution...")
    
    # Convert to images
    images = pdf_to_images(pdf_data, max_pages=20)
    
    if not images:
        return {
            'smart_summary': f"Rule: AAA Research\n\n📄 {title}\n\n[PDF conversion failed]",
            'actors': ['Error'],
            'themes': ['Error'],
            'smart_category': 'RESEARCH',
            'ai_relevance_score': 6.0,
            'detected_source': None
        }
    
    print(f"   📸 {len(images)} pages ready for analysis")
    
    # Process with source detection
    vision_result = process_with_source_detection(images, api_key)
    
    if vision_result and 'source_detection' in vision_result:
        detected = vision_result['source_detection']['institution']
        confidence = vision_result['source_detection']['confidence']
        print(f"   ✅ SOURCE DETECTED: {detected} ({confidence} confidence)")
    
    # Format with source-specific styling
    result = format_universal_output(vision_result, title)
    
    print(f"   ✨ Generated {len(result['smart_summary'])} char summary")
    
    return result

