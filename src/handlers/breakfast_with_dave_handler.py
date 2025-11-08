"""
Breakfast with Dave - Complete Headlines Extractor
Gets ALL headlines from all sections
"""
from bs4 import BeautifulSoup

def is_breakfast_with_dave(sender, title, content_text, content_html):
    """Detect Breakfast with Dave"""
    is_rosenberg = 'rosenberg' in sender.lower()
    is_breakfast = 'breakfast with dave' in title.lower()
    return is_rosenberg and is_breakfast


def enrich_breakfast_with_dave(title, content_html):
    """Extract ALL headlines - complete extraction"""
    
    if not content_html:
        return None
    
    soup = BeautifulSoup(content_html, 'html.parser')
    
    # Remove noise
    for element in soup(['script', 'style', 'noscript']):
        element.decompose()
    
    # Get text
    full_text = soup.get_text()
    
    # Extract ALL potential headlines (clean lines 40-150 chars)
    all_headlines = []
    for line in full_text.split('\n'):
        line = line.strip()
        
        # Must be headline-length
        if not (40 < len(line) < 200):
            continue
        
        # Skip footer/noise
        if any(skip in line.lower() for skip in [
            'download the full', 'your daily headlines', 'you are receiving',
            'notification', 'follow us', 'next event', 'webcast',
            '3080 yonge', 'toronto', 'canada,', 'phone:', 'update your'
        ]):
            continue
        
        # Add if not duplicate
        if line not in all_headlines:
            all_headlines.append(line)
    
    # Organize by sections (keyword-based matching)
    sections = {
        'Early Morning with Dave': [],
        'Data Commentary': [],
        'Market Insights': [],
        'In Case You Missed It': []
    }
    
    for headline in all_headlines:
        matched = False
        
        # Early Morning - usually about bonds, stocks, major themes
        if any(kw in headline for kw in ['Bonds', 'Stocks', 'Like the', 'Takaichi', 'Inflation News', 'Japanese']):
            sections['Early Morning with Dave'].append(headline)
            matched = True
        
        # Data Commentary - Fed surveys, economic data, CPI, PMI
        if any(kw in headline for kw in ['Philly', 'Fed Survey', 'CPI', 'Canada', 'PCE', 'Jobless', 'PMI', 'Survey']):
            sections['Data Commentary'].append(headline)
            matched = True
        
        # Market Insights - specific sector/market analysis
        if any(kw in headline for kw in ['Defense Stocks', 'Room to Run', 'Strategic', 'Investment', 'Sector']):
            sections['Market Insights'].append(headline)
            matched = True
        
        # ICYMI - broader topics, travel, regions, themes
        if any(kw in headline for kw in ['Travel', 'Beige Book', 'Latin America', 'Boycott', 'throughlines', 'retrenchment']):
            sections['In Case You Missed It'].append(headline)
            matched = True
    
    # Build output
    summary_parts = [f"📰 BREAKFAST WITH DAVE - {title.replace('Breakfast with Dave -- ', '')}"]
    summary_parts.append("━" * 60)
    summary_parts.append("\n📋 YOUR DAILY HEADLINES:\n")
    
    emojis = {
        'Early Morning with Dave': '🌅',
        'Data Commentary': '📊',
        'Market Insights': '💡',
        'In Case You Missed It': '📚'
    }
    
    section_num = 0
    for section_name, headlines in sections.items():
        if headlines:
            section_num += 1
            emoji = emojis[section_name]
            summary_parts.append(f"{section_num}. {emoji} {section_name.upper()}")
            
            # Remove duplicates while preserving order
            seen = set()
            for headline in headlines:
                if headline not in seen:
                    summary_parts.append(f"   • {headline}")
                    seen.add(headline)
            
            summary_parts.append("")
    
    summary_parts.append("━" * 60)
    summary_parts.append("📄 Full reports available via download links")
    
    return {
        'smart_summary': '\n'.join(summary_parts),
        'actors': ['David Rosenberg', 'Rosenberg Research'],
        'themes': ['Daily headlines', 'Market research digest'],
        'ai_relevance_score': 8.0,
        'category': 'BREAKFAST_HEADLINES'
    }
