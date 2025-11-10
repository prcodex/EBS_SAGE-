# Gmail-Style Analysis Batch Specification

## Overview
Third analysis batch that fetches emails matching tagging rules, stores complete email content for Gmail-style rendering, and applies deep AI enrichment through tag-handler mappings.

## Architecture Design

### 1. Data Flow
```
Email Source → Tagging Rules Filter → Full Content Storage → Handler Enrichment → Gmail-Style Display
```

### 2. Key Components

#### Batch Processor (`analysis_email_batch.py`)
- **Schedule**: Every hour (configurable)
- **Time Window**: Last 24 hours
- **Functions**:
  1. Query `unified_feed` for emails matching tagging rules
  2. Fetch complete email content (headers, HTML, attachments info)
  3. Store in new `email_analysis` table
  4. Apply tag-handler mapping for enrichment
  5. Update with deep AI analysis

#### Storage Table (`email_analysis`)
```python
schema = {
    # Identity
    'id': str,                      # Unique analysis ID
    'original_id': str,              # Link to unified_feed
    'message_id': str,               # Gmail message ID
    
    # Email Headers
    'from_address': str,             # Full sender email
    'from_name': str,                # Sender display name
    'to_addresses': str,             # Recipients (JSON)
    'cc_addresses': str,             # CC recipients (JSON)
    'subject': str,                  # Full subject line
    'date_sent': str,                # Original send date
    'date_received': str,            # Receipt timestamp
    
    # Content
    'content_html': str,             # Full HTML body
    'content_text': str,             # Plain text version
    'attachments': str,              # Attachment metadata (JSON)
    'embedded_images': str,          # Inline images (JSON)
    
    # Classification
    'detected_tag': str,             # From tagging rules
    'handler_used': str,             # Applied handler
    'sender_category': str,          # Sender classification
    
    # AI Analysis
    'executive_summary': str,        # One-paragraph summary
    'key_points': str,               # Bullet points (JSON)
    'actors': str,                   # Identified entities (JSON)
    'themes': str,                   # Main topics (JSON)
    'sentiment': str,                # Positive/Negative/Neutral
    'urgency_score': float,          # 0-10 urgency rating
    'relevance_score': float,        # 0-10 relevance rating
    
    # Enrichment
    'extracted_links': str,          # All URLs (JSON)
    'mentioned_tickers': str,        # Stock symbols (JSON)
    'action_items': str,             # Required actions (JSON)
    'related_items': str,            # Similar content IDs (JSON)
    
    # Metadata
    'created_at': str,               # Analysis timestamp
    'updated_at': str,               # Last modification
    'is_expanded': bool,             # UI state tracker
    'user_notes': str,               # User annotations
}
```

### 3. Gmail-Style Interface (`sage_email_analysis.py`)

#### Port: 8547

#### UI Components:

##### Email List View
```html
<div class="email-item">
    <div class="sender-avatar">📧</div>
    <div class="email-summary">
        <div class="sender-line">
            <span class="sender-name">Bloomberg</span>
            <span class="timestamp">2:34 PM</span>
        </div>
        <div class="subject-line">Markets Update: Fed Decision Impact</div>
        <div class="preview-text">Federal Reserve announces rate decision...</div>
        <div class="ai-badges">
            <span class="urgency-high">🔴 High Priority</span>
            <span class="relevance">⭐ 9/10</span>
            <span class="handler">🤖 Bloomberg Handler</span>
        </div>
    </div>
</div>
```

##### Expanded Email View (Gmail-style)
```html
<div class="email-expanded">
    <!-- Header Section -->
    <div class="email-header">
        <h2 class="subject">Markets Update: Fed Decision Impact</h2>
        <div class="sender-details">
            <img src="avatar.png" class="sender-avatar-large">
            <div>
                <div class="sender-name">Bloomberg News</div>
                <div class="sender-email">alerts@bloomberg.com</div>
            </div>
            <div class="email-actions">
                <button>Reply</button>
                <button>Forward</button>
                <button>Archive</button>
            </div>
        </div>
        <div class="email-metadata">
            <span>To: me</span>
            <span>Date: Nov 10, 2025, 2:34 PM</span>
        </div>
    </div>
    
    <!-- AI Analysis Panel -->
    <div class="ai-analysis-panel">
        <h3>🤖 AI Analysis</h3>
        <div class="executive-summary">
            <strong>Summary:</strong> Federal Reserve maintains rates...
        </div>
        <div class="key-points">
            <strong>Key Points:</strong>
            <ul>
                <li>Fed holds rates at 5.25-5.50%</li>
                <li>Markets rally on dovish tone</li>
                <li>Next meeting December 15</li>
            </ul>
        </div>
        <div class="entities">
            <strong>Mentioned:</strong>
            <span class="tag">Jerome Powell</span>
            <span class="tag">Federal Reserve</span>
            <span class="tag">S&P 500</span>
        </div>
    </div>
    
    <!-- Original Email Content -->
    <div class="email-body">
        <!-- Full HTML content rendered here -->
    </div>
    
    <!-- Enrichment Actions -->
    <div class="enrichment-actions">
        <button onclick="deepAnalysis()">🔍 Deep Analysis</button>
        <button onclick="relatedContent()">📊 Related Items</button>
        <button onclick="addNote()">📝 Add Note</button>
    </div>
</div>
```

