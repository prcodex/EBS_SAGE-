"""
Rosenberg Early Morning - COMPLETE Topic Extraction
EVERY paragraph/section must be included
"""

def is_rosenberg_deep_research(sender, title, content_text):
    """Detect Rosenberg deep research"""
    is_rosenberg = 'rosenberg' in sender.lower()
    is_early_morning = 'early morning with dave' in title.lower()
    has_key_takeaways = 'key takeaways' in (content_text or '').lower()
    is_substantial = len(content_text or '') > 8000
    
    return is_rosenberg and (is_early_morning or has_key_takeaways or is_substantial)


def enrich_rosenberg_deep_research(title, content_text, api_key):
    """COMPLETE extraction - EVERY topic/section included"""
    from anthropic import Anthropic
    
    prompt = f"""Extract COMPLETE STRUCTURED summary from this Rosenberg "Early Morning with Dave" report.
YOU MUST INCLUDE EVERY SINGLE TOPIC/PARAGRAPH - DO NOT SKIP ANYTHING.

TITLE: {title}

{content_text[:35000]}

MANDATORY STRUCTURE - Include ALL these sections if present in content:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rule: Rosenberg Early Morning\n\n📊 EARLY MORNING WITH DAVE - [Date]
[Clean title]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 KEY TAKEAWAYS
[Extract 3 main themes from "Key Takeaways" section with ALL data]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 YESTERDAY'S MARKETS
[EVERY index, stock, commodity with exact %]
ROSENBERG VIEW: [His quote about the market]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌏 TODAY'S GLOBAL MARKETS
[Asia, Europe, US futures - all exact numbers]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🇬🇧 UK INFLATION - BREAKING LOWER
[EVERY inflation number: headline, core, services, PPI, retail]
[EVERY market move: gilt yields exact bps, GBP, BoE cut odds %]
ROSENBERG VIEW: [Quote about gilt position]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🇯🇵 TAKAICHI TRADE - JAPAN
[Political context, export data, sector winners]
ROSENBERG VIEW: [Quote about looking closely at Japan]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🇨🇦 CANADIAN ECONOMY IN TROUBLE
[Business survey ALL %, household survey, inflation expectations]
[Margin squeeze explanation, tariff timing]
ROSENBERG QUOTE: WSJ reference and "What else does Tiff Macklem need to know?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💥 MARKET BUBBLES - KATIE MARTIN FT
[BOTH direct quotes from Katie Martin article]
ROSENBERG VIEW: [His interpretation]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚨 BEIGE BOOK - NO BLS DATA NEEDED
[Expansion share: 18% exact, down from 43%, from 100%]
[ALL historical comparisons: May 2020, July 2009, bottom 8%, 1-in-10]
[Net diffusion -19pp]
[2022-2023 comparison with $2T stimulus]
[AI spending impact quote]
[ALL the paradox data: consumer sentiment 1%, employment declines, home prices, rents]
ROSENBERG VIEW: "S&P disconnected from real economy" + "sentiment-fueled" quotes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎭 SENTIMENT EXTREMES - EUPHORIA LEVELS
CITI PANIC/EUPHORIA:
[0.71 level, 0.41 threshold, 2021 comparison]
[Peter Boockvar reference, 80% probability quote]

MARKET VANE:
[Pressing 70, 1.2 std dev, high end range]

THE PARADOX:
[Consumer/employment metrics worst 1-2%, equity bullishness top 3%]
[70% of income from jobs quote]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 IS GOLD IN A BUBBLE?
ROSENBERG ANSWER: NO

[Great Reallocation thesis: 70% in 1980 → 24% today]
[Demand 3x supply growth]
[No valuation metric argument]
[Bubble definition: 2 std dev from fundamentals]
[Gold/S&P ratio: -0.5 std dev BELOW average]
[Bull ends when central banks stop buying]
[1999 Washington Agreement reference]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 TREASURY TECHNICALS - GOLDEN CROSS
[10Y fresh 52-week highs, TLT near April high]
[Golden cross: 50-day above 200-day, early October]
[Forward returns exceed norms at 1M, 3M, 6M, 12M]
[Sentiment/technical divergence: 60% lower yield probability]
[Asset allocation: Overweight signal]
ROSENBERG VIEW: "More room to run as markets sniff out lower rates"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 ROSENBERG'S BOTTOM LINE

POSITIONING:
✅ Trimmed gold/silver (prescient before -5-7% drops)
✅ Long UK gilts (paying off with -8bp drop)
✅ Overweight Treasuries (golden cross + weak economy)
⚠️ Cautious equities (euphoria + disconnect)

THESIS:
• Economy weak: 18% expansion, downturn signals, Canada trouble
• Markets euphoric: Citi 0.71, Market Vane 70
• AI masking reality: "Strip out AI, no growth this year"
• Bonds attractive: Technical + fundamental support
• Gold secular bull: Pullback healthy, central bank buying continues
• Equities risky: Valuations + sentiment at extremes

WARNINGS:
• S&P disconnected from real economy
• Tremendous complacency (pervasive belief economy fine)
• Katie Martin: Bubble talk broken confinement
• 80% probability stocks lower after euphoria

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL: Extract EVERY section above. If content discusses it, include it with ALL data points.
Use exact numbers, preserve quotes, include Rosenberg's views.
Length: ~4000-5000 chars to cover everything comprehensively.
"""

    try:
        client = Anthropic(api_key=''YOUR_ANTHROPIC_API_KEY_HERE'')
        
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=8192,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        summary = message.content[0].text
        
        return {
            'smart_summary': summary,
            'actors': ['David Rosenberg'],
            'themes': ['Comprehensive market analysis'],
            'ai_relevance_score': 9.5,
            'category': 'ROSENBERG_DEEP'
        }
        
    except Exception as e:
        print(f"API Error: {e}")
        return None
