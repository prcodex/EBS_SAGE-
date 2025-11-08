# EBS SAGE NewsFlow - How It Works (Summary for RAG Planning)

## Quick Overview
EBS SAGE is an automated news intelligence system that aggregates, enriches, and serves financial news and social media content through an AI-powered pipeline.

## Data Flow in 5 Steps

### Step 1: Data Ingestion
- **Email**: Gmail IMAP → Newsletter parsing → Story extraction
- **Twitter**: API calls → Tweet fetching → Metadata extraction
- **Schedule**: Emails every 2 hours, Tweets every 15 minutes

### Step 2: AI Enrichment
- Content sent to Anthropic Claude API
- Extracts keywords in original language (EN/PT)
- Scores relevance (0-10 scale)
- Classifies junk content (score ≤ 3)

### Step 3: Storage
- LanceDB vector database on EBS volume
- Unified schema for all content types
- Deduplication at insertion time
- ID tracking prevents reprocessing

### Step 4: API Service
- Flask web server on port 8545
- RESTful JSON endpoints
- Real-time data serving
- Timezone conversion (UTC → Brazil)

### Step 5: Display
- Web interface with live updates
- Filtered views (email/tweet/junk)
- Chronological sorting
- Multilingual support

## Key Components

### 1. NewsBreif Processor ()
- Fetches emails from configured Gmail account
- Parses HTML/text to extract individual stories
- Enriches each story with AI
- Stores in database with metadata

### 2. Twitter Fetcher ()
- Calls Twitter API v2
- Fetches from curated list
- Enriches tweets with keywords
- Tracks engagement metrics

### 3. Flask API ()
- Serves data via HTTP endpoints
- Handles date parsing and sorting
- Formats responses for web consumption
- Manages database connections

### 4. AI Handler ()
- Interfaces with Anthropic Claude
- Bilingual keyword extraction
- Content scoring algorithm
- Language detection

## Data Schema



## For RAG Implementation

### Current Data Assets
- **Volume**: ~700+ documents (growing continuously)
- **Languages**: English (60%), Portuguese (40%)
- **Update Rate**: ~100 new documents daily
- **Rich Metadata**: Timestamps, scores, keywords, sources

### RAG Opportunities

#### 1. Knowledge Base
- Pre-enriched with keywords and topics
- Quality scores for relevance filtering
- Temporal data for trend analysis
- Multilingual content

#### 2. Vector Search Potential
- Content already in LanceDB (vector-ready)
- Structured metadata for filtering
- Natural language text for embeddings
- Existing deduplication

#### 3. Use Cases
- **Q&A System**: "What's the latest on Brazilian markets?"
- **Trend Analysis**: "How has inflation sentiment changed?"
- **Entity Tracking**: "News about Tesla this week?"
- **Cross-lingual**: "Notícias sobre Petrobras?"

### Technical Advantages for RAG

1. **Clean Data Pipeline**
   - Automated ingestion
   - Consistent schema
   - Quality filtering
   - No manual cleanup needed

2. **AI-Ready**
   - Pre-computed keywords
   - Relevance scores
   - Language tags
   - Clean text extraction

3. **Scalable Architecture**
   - Modular components
   - API-based access
   - Real-time updates
   - Cloud-native storage

### RAG Implementation Path

#### Phase 1: Embedding Generation


#### Phase 2: Retrieval System


#### Phase 3: Generation Layer


## Why This System is Perfect for RAG

1. **Data Quality**: Pre-processed, cleaned, and enriched
2. **Structure**: Consistent schema across all sources
3. **Metadata**: Rich context for filtering and ranking
4. **Updates**: Continuous fresh content
5. **Bilingual**: Natural multilingual support
6. **Scoring**: Built-in relevance metrics
7. **API Ready**: Easy integration points
8. **Scalable**: Designed for growth

## Next Steps for RAG

1. **Generate Embeddings**: Use OpenAI or Cohere for vector representations
2. **Enhance Storage**: Add vector index to LanceDB
3. **Build Retriever**: Implement semantic search
4. **Create Interface**: Chat-based Q&A system
5. **Evaluate Quality**: Measure retrieval accuracy
6. **Deploy Service**: Containerize and scale

## Expected Outcomes

With RAG implementation, the system will enable:
- Natural language questions about news/markets
- Intelligent summarization across sources
- Trend identification and analysis
- Multi-language conversational interface
- Real-time intelligence briefings
- Automated report generation

---
*This summary provides the essential information needed to plan a RAG system using EBS SAGE data*
*Created: November 8, 2025*
