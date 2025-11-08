#!/usr/bin/env python3
"""
Tweet-specific keyword handler - Bilingual (EN/PT)
Extracts keywords only, respects original language
"""

import anthropic
import json
import os
import logging

logger = logging.getLogger(__name__)

def extract_tweet_keywords(tweet_text, api_key, exclusions):
    """
    Extract keywords from tweet in original language (EN or PT)
    
    Args:
        tweet_text: The tweet text
        api_key: Anthropic API key
        exclusions: Dictionary of exclusion terms
        
    Returns:
        dict: {'keywords': [...], 'language': 'en/pt', 'score': 0-10}
    """
    
    # Flatten exclusions into single list
    all_exclusions = []
    for category in exclusions.values():
        all_exclusions.extend(category)
    
    exclusion_str = ", ".join(all_exclusions[:20])  # Sample for prompt
    
    prompt = f"""Analyze this tweet and extract keywords.

CRITICAL LANGUAGE RULE:
- If the tweet is in Portuguese → Return keywords in PORTUGUESE
- If the tweet is in English → Return keywords in ENGLISH  
- DO NOT translate keywords to another language!

Tweet: "{tweet_text}"

Extract 4-6 keywords focusing on:
- Companies/Organizations (Tesla, Petrobras, Goldman Sachs, Congresso, etc.)
- People (Jerome Powell, Lula, Trump, Elon Musk, etc.)
- Topics (Inflation/Inflação, Tariffs/Tarifas, Trade/Comércio, etc.)
- Locations (Brazil/Brasil, China, USA, Washington, São Paulo, etc.)
- Concepts (Monetary Policy/Política Monetária, AI/IA, etc.)

EXCLUDE generic terms like:
- Source names (CNN, Bloomberg, FT, InfoMoney)
- Generic words (Breaking News, Notícias, Update, Análise)
- Examples to exclude: {exclusion_str}...

Return ONLY valid JSON (no markdown):
{{
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4"],
  "language": "en" or "pt",
  "score": 0-10
}}

Score 0-10 based on financial/market relevance."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=200,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response - robust JSON extraction
        ai_text = response.content[0].text.strip()
        
        # Remove markdown code blocks
        if '```json' in ai_text:
            ai_text = ai_text.split('```json')[1].split('```')[0]
        elif '```' in ai_text:
            ai_text = ai_text.split('```')[1].split('```')[0]
        
        # Extract just the JSON object
        import re
        json_match = re.search(r'\{[^{}]*"keywords"[^{}]*\}', ai_text, re.DOTALL)
        if json_match:
            ai_text = json_match.group(0)
        
        # Clean up
        ai_text = ai_text.strip()
        
        result = json.loads(ai_text)
        
        # Validate
        if 'keywords' not in result:
            result['keywords'] = []
        if 'language' not in result:
            result['language'] = 'en'
        if 'score' not in result:
            result['score'] = 5
        
        # Post-process: filter out any remaining exclusions
        filtered_keywords = []
        for kw in result['keywords']:
            if kw.lower() not in [e.lower() for e in all_exclusions]:
                filtered_keywords.append(kw)
        
        result['keywords'] = filtered_keywords[:6]  # Max 6
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}")
        return {
            'keywords': [],
            'language': 'en',
            'score': 0
        }
