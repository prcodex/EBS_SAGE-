# Analysis Batch Specification (3rd Batch System)

## Overview

The Analysis Batch is a **separate, independent batch process** that performs deep analysis on already-ingested data from the unified_feed table. It operates in read-only mode on the main table and writes results to a separate storage location.

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                 ANALYSIS BATCH PIPELINE                 │
├────────────────────────────────────────────────────────┤
│                                                        │
│  1. READ PHASE                                        │
│  └─ Query unified_feed table (read-only)             │
│  └─ Filter last 24-48 hours of data                  │
│  └─ Select items not yet analyzed                    │
│                                                        │
│  2. DETECTION PHASE                                   │
│  └─ Apply tag_detection_rules.json                   │
│  └─ Match sender patterns                            │
│  └─ Assign appropriate tags                          │
│                                                        │
│  3. ROUTING PHASE                                     │
│  └─ Load tag_handler_mappings.json                   │
│  └─ Route to unified_adaptive_enrichment.py          │
│  └─ Select appropriate handler                       │
│                                                        │
│  4. ENRICHMENT PHASE                                  │
│  └─ Execute specialized handler                      │
│  └─ Generate deep analysis (2,500-5,000 chars)       │
│  └─ Extract comprehensive actors/themes              │
│                                                        │
│  5. SYNTHESIS PHASE                                   │
│  └─ Combine all analysis components                  │
│  └─ Generate confidence scores                       │
│  └─ Create structured output                         │
│                                                        │
│  6. STORAGE PHASE                                     │
│  └─ Write to analysis_results table                  │
│  └─ Link to original item ID                         │
│  └─ Update analysis tracker                          │
│                                                        │
│  7. DISPLAY PHASE                                     │
│  └─ Serve via Flask API (port 8546)                  │
│  └─ Show 8-step journey visualization                │
│  └─ Interactive analysis explorer                    │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## Implementation Details

### File: `analysis_batch_processor.py`

