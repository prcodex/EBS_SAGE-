"""
Macro Charts & ChartStorm Handler - VLM Chart Analysis
Analyzes each chart individually with detailed insights
Supports: Macro Charts, ChartStorm (Callum Thomas)
October 2025
"""

from typing import Dict, List
from bs4 import BeautifulSoup
import anthropic
import re
import base64
import requests
from io import BytesIO
from PIL import Image


def is_macro_charts(sender_email: str, sender_display_name: str, title: str, content_text: str) -> bool:
    """Detect Macro Charts and ChartStorm emails"""
    sender_lower = (sender_email or '').lower()
    name_lower = (sender_display_name or '').lower()
    title_lower = (title or '').lower()
    
    indicators = [
        'macrocharts@substack.com' in sender_lower,
        'chartstorm@substack.com' in sender_lower,
        'macro charts' in name_lower,
        'chartstorm' in name_lower,
        '#chartstorm' in title_lower
    ]
    
    return any(indicators)


def extract_images_from_html(content_html: str) -> List[str]:
    """Extract all image URLs from HTML"""
    soup = BeautifulSoup(content_html, 'html.parser')
    
    image_urls = []
    
    # Find all img tags
    for img in soup.find_all('img'):
        src = img.get('src', '')
        
        # Skip tiny images (logos, icons)
        width = img.get('width', '')
        height = img.get('height', '')
        
        # Only get substantial images
        if src and ('http' in src):
            # Skip very small images
            try:
                if width and int(width) < 100:
                    continue
                if height and int(height) < 100:
                    continue
            except:
                pass
            
            image_urls.append(src)
    
    return image_urls


def download_and_encode_image(url: str) -> str:
    """Download image and convert to base64"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Convert to PIL Image and resize if needed
            img = Image.open(BytesIO(response.content))
            
            # Resize if too large (Claude has limits)
            max_size = 1568
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert to PNG bytes
            buffer = BytesIO()
            img.convert('RGB').save(buffer, format='PNG')
            img_bytes = buffer.getvalue()
            
            # Encode to base64
            return base64.b64encode(img_bytes).decode('utf-8')
    except Exception as e:
        print(f"   ⚠️  Failed to download image: {e}")
    
    return None


def enrich_macro_charts(title: str, content_text: str, content_html: str, api_key: str) -> Dict:
    """
    Charts Rule:
    VLM analysis of each chart with detailed insights
    """
    print(f"   📊 MACRO CHARTS Processing: {title[:50]}...")
    
    # Extract image URLs
    image_urls = extract_images_from_html(content_html)
    
    print(f"   Found {len(image_urls)} chart images")
    
    if len(image_urls) == 0:
        return {
            'smart_summary': f"Rule: Charts\n\n# 📊 Macro Charts\n## {title}\n\n[No charts found in email]",
            'actors': ['Macro Charts'],
            'themes': ['Economic Charts'],
            'smart_category': 'CHART_ANALYSIS',
            'ai_relevance_score': 6.0
        }
    
    # Download and encode images (limit to first 10)
    chart_images = []
    for i, url in enumerate(image_urls[:10], 1):
        print(f"   📥 Downloading chart {i}/{min(len(image_urls), 10)}...")
        img_b64 = download_and_encode_image(url)
        if img_b64:
            chart_images.append({
                'number': i,
                'url': url,
                'base64': img_b64
            })
    
    print(f"   ✅ Downloaded {len(chart_images)} charts")
    
    if len(chart_images) == 0:
        return {
            'smart_summary': f"Rule: Charts\n\n# 📊 Macro Charts\n## {title}\n\n[Could not download chart images]",
            'actors': ['Macro Charts'],
            'themes': ['Economic Charts'],
            'smart_category': 'CHART_ANALYSIS',
            'ai_relevance_score': 6.0
        }
    
    # Prepare images for Claude Vision
    image_messages = []
    for chart in chart_images:
        image_messages.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": chart['base64']
            }
        })
    
    # Create comprehensive prompt for chart analysis
    prompt = f"""You are analyzing charts from a financial newsletter.

TITLE: {title}

NUMBER OF CHARTS: {len(chart_images)}

For EACH chart, provide detailed analysis.

OUTPUT FORMAT (CRITICAL - Start with this EXACT line):

Rule: Charts

# 📊 Macro Charts
## {title}

────────────────────────────────────────────────────────────

### Chart 1: [Descriptive name]

**What It Shows:**
[Chart type, axes, data, time period]

**Key Data Points:**
• Current level: [number]
• Change: [%/points]
• [Other data]

**Analysis:**
[Trend, patterns, momentum]

**Implications:**
[Market/economic implications]

────────────────────────────────────────────────────────────

[Repeat for each chart]

────────────────────────────────────────────────────────────

### 💡 Overall Market Implications

[Synthesis of all charts]

CRITICAL: Start your response with EXACTLY "Rule: Charts" on the first line."""
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Use Claude 3.7 Sonnet with VLM
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=8192,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *image_messages
                ]
            }]
        )
        
        response_text = response.content[0].text
        
        # Ensure it starts with Rule: Charts
        if not response_text.startswith('Rule: Charts'):
            response_text = 'Rule: Charts\n\n' + response_text
        
        summary = response_text
        actors = ['Macro Charts']
        themes = ['Economic Charts', 'Market Analysis']
        
        print(f"   ✅ Analyzed {len(chart_images)} charts - {len(summary)} chars")
        
        return {
            'smart_summary': summary,
            'actors': actors[:7],
            'themes': themes[:7],
            'smart_category': 'CHART_ANALYSIS',
            'ai_relevance_score': 9.0
        }
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            'smart_summary': f"Rule: Charts\n\n# 📊 Macro Charts\n## {title}\n\n[Processing error: {str(e)}]",
            'actors': ['Macro Charts'],
            'themes': ['Economic Charts'],
            'smart_category': 'CHART_ANALYSIS',
            'ai_relevance_score': 6.0
        }
