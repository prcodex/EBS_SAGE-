# EBS SAGE System - NewsFlow Intelligence Platform

## Overview
EBS SAGE is a real-time news and social media aggregation system that fetches, processes, enriches, and displays content from multiple sources with AI-powered analysis.

## System Architecture

### Core Components

#### 1. Data Sources
- **Email (NewsBreif)**: Gmail IMAP integration fetching newsletter digests
- **Twitter/X**: API integration fetching tweets from curated lists
- **Supported Publishers**: Reuters, Bloomberg, WSJ, Financial Times, Barron's, Folha de S.Paulo, O Globo, Estadão

#### 2. Data Processing Pipeline



#### 3. Storage Layer
- **Database**: LanceDB (vector database)
- **Location**: EBS Volume at 
- **Table**: 
- **Format**: Columnar storage with Apache Arrow

#### 4. AI Enrichment
- **Provider**: Anthropic Claude (claude-3-haiku)
- **Functions**:
  - Keyword extraction (bilingual: EN/PT)
  - Content scoring (0-10 relevance scale)
  - Junk classification (score ≤ 3 = junk)
  - Language detection

#### 5. Web Interface
- **Framework**: Flask
- **Port**: 8545
- **Endpoints**:
  -  - Main interface
  -  - JSON data endpoint
  -  - Statistics

## Data Flow

### NewsBreif Email Processing
1. **Fetch**: Connect to Gmail via IMAP
2. **Filter**: Check sender against allowlist
3. **Parse**: Extract stories from HTML/text
4. **Enrich**: AI extracts keywords and scores
5. **Store**: Insert into LanceDB with deduplication
6. **Track**: Update processed IDs

### Twitter Processing
1. **Fetch**: Call Twitter API for list tweets
2. **Parse**: Extract text, media, metrics
3. **Enrich**: AI analysis for keywords/score
4. **Classify**: Mark low-score as junk
5. **Store**: Insert with tweet metadata

## Key Features

### 1. Duplicate Prevention
- ID tracking in 
- Pre-insertion duplicate checking
- Unique constraint on record IDs

### 2. Multilingual Support
- Portuguese content preserved
- Keywords extracted in original language
- No automatic translation

### 3. Time Management
- UTC storage with 'Z' suffix
- Brazil timezone display (UTC-3)
- Proper datetime parsing

### 4. Automated Processing
- Cron jobs for scheduled fetching
- 2-hour NewsBreif cycle
- 15-minute Twitter updates
- Automatic junk classification

## Database Schema



## Cron Schedule



## Installation Requirements

Usage: flask [OPTIONS] COMMAND [ARGS]...

  A general utility script for Flask applications.

  An application to load must be given with the '--app' option, 'FLASK_APP'
  environment variable, or with a 'wsgi.py' or 'app.py' file in the current
  directory.

Options:
  -e, --env-file FILE   Load environment variables from this file, taking
                        precedence over those set by '.env' and '.flaskenv'.
                        Variables set directly in the environment take highest
                        precedence. python-dotenv must be installed.
  -A, --app IMPORT      The Flask application or factory function to load, in
                        the form 'module:name'. Module can be a dotted import
                        or file path. Name is not required if it is 'app',
                        'application', 'create_app', or 'make_app', and can be
                        'name(args)' to pass arguments.
  --debug / --no-debug  Set debug mode.
  --version             Show the Flask version.
  --help                Show this message and exit.

Commands:
  routes  Show the routes for the app.
  run     Run a development server.
  shell   Run a shell in the app context.

## Environment Variables



## Performance Metrics

- **Capacity**: ~1000+ records without performance degradation
- **Processing Time**: ~2-3 seconds per email digest
- **API Response**: <100ms for feed endpoint
- **Storage**: ~1MB per 500 records

## Error Handling

- Graceful API failures with retry logic
- Duplicate prevention at multiple levels
- Transaction rollback on errors
- Comprehensive logging to 

## Security Considerations

- API keys stored as environment variables
- No sensitive data in logs
- Sanitized configuration exports
- Read-only Gmail access
- Rate limiting on API calls

## Future Enhancements

1. **RAG System Integration**
   - Vector embeddings for semantic search
   - Document chunking strategies
   - Retrieval optimization

2. **Advanced Analytics**
   - Trend detection
   - Entity relationship mapping
   - Sentiment analysis

3. **Scalability**
   - Distributed processing
   - Cache layer implementation
   - Database partitioning

## Maintenance

### Daily Tasks
- Monitor log files for errors
- Check duplicate count
- Verify cron execution

### Weekly Tasks
- Database optimization
- Clear old logs
- Update API keys if needed

### Monthly Tasks
- Full system backup
- Performance analysis
- Security audit

---
*Last Updated: November 8, 2025*
*Version: 1.0.0*