### 4. Processing Pipeline

#### Step 1: Fetch Matching Emails
```python
def fetch_tagged_emails(hours=24):
    # Load tagging rules
    rules = load_tag_detection_rules()
    
    # Query unified_feed for emails
    emails = query_emails_with_tags(rules, hours)
    
    return emails
```

#### Step 2: Enrich with Full Content
```python
def enrich_email_content(email):
    # Get complete email data
    full_content = fetch_full_email(email['message_id'])
    
    # Parse HTML/Text
    parsed = parse_email_content(full_content)
    
    # Extract metadata
    metadata = extract_email_metadata(parsed)
    
    return {**email, **parsed, **metadata}
```

#### Step 3: Apply Handler Analysis
```python
def apply_handler_analysis(email):
    # Get handler mapping
    handler = get_handler_for_tag(email['detected_tag'])
    
    # Run handler
    analysis = handler.analyze(
        title=email['subject'],
        content=email['content_text'],
        html=email['content_html']
    )
    
    return {**email, **analysis}
```

#### Step 4: Store for Display
```python
def store_email_analysis(enriched_email):
    # Create record
    record = {
        'id': f"email_analysis_{enriched_email['id']}",
        'created_at': datetime.now(UTC).isoformat(),
        **enriched_email
    }
    
    # Insert into LanceDB
    table.add(record)
```

### 5. Interactive Features

#### Click to Expand
- Clicking email item loads full content
- Smooth animation from list to detail view
- Maintains scroll position

#### AI Enrichment Button
- On-demand deep analysis
- Shows loading state
- Updates UI with results

#### Related Content
- Finds similar emails/tweets
- Links to original items
- Shows relevance scores

#### User Notes
- Add personal annotations
- Persist across sessions
- Searchable

### 6. Styling (Gmail-inspired)

```css
/* Email List */
.email-item {
    border-bottom: 1px solid #e0e0e0;
    padding: 12px 16px;
    cursor: pointer;
    transition: background 0.2s;
}

.email-item:hover {
    background: #f5f5f5;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

/* Expanded View */
.email-expanded {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    padding: 24px;
    animation: slideDown 0.3s ease;
}

/* AI Analysis */
.ai-analysis-panel {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 16px;
    border-radius: 8px;
    margin: 16px 0;
}
```

### 7. Implementation Timeline

#### Phase 1: Backend (2-3 hours)
1. Create `email_analysis` table schema
2. Implement batch processor
3. Integrate with existing handlers
4. Set up cron job

#### Phase 2: Frontend (3-4 hours)
1. Create Flask interface on port 8547
2. Design Gmail-style templates
3. Implement expand/collapse logic
4. Add AI enrichment buttons

#### Phase 3: Enhancement (2 hours)
1. Add search functionality
2. Implement filtering by tag/sender
3. Add export capabilities
4. Create user notes system

### 8. Integration Points

#### With Existing System:
- Reads from `unified_feed` (no modifications)
- Uses `tag_detection_rules.json`
- Uses `tag_handler_mappings.json`
- Leverages existing handlers in `/handlers`

#### New Components:
- `email_analysis` LanceDB table
- `sage_email_analysis.py` Flask app
- `templates/email_analysis.html`
- Port 8547 for interface

### 9. Benefits

1. **Complete Context**: Full email content preserved
2. **Rich Display**: Gmail-like familiar interface
3. **Deep Analysis**: Handler-based AI enrichment
4. **User Control**: On-demand analysis and notes
5. **Performance**: Pre-processed and cached

### 10. Example Use Cases

#### Financial Alert
- Email from Bloomberg about Fed decision
- Tagged as "Bloomberg"
- Routed to `bloomberg_breaking_news_handler`
- Displays with urgency indicators
- Shows market impact analysis

#### Research Report
- Email from Goldman Sachs
- Tagged as "GS Research"
- Routed to `gold_standard_enhanced_handler`
- Displays with key findings highlighted
- Links to related reports

#### Newsletter Digest
- Email from Reuters
- Tagged as "Reuters"
- Routed to `newsbrief_with_links_handler`
- Displays with story summaries
- Each story expandable

---

## Next Steps

1. **Confirm Design**: Review and approve the architecture
2. **Create Backend**: Implement batch processor and storage
3. **Build Interface**: Create Gmail-style UI
4. **Test Integration**: Verify with live data
5. **Deploy**: Add to cron schedule

This design provides a complete, Gmail-inspired interface for deep email analysis while maintaining the integrity of the existing EBS SAGE system.