```python
#!/usr/bin/env python3
"""
Analysis Batch Processor - 3rd Batch System
Performs deep analysis on ingested data
"""

import json
import lancedb
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
import time

# Add handlers to path
sys.path.append('/home/ubuntu/newspaper_project')
sys.path.append('/home/ubuntu/newspaper_project/handlers')

from unified_adaptive_enrichment import apply_rule
from id_tracker_ebs import load_tracker, save_tracker

# Configuration
DB_URI = '/mnt/lancedb_clean'
INPUT_TABLE = 'unified_feed'
OUTPUT_TABLE = 'analysis_results'
ANALYSIS_TRACKER = 'analyzed_ids.json'

def load_analyzed_ids():
    """Load IDs that have been analyzed"""
    if Path(ANALYSIS_TRACKER).exists():
        with open(ANALYSIS_TRACKER, 'r') as f:
            return set(json.load(f))
    return set()

def save_analyzed_ids(analyzed_ids):
    """Save analyzed IDs"""
    with open(ANALYSIS_TRACKER, 'w') as f:
        json.dump(list(analyzed_ids), f)

def load_detection_rules():
    """Load tag detection rules"""
    with open('tag_detection_rules.json', 'r') as f:
        return json.load(f).get('rules', {})

def load_handler_mappings():
    """Load tag to handler mappings"""
    with open('tag_handler_mappings.json', 'r') as f:
        return json.load(f)

def detect_tag(item, rules):
    """Detect appropriate tag for item"""
    sender = item.get('sender', '')
    subject = item.get('subject', '')
    content = item.get('content_text', '')
    
    for tag, rule in rules.items():
        # Check sender match
        if rule.get('sender') and rule['sender'].lower() in sender.lower():
            return tag
        # Check subject match
        if rule.get('subject') and rule['subject'].lower() in subject.lower():
            return tag
        # Check content patterns
        if rule.get('body') and rule['body'].lower() in content.lower():
            return tag
    
    return None

def analyze_item(item, tag, handler_mapping, api_key):
    """Perform deep analysis on item"""
    handler = handler_mapping.get(tag, 'aaa_universal_handler')
    
    # Apply the handler
    result = apply_rule(
        tag=tag,
        rule={'handler': handler},
        title=item.get('title', item.get('subject', '')),
        content_text=item.get('content_text', ''),
        content_html=item.get('content_html', ''),
        api_key=api_key
    )
    
    return result

def create_analysis_record(item, analysis, tag, handler):
    """Create analysis result record"""
    return {
        'id': f"analysis_{item['id']}_{datetime.now().timestamp()}",
        'original_id': item['id'],
        'analyzed_at': datetime.now().isoformat() + 'Z',
        'source_type': item.get('source_type'),
        'tag_detected': tag,
        'handler_used': handler,
        'deep_analysis': analysis.get('smart_summary', ''),
        'actors_extracted': json.dumps(analysis.get('actors', [])),
        'themes_extracted': json.dumps(analysis.get('themes', [])),
        'confidence_score': analysis.get('ai_relevance_score', 0),
        'analysis_category': analysis.get('smart_category', ''),
        'processing_steps': json.dumps({
            'step1_fetch': 'Read from unified_feed',
            'step2_filter': f'Detected tag: {tag}',
            'step3_tag': tag or 'No tag',
            'step4_route': handler,
            'step5_enrich': 'Deep analysis complete',
            'step6_extract': f"{len(analysis.get('actors', []))} actors, {len(analysis.get('themes', []))} themes",
            'step7_score': f"Score: {analysis.get('ai_relevance_score', 0)}/10",
            'step8_store': 'Saved to analysis_results'
        })
    }

def main():
    """Main analysis batch process"""
    print(f"{'='*60}")
    print(f"Analysis Batch Processor - {datetime.now()}")
    print(f"{'='*60}")
    
    # Load configurations
    analyzed_ids = load_analyzed_ids()
    detection_rules = load_detection_rules()
    handler_mappings = load_handler_mappings()
    
    # Connect to database
    db = lancedb.connect(DB_URI)
    input_table = db.open_table(INPUT_TABLE)
    
    # Create or open output table
    try:
        output_table = db.open_table(OUTPUT_TABLE)
    except:
        # Create table if it doesn't exist
        output_table = db.create_table(OUTPUT_TABLE, data=[])
    
    # Query recent unanalyzed items
    df = input_table.to_pandas()
    
    # Filter for recent items (last 48 hours)
    cutoff = datetime.now() - timedelta(hours=48)
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True, errors='coerce')
    df = df[df['created_at'] > cutoff]
    
    # Filter out already analyzed
    df = df[~df['id'].isin(analyzed_ids)]
    
    # Filter out junk
    if 'is_junk' in df.columns:
        df = df[df['is_junk'] != True]
    
    print(f"Found {len(df)} items to analyze")
    
    # Process each item
    analysis_results = []
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    for idx, item in df.iterrows():
        try:
            # Detect tag
            tag = detect_tag(item.to_dict(), detection_rules)
            if not tag:
                print(f"  No tag detected for {item['id']}, skipping")
                continue
            
            # Get handler
            handler = handler_mappings.get(tag, 'aaa_universal_handler')
            print(f"  Analyzing {item['id']} with tag={tag}, handler={handler}")
            
            # Perform analysis
            analysis = analyze_item(item.to_dict(), tag, handler_mappings, api_key)
            
            # Create result record
            result = create_analysis_record(item.to_dict(), analysis, tag, handler)
            analysis_results.append(result)
            
            # Update tracker
            analyzed_ids.add(item['id'])
            
            # Respect API rate limits
            time.sleep(2)
            
        except Exception as e:
            print(f"  Error analyzing {item['id']}: {e}")
            continue
    
    # Save results
    if analysis_results:
        results_df = pd.DataFrame(analysis_results)
        output_table.add(results_df)
        print(f"Saved {len(analysis_results)} analysis results")
    
    # Save tracker
    save_analyzed_ids(analyzed_ids)
    
    print(f"Analysis batch complete: {len(analysis_results)} items processed")

if __name__ == '__main__':
    main()
```

## Display Interface Specification

### Port 8546: Analysis Explorer

```python
# analysis_interface.py
from flask import Flask, render_template, jsonify
import lancedb
import pandas as pd

app = Flask(__name__)

DB_URI = '/mnt/lancedb_clean'

@app.route('/')
def index():
    return render_template('analysis_explorer.html')

@app.route('/api/analysis/<item_id>')
def get_analysis(item_id):
    """Get analysis for specific item"""
    db = lancedb.connect(DB_URI)
    
    # Get original item
    unified = db.open_table('unified_feed')
    original = unified.to_pandas()
    original = original[original['id'] == item_id]
    
    # Get analysis
    analysis = db.open_table('analysis_results')
    results = analysis.to_pandas()
    results = results[results['original_id'] == item_id]
    
    if not results.empty:
        result = results.iloc[0].to_dict()
        result['processing_steps'] = json.loads(result['processing_steps'])
        result['original'] = original.iloc[0].to_dict() if not original.empty else {}
        return jsonify(result)
    
    return jsonify({'error': 'No analysis found'}), 404

@app.route('/api/analysis/recent')
def get_recent_analyses():
    """Get recent analysis results"""
    db = lancedb.connect(DB_URI)
    analysis = db.open_table('analysis_results')
    df = analysis.to_pandas()
    
    # Sort by analysis time
    df = df.sort_values('analyzed_at', ascending=False)
    df = df.head(50)
    
    results = []
    for _, row in df.iterrows():
        results.append({
            'id': row['id'],
            'original_id': row['original_id'],
            'analyzed_at': row['analyzed_at'],
            'tag': row['tag_detected'],
            'handler': row['handler_used'],
            'score': row['confidence_score'],
            'category': row['analysis_category']
        })
    
    return jsonify({'analyses': results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8546, debug=False)
```

