#!/usr/bin/env python3
"""
OPTIMIZED NewsBreif Handler - Extract EVERYTHING in ONE Claude call
- Story title & details
- Story-specific keywords (4-6 per story)
- Story-specific AI score (0-10 per story)
- Links

Result: 50% cost savings, better quality (each story rated individually)
"""

from anthropic import Anthropic

def enrich_newsbrief_optimized(title, content_text, sender_tag, api_key):
    """
    Extract all story data in ONE Claude call
    Returns stories with keywords and AI scores embedded
    """
    
    print(f"   🔗 OPTIMIZED NewsBrief ({sender_tag})")
    
    # Detect language
    is_portuguese = any(word in content_text.lower()[:500] for word in [
        'notícias', 'brasil', 'governo', 'mercado', 'economia', 'empresas'
    ])
    
    if is_portuguese:
        prompt = """
Extraia 6-12 notícias principais deste briefing.

Para CADA notícia, forneça em JSON:
{
  "stories": [
    {
      "title": "Título da notícia",
      "bullets": [
        "Detalhe específico com palavras do texto",
        "Detalhe com números/nomes/dados específicos"
      ],
      "link": "URL se mencionado no conteúdo, ou vazio",
      "keywords": ["palavra1", "palavra2", "palavra3", "palavra4"],
      "ai_score": 8
    }
  ]
}

KEYWORDS: 4-6 palavras-chave ESPECÍFICAS em PORTUGUÊS (empresas, pessoas, conceitos, locais)
- Exclua termos genéricos: "Breaking News", "Análise", "Mercado", "Notícias"
- Foque no ASSUNTO da notícia

AI_SCORE: Avalie a importância de 0-10
- 9-10: Notícia crítica (decisões de política, grandes movimentos de mercado)
- 7-8: Importante (dados econômicos, earnings, M&A)
- 5-6: Relevante (análises, opiniões)
- 3-4: Menor importância
- 1-2: Trivial

Conteúdo do newsletter:
"""
    else:
        prompt = """
Extract 6-12 main news stories from this briefing.

For EACH story, provide in JSON:
{
  "stories": [
    {
      "title": "Story title",
      "bullets": [
        "Specific detail with words from text",
        "Detail with numbers/names/specific data"
      ],
      "link": "URL if mentioned in content, or empty",
      "keywords": ["keyword1", "keyword2", "keyword3", "keyword4"],
      "ai_score": 8
    }
  ]
}

KEYWORDS: 4-6 SPECIFIC keywords in ENGLISH (companies, people, concepts, locations)
- Exclude generic terms: "Breaking News", "Analysis", "Market", "News"
- Focus on the SUBJECT of the story

AI_SCORE: Rate importance 0-10
- 9-10: Critical news (policy decisions, major market moves)
- 7-8: Important (economic data, earnings, M&A)
- 5-6: Relevant (analysis, opinions)
- 3-4: Minor importance
- 1-2: Trivial

Newsletter content:
"""
    
    # Add content (truncate to 10K for efficiency)
    prompt += f"\n{content_text[:10000]}"
    
    try:
        # Call Claude
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result_text = response.content[0].text
        
        # Parse JSON
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            data = json.loads(json_match.group(0))
            
            print(f"   ✅ Extracted {len(data.get('stories', []))} stories with keywords & scores")
            
            return {
                'stories': data.get('stories', []),
                'rule': 'newsbrief_optimized'
            }
        else:
            print(f"   ❌ No JSON found in response")
            return {'stories': [], 'rule': 'newsbrief_optimized'}
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")
        return {'stories': [], 'rule': 'newsbrief_optimized'}
