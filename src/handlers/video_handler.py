"""
Video Transcript Handler
Transforms YouTube transcripts into detailed, fluid explanations
October 2025
"""

import re
from typing import Dict, Optional
from bs4 import BeautifulSoup
import anthropic


def is_video_transcript(sender_email: str, sender_display_name: str, title: str, content_text: str) -> bool:
    """Detect video transcript emails"""
    title_lower = (title or '').lower()
    
    # Check if subject starts with VIDEO
    if title_lower.startswith('video'):
        return True
    
    # Also check for common video transcript indicators
    if any(indicator in title_lower for indicator in ['youtube', 'transcript', 'video:']):
        return True
    
    # Check content for transcript markers
    content_lower = (content_text or '')[:1000].lower()
    if any(marker in content_lower for marker in ['transcript', 'youtube', '[music]', '[applause]', 'speaker:']):
        return True
    
    return False


def extract_clean_transcript(content_html: str, content_text: str) -> str:
    """Extract and clean transcript text"""
    # Prefer HTML if available for better structure preservation
    if content_html and len(content_html) > len(content_text):
        soup = BeautifulSoup(content_html, 'html.parser')
        
        # Remove script and style elements
        for element in soup(["script", "style", "meta", "link"]):
            element.decompose()
        
        # Get text with proper spacing
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up excessive whitespace while preserving paragraphs
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(line for line in lines if line)
        
        return text[:30000]  # Take first 30k chars for comprehensive analysis
    
    return content_text[:30000]


