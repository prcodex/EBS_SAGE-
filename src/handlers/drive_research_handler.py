"""
Drive Research Handler - Enhanced with Metadata Detection
Auto-detects company, author, and title from PDFs
October 2025
"""

import anthropic
import os
import base64
from typing import Dict, List, Optional, Tuple
import fitz  # PyMuPDF
from PIL import Image
import io

# --- Configuration ---
MODEL = "claude-3-7-sonnet-20250219"
MAX_TOKENS = 8192
PAGES_TO_PROCESS = 20

def extract_pdf_content(pdf_path: str) -> tuple:
    """Extract text and convert pages to images for VLM"""
    
    print(f"   📄 Extracting content from PDF...")
    
    try:
        doc = fitz.open(pdf_path)
        
        # Extract text
        full_text = ""
        for page_num in range(min(PAGES_TO_PROCESS, len(doc))):
            page = doc[page_num]
            full_text += page.get_text()
        
        # Convert pages to images for VLM
        images_base64 = []
        for page_num in range(min(PAGES_TO_PROCESS, len(doc))):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x resolution
            img_bytes = pix.tobytes("png")
            
            # Convert to base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            images_base64.append(img_base64)
        
        doc.close()
        
        print(f"   ✅ Extracted {len(full_text)} chars, {len(images_base64)} pages")
        
        return full_text, images_base64
        
    except Exception as e:
        print(f"   ❌ PDF extraction error: {e}")
        return "", []


def detect_metadata(text_content: str, images_base64: List[str], api_key: str) -> Dict:
    """
    Detect company, author, and title from PDF using Claude VLM
    Returns: {'company': str, 'author': str, 'title': str}
    """
    
    print(f"   🔍 Detecting metadata (company, author, title)...")
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Build content with first few pages for metadata detection
        content = []
        
        # Add first page images (most likely to have metadata)
        for img_base64 in images_base64[:3]:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_base64
                }
            })
        
        # Add text excerpt
        content.append({
            "type": "text",
            "text": f"""Analyze this research document and extract:

1. COMPANY/INSTITUTION: Which bank, research firm, or institution produced this?
   Look for: Logos, headers, footers, email domains, legal text
   Common: UBS, Goldman Sachs, JP Morgan, Morgan Stanley, Bank of America, 
          Citigroup, Wells Fargo, Barclays, Deutsche Bank, Credit Suisse, 
          HSBC, BNP Paribas, Societe Generale, Nomura, etc.

2. AUTHOR(S): Who wrote this document?
   Look for: "By [Name]", "Author:", signatures, contact info
   Extract full name(s)

3. TITLE: What is the document title?
   Look for: Main headline, report title (not section headers)
   Extract the ACTUAL title, not generic descriptions

FIRST PAGE TEXT:
{text_content[:3000]}

Respond in JSON:
{{
    "company": "Company Name",
    "author": "Author Name(s)",
    "title": "Document Title"
}}

If you cannot determine something, use "Unknown" for that field."""
        })
        
        # Quick metadata detection call
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",  # Haiku for quick metadata
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": content
            }]
        )
        
        response_text = message.content[0].text
        
        # Parse JSON
        import json
        import re
        
        # Try to extract JSON
        json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
        if json_match:
            metadata = json.loads(json_match.group(0))
        else:
            metadata = {
                'company': 'Unknown',
                'author': 'Unknown',
                'title': 'Unknown'
            }
        
        print(f"   ✅ Detected:")
        print(f"      Company: {metadata.get('company', 'Unknown')}")
        print(f"      Author: {metadata.get('author', 'Unknown')}")
        print(f"      Title: {metadata.get('title', 'Unknown')[:60]}...")
        
        return metadata
        
    except Exception as e:
        print(f"   ⚠️  Metadata detection error: {e}")
        return {
            'company': 'Unknown',
            'author': 'Unknown',
            'title': 'Unknown'
        }


