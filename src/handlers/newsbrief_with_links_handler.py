#!/usr/bin/env python3
"""
Fixed NewsBrief handler with proper response parsing
"""

import os
from typing import Dict
import re
from anthropic import Anthropic

def enrich_newsbrief_with_links(title, content_text, sender_tag, api_key):
    """
    NewsBrief with clickable links - FIXED VERSION
    """
    
    print(f"   🔗 NewsBrief WITH LINKS ({sender_tag})")
    
    # Determine language
    portuguese_senders = ['Estadão', 'Folha', 'O Globo']
    is_portuguese = sender_tag in portuguese_senders
    
    # Build prompt
    if is_portuguese:
        prompt = """
        Extraia 6-12 notícias principais do briefing.
        
        Para CADA notícia, forneça:
        1. Título da notícia (destaque, importante)
        2. Detalhes chave (2-4 bullets com palavras/frases/números específicos extraídos do texto)
        3. Se houver um link/URL mencionado para esta notícia no conteúdo, inclua-o
        
        Formate EXATAMENTE assim:
        
        <strong style="font-size: 18px; display: block; margin-top: 12px; margin-bottom: 2px;">1. [Título da Notícia]</strong>
        • [Detalhe com palavras específicas do texto]
        • [Detalhe com números/nomes/dados específicos]
        🔗 <a href="[URL]" target="_blank" style="color: #1DA1F2; text-decoration: none;">Leia mais</a>
        
        CRÍTICO: Responda em português
        
        Conteúdo do newsletter:
        """
    else:
        prompt = """
        Extract 6-12 main news stories from this briefing.
        
        For EACH story, provide:
        1. Story title (highlight, important)
        2. Key details (2-4 bullets with specific words/phrases/numbers extracted from text)
        3. If there's a link/URL mentioned for this story in the content, include it
        
        Format EXACTLY like this:
        
        <strong style="font-size: 18px; display: block; margin-top: 12px; margin-bottom: 2px;">1. [Story Title]</strong>
        • [Detail with specific words from text]
        • [Detail with numbers/names/specific data]
        🔗 <a href="[URL]" target="_blank" style="color: #1DA1F2; text-decoration: none;">Read more</a>
        
        Newsletter content:
        """
    
    # Add content
    prompt += f"\n{content_text[:10000]}"
    
    # Call API
    try:
        client = Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=4096,
            temperature=0,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Parse response properly
        result = ""
        if hasattr(message, 'content'):
            if isinstance(message.content, list) and len(message.content) > 0:
                # Get the text from the first content block
                result = message.content[0].text if hasattr(message.content[0], 'text') else str(message.content[0])
            elif isinstance(message.content, str):
                result = message.content
            else:
                result = str(message.content)
        
        # Return structured response
        return {
            'smart_summary': result,
            'rule': 'newsbrief_with_links'
        }
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            'summary': '',
            'rule': 'newsbrief_with_links'
        }
