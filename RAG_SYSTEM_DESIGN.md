# RAG System Design for EBS SAGE Data

## Executive Summary
Design document for implementing a Retrieval-Augmented Generation (RAG) system using the EBS SAGE NewsFlow data as the knowledge base.

## Current Data Assets

### 1. Data Volume
- **Email Stories**: ~400+ records
- **Tweets**: ~300+ records  
- **Update Frequency**: Real-time (every 15 min for tweets, 2 hours for emails)
- **Languages**: English and Portuguese
- **Time Range**: Continuous from system start date

### 2. Data Structure
- **Structured Fields**: Timestamps, authors, scores, categories
- **Unstructured Text**: News content, tweet text, HTML content
- **Metadata**: AI scores, keywords, language tags
- **Relationships**: Parent-child (digest-story), temporal sequences

## RAG Architecture Proposal

### Phase 1: Data Preparation

#### 1.1 Document Chunking Strategy
```python
chunk_config = {
    'chunk_size': 512,  # tokens
    'chunk_overlap': 50,  # tokens
    'strategy': 'semantic',  # vs. fixed-size
    'preserve_structure': True  # Keep story boundaries
}
```

#### 1.2 Embedding Generation
- **Model**: OpenAI text-embedding-3-small or Cohere embed-v3
- **Dimensions**: 1536 (OpenAI) or 1024 (Cohere)
- **Batch Processing**: 100 documents at a time

#### 1.3 Vector Storage
```python
vector_db_options = {
    'Option 1': 'Pinecone',  # Cloud-native, scalable
    'Option 2': 'Weaviate',  # Self-hosted, flexible
    'Option 3': 'ChromaDB',  # Lightweight, embedded
    'Current': 'LanceDB'     # Already in use, can add vectors
}
```

### Phase 2: Retrieval Pipeline

#### 2.1 Query Processing
```python
def process_query(query: str):
    # 1. Language detection
    language = detect_language(query)
    
    # 2. Query expansion
    expanded = expand_with_synonyms(query, language)
    
    # 3. Hybrid search
    results = {
        'semantic': vector_search(query),
        'keyword': bm25_search(expanded),
        'metadata': filter_search(query)
    }
    
    # 4. Re-ranking
    return rerank_results(results)
```

#### 2.2 Retrieval Strategies
1. **Semantic Search**: Vector similarity
2. **Keyword Search**: BM25 on text fields
3. **Metadata Filtering**: Date ranges, sources, scores
4. **Hybrid Approach**: Combine all three

#### 2.3 Context Window Management
```python
context_config = {
    'max_tokens': 4096,
    'prioritize': 'relevance',  # vs. recency
    'include_metadata': True,
    'deduplication': True
}
```

### Phase 3: Generation Pipeline

#### 3.1 Prompt Template
```python
PROMPT_TEMPLATE = '''
You are a financial news analyst with access to a knowledge base.

Context from NewsFlow Database:
{retrieved_context}

Metadata:
- Sources: {sources}
- Time Range: {time_range}
- AI Scores: {avg_score}

User Question: {query}

Instructions:
1. Answer based on the provided context
2. Cite specific sources when possible
3. Indicate confidence level
4. Preserve original language (PT/EN)

Response:
'''
```

#### 3.2 LLM Integration
```python
llm_config = {
    'model': 'gpt-4-turbo',  # or claude-3-opus
    'temperature': 0.3,
    'max_tokens': 1000,
    'stop_sequences': ['User:', 'Question:'],
    'stream': True
}
```

### Phase 4: Implementation Steps

#### 4.1 Data Export Pipeline
```python
def export_for_rag():
    # 1. Connect to LanceDB
    db = lancedb.connect('/mnt/lancedb_clean')
    table = db.open_table('unified_feed')
    
    # 2. Export to formats
    df = table.to_pandas()
    
    # 3. Prepare documents
    documents = []
    for _, row in df.iterrows():
        doc = {
            'id': row['id'],
            'text': row['content_text'],
            'metadata': {
                'source': row['source'],
                'created_at': row['created_at'],
                'ai_score': row['ai_score'],
                'keywords': row['themes'],
                'language': detect_language(row['content_text'])
            }
        }
        documents.append(doc)
    
    return documents
```