def clean_transcript_artifacts(text: str) -> str:
    """Remove common transcript artifacts"""
    # Remove timestamps like [00:15:32]
    text = re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', text)
    text = re.sub(r'\[\d{1,2}:\d{2}\]', '', text)
    
    # Remove sound effects and stage directions but keep them noted
    sound_effects = re.findall(r'\[([^\]]+)\]', text.lower())
    text = re.sub(r'\[[^\]]+\]', '', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Fix common transcript issues
    text = text.replace(' ,', ',').replace(' .', '.')
    
    return text.strip(), sound_effects


def identify_speakers(text: str) -> list:
    """Identify speakers in the transcript"""
    speakers = []
    
    # Common patterns for speakers
    patterns = [
        r'^([A-Z][A-Za-z\s]+):',  # Name: at start of line
        r'\n([A-Z][A-Za-z\s]+):',  # Name: after newline
        r'Speaker ([A-Z\d]+):',     # Speaker 1:, Speaker A:
        r'([A-Z][a-z]+ [A-Z][a-z]+):',  # Full names
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match not in speakers and len(match) < 30:
                speakers.append(match.strip())
    
    return list(set(speakers))[:10]  # Return up to 10 unique speakers


def enrich_video_transcript(title: str, content_text: str, content_html: str, api_key: str) -> Dict:
    """
    Video Rule:
    Transform video transcripts into detailed, fluid explanations
    """
    print("   📹 Processing video transcript...")
    
    # Extract and clean transcript
    raw_transcript = extract_clean_transcript(content_html, content_text)
    cleaned_text, effects = clean_transcript_artifacts(raw_transcript)
    
    if len(cleaned_text) < 200:
        return {
            'smart_summary': f"Rule: Video\n\n# 📹 {title}\n\n[Transcript too short for analysis]",
            'actors': ['Video Analysis'],
            'themes': ['Transcript'],
            'smart_category': 'VIDEO_ANALYSIS',
            'ai_relevance_score': 6.0
        }
    
    # Identify speakers if present
    speakers = identify_speakers(raw_transcript)
    
    # Create comprehensive analysis prompt
    prompt = f"""You are analyzing a video transcript. Your task is to transform this raw transcript into a DETAILED, FLUID, and COMPREHENSIVE explanation of the discussion, ideas, and thesis presented.

TITLE: {title}

TRANSCRIPT:
{cleaned_text}

{f"IDENTIFIED SPEAKERS: {', '.join(speakers)}" if speakers else ""}
{f"NOTED EFFECTS: {', '.join(set(effects[:10]))}" if effects else ""}

Create a detailed, flowing analysis following these guidelines:

1. **Write in clear, flowing paragraphs** - Not bullet points, but connected narrative
2. **Explain the main thesis comprehensively** - What's the core argument or message?
3. **Detail the rational ideas presented** - Break down the logic and reasoning
4. **Preserve important quotes** - Include key statements in context
5. **Structure the flow of discussion** - How do ideas build on each other?
6. **Identify and explain key concepts** - Define terms, explain frameworks
7. **Note areas of emphasis or repetition** - What points are stressed?
8. **Capture the tone and style** - Is it academic, conversational, persuasive?

Format as:

Rule: Video

# 📹 Video Analysis
## {title}

### 🎯 Core Thesis & Overview
[2-3 flowing paragraphs explaining the main argument and what this video is about]

The central thesis of this discussion revolves around... [explain main idea]

What makes this perspective particularly noteworthy is... [why it matters]

The speakers approach this topic by... [methodology or structure]

### 💡 Key Ideas & Rational Arguments

**The Primary Argument**
[2-3 paragraphs of detailed explanation]

The discussion begins with the fundamental premise that... [detailed explanation of opening ideas]. This foundation is critical because... [explain why]. The speakers elaborate on this by presenting evidence that... [describe supporting points].

As the conversation develops, we see a sophisticated argument emerge regarding... [next major point]. The rational basis for this claim rests on... [explain logic]. What's particularly compelling is how they connect... [show relationships between ideas].

**Secondary Themes & Supporting Ideas**
[2-3 paragraphs exploring supporting arguments]

Beyond the central thesis, several important supporting ideas emerge. First, there's the notion that... [explain first supporting idea in detail]. This connects to the broader argument by... [show connection].

Additionally, the speakers explore... [second supporting theme]. The evidence presented includes... [specific examples or data]. This reinforces the main thesis by demonstrating... [explain reinforcement].

### 📊 Evidence & Examples

[2-3 paragraphs detailing specific evidence, examples, or case studies mentioned]

The speakers substantiate their arguments with several compelling examples. Most notably... [describe key example in detail]. This case illustrates... [explain what it demonstrates].

Further evidence is presented through... [additional examples]. The cumulative effect of these examples is to... [explain overall impact].

### 🔍 Critical Analysis & Nuances

[2-3 paragraphs exploring complexities, counterarguments, or nuanced points]

The discussion doesn't shy away from complexity. One particularly nuanced aspect involves... [explain complex point]. The speakers acknowledge that... [describe acknowledgment of limitations or counterpoints].

There's also careful attention paid to... [another nuanced aspect]. This shows intellectual honesty in... [explain how].

### 🎭 Rhetorical Approach & Presentation Style

[1-2 paragraphs on how the ideas are presented]

The presentation style is notably... [describe tone and approach]. The speakers employ... [rhetorical techniques]. This approach is effective because... [explain effectiveness].

{f"The interaction between {speakers[0] if speakers else 'the speakers'} creates..." if speakers else "The flow of ideas demonstrates..."}

### 📈 Implications & Takeaways

[2-3 paragraphs on what this means and why it matters]

The implications of this discussion are far-reaching. If we accept the central thesis, it follows that... [explore implications]. This would fundamentally change how we think about... [broader impact].

Moreover, the practical applications include... [specific applications]. For practitioners or those interested in this field, the key takeaway is... [actionable insights].

### 🔮 Future Directions & Open Questions

[1-2 paragraphs on what remains to be explored]

While the discussion is comprehensive, it also raises important questions for future exploration. Particularly intriguing is... [identify open question]. This suggests that... [potential future direction].

The speakers hint at... [future possibilities or next steps]. This opens up exciting avenues for... [describe opportunities].

### 📝 Summary Synthesis

[2-3 concluding paragraphs that tie everything together]

In synthesis, this video presents a compelling case for... [restate main thesis with full context]. Through careful argumentation and evidence, the speakers demonstrate... [key achievements of the discussion].

The strength of the presentation lies in... [identify strengths]. While there are areas that could benefit from further exploration, particularly... [note any gaps constructively], the overall contribution is significant.

Ultimately, this discussion advances our understanding of... [final assessment of contribution]. For anyone interested in... [target audience], this video offers... [value proposition].

CRITICAL INSTRUCTIONS:
- Create FLOWING TEXT, not bullet lists
- Write detailed PARAGRAPHS that connect ideas
- Explain concepts THOROUGHLY
- Maintain logical flow between sections
- Include specific examples and quotes when notable
- Aim for 6,000-10,000 characters of rich analysis"""
    
    try:
        # Use Claude 3.7 Sonnet for comprehensive analysis
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        summary = message.content[0].text
        
        # Extract actors (speakers, mentioned people, organizations)
        actors = ['Video Analysis'] + speakers[:5]
        
        # Extract themes based on content
        themes = ['Video Transcript', 'Discussion Analysis']
        
        # Add specific themes based on keywords
        theme_keywords = {
            'Technology': ['technology', 'ai', 'software', 'digital', 'innovation'],
            'Economics': ['economy', 'market', 'finance', 'money', 'trade'],
            'Politics': ['policy', 'government', 'political', 'election', 'democracy'],
            'Science': ['research', 'study', 'data', 'experiment', 'hypothesis'],
            'Philosophy': ['philosophy', 'ethics', 'moral', 'meaning', 'existence'],
            'Business': ['business', 'company', 'startup', 'entrepreneur', 'strategy'],
            'Education': ['education', 'learning', 'teaching', 'knowledge', 'academic'],
            'Health': ['health', 'medical', 'wellness', 'disease', 'treatment']
        }
        
        content_lower = cleaned_text.lower()
        for theme, keywords in theme_keywords.items():
            if any(kw in content_lower for kw in keywords):
                themes.append(theme)
        
        return {
            'smart_summary': summary,
            'actors': actors[:7],
            'themes': themes[:7],
            'smart_category': 'VIDEO_ANALYSIS',
            'ai_relevance_score': 9.0
        }
        
    except Exception as e:
        print(f"   ❌ Error in video analysis: {e}")
        return {
            'smart_summary': f"Rule: Video\n\n# 📹 {title}\n\n[Processing error: {str(e)}]",
            'actors': ['Video Analysis'],
            'themes': ['Transcript'],
            'smart_category': 'VIDEO_ANALYSIS',
            'ai_relevance_score': 6.0
        }