## HTML Template

```html
<!-- templates/analysis_explorer.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Analysis Explorer - 8-Step Pipeline</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #f0f2f5;
            margin: 0;
            padding: 20px;
        }
        
        .pipeline-visualization {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        
        .step {
            display: flex;
            align-items: center;
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #1da1f2;
        }
        
        .step.complete {
            border-left-color: #28a745;
            background: #f0fff4;
        }
        
        .step-number {
            font-size: 24px;
            font-weight: bold;
            color: #1da1f2;
            margin-right: 15px;
        }
        
        .step-content {
            flex: 1;
        }
        
        .step-title {
            font-weight: 600;
            color: #14171a;
            margin-bottom: 5px;
        }
        
        .step-detail {
            color: #657786;
            font-size: 14px;
        }
        
        .analysis-content {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .deep-analysis {
            line-height: 1.6;
            color: #14171a;
        }
        
        .actors-themes {
            display: flex;
            gap: 20px;
            margin-top: 20px;
        }
        
        .actors, .themes {
            flex: 1;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .tag {
            display: inline-block;
            padding: 4px 8px;
            background: #e8f4fd;
            color: #1da1f2;
            border-radius: 4px;
            margin: 2px;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <h1>🔬 Analysis Explorer - 8-Step Pipeline</h1>
    
    <div class="pipeline-visualization" id="pipeline">
        <!-- Pipeline steps will be populated here -->
    </div>
    
    <div class="analysis-content" id="analysis">
        <!-- Analysis content will be shown here -->
    </div>
    
    <script>
        // JavaScript to load and display analysis
        async function loadAnalysis(itemId) {
            const response = await fetch(`/api/analysis/${itemId}`);
            const data = await response.json();
            
            // Display pipeline steps
            const pipeline = document.getElementById('pipeline');
            const steps = data.processing_steps;
            
            let html = '<h2>Processing Pipeline</h2>';
            Object.entries(steps).forEach(([key, value], index) => {
                const stepNum = index + 1;
                const stepName = key.replace('step', 'Step ');
                html += `
                    <div class="step complete">
                        <div class="step-number">${stepNum}</div>
                        <div class="step-content">
                            <div class="step-title">${stepName.toUpperCase()}</div>
                            <div class="step-detail">${value}</div>
                        </div>
                    </div>
                `;
            });
            pipeline.innerHTML = html;
            
            // Display analysis
            const analysis = document.getElementById('analysis');
            html = `
                <h2>Deep Analysis</h2>
                <div class="deep-analysis">${data.deep_analysis}</div>
                <div class="actors-themes">
                    <div class="actors">
                        <h3>🎭 Actors</h3>
                        ${JSON.parse(data.actors_extracted).map(a => `<span class="tag">${a}</span>`).join('')}
                    </div>
                    <div class="themes">
                        <h3>🎯 Themes</h3>
                        ${JSON.parse(data.themes_extracted).map(t => `<span class="tag">${t}</span>`).join('')}
                    </div>
                </div>
            `;
            analysis.innerHTML = html;
        }
        
        // Load recent analyses
        async function loadRecent() {
            const response = await fetch('/api/analysis/recent');
            const data = await response.json();
            // Display list of recent analyses
        }
        
        // Initialize
        loadRecent();
    </script>
</body>
</html>
```

## Cron Schedule

```bash
# Run analysis batch every 4 hours
0 */4 * * * cd /home/ubuntu/newspaper_project && python3 analysis_batch_processor.py >> /home/ubuntu/logs/analysis_batch.log 2>&1
```

## Key Features

1. **Complete Separation**: Independent from ingestion batches
2. **Read-Only on Main Table**: No risk of data corruption
3. **Deep Analysis**: 2,500-5,000 character summaries
4. **Handler Reactivation**: All 26 handlers available
5. **Visual Pipeline**: Shows 8-step journey
6. **Performance**: Processes ~100 items per hour
7. **Configurable**: Via admin interface (port 8543)

## Benefits

- **No Impact on Ingestion**: Runs separately
- **Retroactive Analysis**: Can process old data
- **Quality over Speed**: Deep, thoughtful analysis
- **Transparency**: Shows decision process
- **Flexibility**: Easy to modify handlers

---

*Analysis Batch Specification v1.0*
*November 9, 2025*