#### 4.2 Embedding Pipeline
```python
def generate_embeddings(documents):
    embeddings = []
    
    for batch in batch_documents(documents, size=100):
        # Generate embeddings
        batch_embeddings = embedding_model.encode(
            [doc['text'] for doc in batch]
        )
        
        # Store with metadata
        for doc, embedding in zip(batch, batch_embeddings):
            embeddings.append({
                'id': doc['id'],
                'embedding': embedding,
                'metadata': doc['metadata']
            })
    
    return embeddings
```

#### 4.3 Query Interface
```python
class RAGQueryEngine:
    def __init__(self, vector_db, llm):
        self.vector_db = vector_db
        self.llm = llm
        
    def query(self, question: str, filters: dict = None):
        # 1. Retrieve relevant documents
        docs = self.retrieve(question, filters)
        
        # 2. Build context
        context = self.build_context(docs)
        
        # 3. Generate response
        response = self.generate(question, context)
        
        return {
            'answer': response,
            'sources': [doc['metadata'] for doc in docs],
            'confidence': self.calculate_confidence(docs)
        }
```

## Use Cases

### 1. Financial Intelligence
- **Query**: "What are the latest developments in the Brazilian market?"
- **RAG Process**: 
  - Retrieve Portuguese content with 'Brasil' or 'Brazil'
  - Filter by recent timestamps
  - Generate bilingual response

### 2. Trend Analysis
- **Query**: "How has sentiment changed about inflation over the past week?"
- **RAG Process**:
  - Time-series retrieval
  - Aggregate AI scores
  - Synthesize trend narrative

### 3. Entity Tracking
- **Query**: "What news about Tesla and Elon Musk?"
- **RAG Process**:
  - Entity extraction
  - Cross-reference tweets and news
  - Compile comprehensive view

## Performance Optimization

### 1. Caching Strategy
```python
cache_config = {
    'embedding_cache': True,  # Cache computed embeddings
    'query_cache': True,      # Cache frequent queries
    'ttl': 3600,             # 1 hour TTL
    'max_size': 1000         # Max cached items
}
```

### 2. Index Optimization
- Pre-compute embeddings during ingestion
- Maintain separate indices for different languages
- Use approximate nearest neighbor (ANN) search

### 3. Incremental Updates
```python
def incremental_update():
    # Only process new records
    last_processed = get_last_processed_id()
    new_records = fetch_records_after(last_processed)
    
    # Generate embeddings for new data
    new_embeddings = generate_embeddings(new_records)
    
    # Update vector store
    vector_store.add(new_embeddings)
    
    # Update checkpoint
    set_last_processed_id(new_records[-1]['id'])
```

## Evaluation Metrics

### 1. Retrieval Quality
- **Precision@K**: Relevant docs in top K
- **Recall@K**: Coverage of relevant docs
- **MRR**: Mean Reciprocal Rank

### 2. Generation Quality
- **Factual Accuracy**: Verification against source
- **Coherence**: Logical flow
- **Citation Accuracy**: Correct source attribution

### 3. System Performance
- **Query Latency**: <2 seconds target
- **Throughput**: 100 QPS minimum
- **Storage Efficiency**: <2x original data size

## Implementation Timeline

### Week 1-2: Data Preparation
- Export current data
- Implement chunking strategy
- Generate initial embeddings

### Week 3-4: Retrieval System
- Set up vector database
- Implement search algorithms
- Build query interface

### Week 5-6: Generation Pipeline
- Integrate LLM
- Design prompt templates
- Implement response generation

### Week 7-8: Testing & Optimization
- Performance tuning
- Quality evaluation
- User interface development

## Cost Estimation

### One-time Costs
- Embedding generation: ~$50 for initial dataset
- Infrastructure setup: ~$200

### Recurring Costs (Monthly)
- Vector database hosting: $50-200
- LLM API calls: $100-500 (usage-dependent)
- Compute resources: $100-300

### Total Estimated Monthly Cost: $250-1000

## Conclusion

The EBS SAGE NewsFlow system provides an excellent foundation for a RAG implementation:
- Rich, multi-source data
- Pre-existing AI enrichment
- Structured metadata
- Real-time updates

The proposed architecture leverages these strengths while adding:
- Semantic search capabilities
- Contextual response generation
- Scalable vector storage
- Intelligent retrieval strategies

This RAG system will transform the NewsFlow data into an intelligent knowledge assistant capable of answering complex queries about financial news and social media trends.

---
*Document Version: 1.0*
*Created: November 8, 2025*