def enrich_drive_research(
    filename: str,
    pdf_path: str,
    file_metadata: Dict,
    api_key: str
) -> Tuple[Dict, Dict]:
    """
    Enrich Google Drive research document with Early Morning style analysis
    
    Returns tuple: (enrichment_dict, metadata_dict)
    - enrichment_dict: smart_summary, actors, themes, etc.
    - metadata_dict: company, author, title
    """
    
    print(f"   🔬 Processing Drive Research: {filename}...")
    
    # Extract content
    text_content, images_base64 = extract_pdf_content(pdf_path)
    
    if not text_content and not images_base64:
        return {
            'smart_summary': f"Rule: Drive Research\n\n# 📁 {filename}\n\n[Could not extract content from PDF]",
            'actors': ['Drive Research'],
            'themes': ['Research Document'],
            'smart_category': 'RESEARCH',
            'ai_relevance_score': 6.0
        }, {
            'company': 'Unknown',
            'author': 'Unknown',
            'title': filename
        }
    
    # STEP 1: Detect metadata
    metadata = detect_metadata(text_content, images_base64, api_key)
    
    # STEP 2: Create comprehensive analysis
    company = metadata.get('company', 'Unknown')
    author = metadata.get('author', 'Unknown')
    title = metadata.get('title', filename)
    
    # Create VLM analysis prompt
    prompt = f"""You are analyzing a research document from {company}. Provide a COMPREHENSIVE, DETAILED analysis in the style of "Early Morning with Dave" by David Rosenberg.

DOCUMENT METADATA:
   • Company: {company}
   • Author: {author}
   • Title: {title}

Your analysis should be EXHAUSTIVE and DETAILED, covering ALL aspects of the document.

Format your response as:

Rule: Drive Research

# {company.upper()} RESEARCH - {title}
Author: {author} | Pages: {len(images_base64)} | Source: Google Drive
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 KEY TAKEAWAYS

• [Main finding 1 with ALL specific data points, numbers, percentages]
• [Main finding 2 with complete context and implications]
• [Main finding 3 with author's exact views and quotes]
• [Continue for 5-8 key takeaways - extract EVERYTHING important]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📊 [SECTION 1 - Main Topic Identified]

[COMPREHENSIVE analysis of first major section]
• Extract ALL data points with specific numbers
• Include author's exact phrasing and quotes
• Describe ALL charts/graphs you see with VLM
• Note market levels, dates, percentages
• Capture reasoning and logic flow

[2-3 rich paragraphs covering this section completely]

## 🌍 [SECTION 2 - Next Topic]

[Continue exhaustive coverage]
• ALL data and statistics
• Chart observations from VLM
• Author's views and opinions
• Market implications
• Forward-looking statements

[Continue for ALL major sections in the document]

## 💡 [SECTION 3...]

[Keep going through entire document]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔮 OUTLOOK & IMPLICATIONS

[Comprehensive forward-looking analysis]
• What this means for markets
• Policy implications
• Investment considerations
• Risks and opportunities

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 CHART & DATA ANALYSIS (VLM)

[Detailed observations of ALL charts and visualizations you can see]
• Describe trends, patterns, levels
• Note key inflection points
• Explain what data shows

CRITICAL INSTRUCTIONS:
- Analyze BOTH text and images thoroughly
- Extract ALL data points (numbers, percentages, dates, levels)
- Include direct quotes from document
- Describe ALL charts using your vision capabilities
- Aim for 9,000-12,000 characters (comprehensive like Early Morning with Dave)
- Cover EVERY major section, don't skip anything
- Preserve author's voice and views
- Topic-organized with emoji headers"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Build content array with text + images for VLM
        content = []
        
        # Add text context
        if text_content:
            content.append({
                "type": "text",
                "text": f"Document text content (first {len(text_content)} chars):\n\n{text_content[:25000]}"
            })
        
        # Add all page images for VLM analysis
        for i, img_base64 in enumerate(images_base64[:PAGES_TO_PROCESS], 1):
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_base64
                }
            })
        
        # Add the main prompt
        content.append({
            "type": "text",
            "text": prompt
        })
        
        # Call Claude with VLM
        message = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{
                "role": "user",
                "content": content
            }]
        )
        
        summary = message.content[0].text
        
        # Extract actors and themes
        actors = [company] if company != 'Unknown' else ['Drive Research']
        if author != 'Unknown':
            actors.append(author)
        
        themes = ['Research Analysis']
        
        # Basic keyword detection for themes
        content_lower = text_content.lower()
        if 'cpi' in content_lower or 'inflation' in content_lower:
            themes.append('Inflation')
        if 'market' in content_lower or 'trading' in content_lower:
            themes.append('Markets')
        if 'economy' in content_lower or 'economic' in content_lower:
            themes.append('Economics')
        if 'fed' in content_lower or 'central bank' in content_lower:
            themes.append('Monetary Policy')
        
        return {
            'smart_summary': summary,
            'actors': actors[:7],
            'themes': themes[:7],
            'smart_category': 'DRIVE_RESEARCH',
            'ai_relevance_score': 9.0
        }, metadata
        
    except Exception as e:
        print(f"   ❌ Enrichment error: {e}")
        return {
            'smart_summary': f"Rule: Drive Research\n\n# 📁 {filename}\n\n[Processing error: {str(e)}]",
            'actors': ['Drive Research'],
            'themes': ['Research Document'],
            'smart_category': 'RESEARCH',
            'ai_relevance_score': 7.0
        }, metadata
