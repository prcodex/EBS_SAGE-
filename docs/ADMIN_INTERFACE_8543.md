# Admin Interface Documentation (Port 8543)

## Overview
The Admin Interface provides comprehensive control over the SAGE EBS system's configuration, tagging rules, and content filtering.

## Access
- **URL**: http://44.225.226.126:8543
- **Port**: 8543
- **Backend**: `scrapex_admin.py`
- **Template**: `templates/admin_complete.html`

## Features

### 1. Allowed Senders Management
- **Purpose**: Control which email senders are accepted by the system
- **Fields**:
  - `sender_tag`: Display name for the sender
  - `email_patterns`: List of email patterns to match
  - `description`: Optional description
  - `active`: Enable/disable sender without deletion
- **Operations**: Add, Edit, Delete senders

### 2. Tagging Rules
- **Purpose**: Define rules to automatically tag incoming content
- **Detection Logic**:
  - Match by sender
  - Match by subject keywords
  - Match by body content
  - Combine with AND/OR logic
- **Operations**: Create, Edit, Delete rules
- **File**: `tag_detection_rules.json`

### 3. Tag → Handler Mappings
- **Purpose**: Link detected tags to AI enrichment handlers
- **Available Handlers** (26 total):
  - `aaa_universal_handler`: General-purpose AI analysis
  - `bloomberg_breaking_news_handler`: Bloomberg-specific processing
  - `breakfast_with_dave_handler`: Dave Rosenberg's analysis
  - `gold_standard_enhanced_handler`: Premium analysis pipeline
  - `newsbrief_with_links_handler`: Extract and process links
  - And 21 more specialized handlers
- **Operations**: Add new mappings, Delete existing mappings
- **File**: `tag_handler_mappings.json`

### 4. NewsFlow Control
- **Purpose**: Manage which senders are processed by NewsBrief batch
- **Separate from general allowed senders**
- **File**: `newsflow_allowlist.json`
- **Operations**: Add/Remove senders from NewsFlow processing

## Configuration Files

### allowed_senders.json
```json
[
  {
    "sender_tag": "Bloomberg",
    "email_patterns": ["bloomberg.com", "bloombergbusiness.com"],
    "description": "Bloomberg financial news",
    "active": true
  }
]
```

### tag_detection_rules.json
```json
{
  "rules": {
    "Bloomberg": {
      "sender": ["Bloomberg"],
      "subject_contains": "",
      "body_contains": "",
      "logic": "OR",
      "description": "Bloomberg emails"
    }
  }
}
```

### tag_handler_mappings.json
```json
{
  "Bloomberg": "bloomberg_breaking_news_handler",
  "Reuters": "newsbrief_with_links_handler",
  "myFT": "aaa_universal_handler"
}
```

### newsflow_allowlist.json
```json
{
  "allowed_senders": [
    "Bloomberg",
    "Reuters",
    "Financial Times",
    "Barron's",
    "Folha de S.Paulo",
    "Estadão"
  ]
}
```

## API Endpoints

### GET Endpoints
- `/api/allowed_senders`: Get list of sender tags
- `/api/allowed_senders_full`: Get complete sender configurations
- `/api/detection_rules`: Get tagging rules
- `/api/tag_handler_mappings`: Get tag-to-handler mappings
- `/api/available_handlers`: Get list of available handler modules
- `/api/newsflow_allowlist`: Get NewsFlow specific allowlist

### POST Endpoints
- `/api/save_sender`: Add/update sender configuration
- `/api/delete_sender`: Remove sender
- `/api/save_detection_rule`: Add/update tagging rule
- `/api/delete_detection_rule`: Remove tagging rule
- `/api/tag_handler_mappings`: Add/delete handler mapping
- `/api/newsflow_allowlist`: Manage NewsFlow allowlist

## Recent Updates (November 10, 2025)

### Bug Fixes
- Fixed JavaScript syntax errors in admin template
- Corrected undefined `rules` variable in `loadDetectionRules()`
- Added missing `/api/save_detection_rule` endpoint
- Fixed double bracket syntax error in handler list
- Restored `/api/allowed_senders_full` endpoint association

### Enhancements
- Dynamic handler list loading from filesystem
- Improved NewsFlow control with dropdown selection
- Better error handling for rule operations
- Fixed delete functionality for rules and mappings

## Troubleshooting

### Common Issues

1. **Interface not loading**
   - Check if service is running: `ps aux | grep scrapex_admin`
   - Restart service: `sudo pkill -f scrapex_admin && nohup python3 scrapex_admin.py &`

2. **Rules not saving**
   - Verify `/api/save_detection_rule` endpoint exists
   - Check file permissions on JSON configuration files

3. **Handlers not showing in dropdown**
   - Ensure `/api/available_handlers` endpoint is working
   - Verify handler files exist in `/handlers` directory

4. **NewsFlow senders not updating**
   - Check `newsflow_allowlist.json` file exists
   - Verify NewsFlow batch is reading from correct file

## Integration with Main System

The admin interface controls three critical aspects:

1. **Email Ingestion**: `allowed_senders.json` determines which emails are accepted
2. **Content Classification**: `tag_detection_rules.json` tags content for routing
3. **AI Enrichment**: `tag_handler_mappings.json` selects appropriate AI analysis
4. **Batch Processing**: `newsflow_allowlist.json` controls NewsBrief batch scope

Changes made through the admin interface take effect:
- **Immediately** for new incoming content
- **On next batch run** for scheduled processes
- **After service restart** for cached configurations

---
*Last Updated: November 10, 2025*
