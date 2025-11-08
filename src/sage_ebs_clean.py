from flask import Flask, jsonify, render_template, request, make_response
from flask_cors import CORS
import lancedb
import pandas as pd
from datetime import datetime
import json
import math
import re

app = Flask(__name__)
CORS(app)

DB_URI = '/mnt/lancedb_clean'
TABLE_NAME = 'unified_feed'

print('=' * 60)
print('🚀 SAGE EBS Clean Interface Starting...')
print(f'   Database: {DB_URI}')
print('   Architecture: INSERT-only (no updates)')
print('   Port: 8545')
print('=' * 60)


def _build_sender_tag(sender: str, source: str) -> str:
    if not sender:
        return 'Unknown'
    name = sender
    if '<' in sender:
        name = sender.split('<')[0].strip().strip('"')
    name = name.strip()
    if source and 'newsbrief' in source.lower() and 'Newsbrief' not in name:
        name = f"{name} - Newsbrief"
    return name or 'Unknown'


def _sanitize_str(value):
    if value is None:
        return ''
    if isinstance(value, float) and math.isnan(value):
        return ''
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return ''
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        value = value.replace(tzinfo=None)
        return value.strftime('%Y-%m-%dT%H:%M:%S')
    text = str(value)
    if text.strip().lower() == 'nat':
        return ''
    return text


def _sanitize_float(value):
    if value in (None, ''):
        return 0.0
    try:
        number = float(value)
        if math.isnan(number):
            return 0.0
        return number
    except (ValueError, TypeError):
        return 0.0


def _sanitize_datetime(value):
    """Sanitize datetime values, keeping naive datetimes as-is and normalizing timezone-aware to UTC"""
    if value is None or value == '':
        return ''

    str_value = str(value).strip()
    if str_value.lower() in {'nat', 'nan'}:
        return ''

    # If pandas timestamp
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return ''
        if value.tzinfo is None:
            return value.isoformat()
        ts_utc = value.tz_convert('UTC')
        iso = ts_utc.isoformat()
        return iso[:-6] + 'Z' if iso.endswith('+00:00') else iso

    # Strings: detect timezone information
    has_timezone = bool(re.search(r"([+-]\d{2}:?\d{2}|Z)$", str_value))
    try:
        ts = pd.to_datetime(str_value, utc=has_timezone)
    except Exception:
        return str_value

    if pd.isna(ts):
        return ''

    if has_timezone:
        iso = ts.isoformat()
        return iso[:-6] + 'Z' if iso.endswith('+00:00') else iso

    # Naive string -> keep original format (truncate microseconds for consistency)
    try:
        ts_naive = pd.to_datetime(str_value).to_pydatetime().replace(tzinfo=None)
        return ts_naive.strftime('%Y-%m-%dT%H:%M:%S')
    except Exception:
        return str_value



def _format_item(row):
    if hasattr(row, 'to_dict'):
        item = row.to_dict()
    else:
        item = dict(row)

    sender = item.get('sender') or item.get('author')
    source = item.get('source', '')

    enriched_content = item.get('enriched_content') or item.get('content_text', '')

    formatted = {
        'id': _sanitize_str(item.get('id', '')),
        'source_type': _sanitize_str(item.get('source_type', 'email')),
        'source': _sanitize_str(source),
        'created_at': _sanitize_datetime(item.get('created_at', '')),
        'author': _sanitize_str(item.get('author', '')),
        'title': _sanitize_str(item.get('title', '')),
        'subject': _sanitize_str(item.get('subject', '')),
        'content_text': _sanitize_str(item.get('content_text', ''))[:1000],
        'content_html': _sanitize_str(item.get('content_html', '')),
        'sender': _sanitize_str(sender),
        'sender_tag': _sanitize_str(item.get('sender_tag') or _build_sender_tag(sender, source)),
        'ai_score': _sanitize_float(item.get('ai_score')),
        'ai_relevance_score': _sanitize_float(item.get('ai_relevance_score')),
        'enriched_content': _sanitize_str(enriched_content),
        'actors': _sanitize_str(item.get('actors', '')),
        'themes': _sanitize_str(item.get('themes', '')),
        'link': _sanitize_str(item.get('link', '')),
        'is_junk': bool(item.get('is_junk', False)),
        'is_attention': bool(item.get('is_attention', False)),
        'custom_fields': _sanitize_str(item.get('custom_fields', ''))
    }
    return formatted



@app.route('/')
def index():
    return render_template('sage_4.0_interface.html')


@app.route('/api/feed')
def get_feed():
    view = request.args.get('view', 'default')
    source_filter = request.args.get('source', 'all')

    try:
        db = lancedb.connect(DB_URI)
        table = db.open_table(TABLE_NAME)
        df = table.to_pandas()

        # Filter by source
        if source_filter == 'email':
            df = df[df['source_type'] == 'email']
        elif source_filter == 'tweet':
            df = df[df['source_type'] == 'tweet']

        # Filter by junk status
        if view == 'junk':
            df = df[df['is_junk'] == True]
        else:
            df = df[df['is_junk'] != True]

        if 'created_at' in df.columns:
            # Convert each value individually so plain ISO strings without timezone are handled
            df['created_at'] = df['created_at'].apply(lambda x: pd.to_datetime(x, utc=True, errors='coerce'))
            df = df.sort_values('created_at', ascending=False, na_position='last')

        items = []
        for _, row in df.iterrows():
            items.append(_format_item(row))

        response = make_response(jsonify({
            'items': items,
            'total': len(items),
            'timestamp': datetime.now().isoformat(),
            'database': 'EBS Clean'
        }))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        return jsonify({'error': str(e), 'items': []}), 500


@app.route('/api/stats')
def get_stats():
    try:
        db = lancedb.connect(DB_URI)
        table = db.open_table(TABLE_NAME)
        df = table.to_pandas()

        stats = {
            'total_items': len(df),
            'email_digests': len(df[df['source'] == 'email_digest']),
            'newsbrief_stories': len(df[df['source'] == 'newsbrief_story']),
            'tweets': len(df[df['source_type'] == 'tweet']),
            'with_ai_scores': len(df[df['ai_score'].notna()]),
            'with_keywords': len(df[df['themes'].notna()]),
            'database': 'EBS Clean (INSERT-only)'
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/email/<item_id>')
def get_email_detail(item_id):
    try:
        db = lancedb.connect(DB_URI)
        table = db.open_table(TABLE_NAME)
        result = table.search().where(f"id = '{item_id}'").limit(1).to_pandas()

        if result.empty:
            return jsonify({'error': 'Item not found'}), 404

        item = result.iloc[0].to_dict()
        source = item.get('source', '')
        sender = item.get('sender') or item.get('author')

        response_data = {
            'id': str(item.get('id', '')),
            'source_type': str(item.get('source_type', 'email')),
            'title': str(item.get('title', '')),
            'sender_tag': str(item.get('sender_tag') or _build_sender_tag(sender, source)),
            'created_at': str(item.get('created_at', '')),
            'content_html': str(item.get('content_html', '')),
            'content_text': str(item.get('content_text', '')),
            'enriched_content': str(item.get('enriched_content', '')),
            'actors': str(item.get('actors', '')),
            'themes': str(item.get('themes', '')),
            'link': str(item.get('link', '')),
            'is_junk': bool(item.get('is_junk', False)),
            'is_attention': bool(item.get('is_attention', False)),
            'ai_score': float(item.get('ai_score', 0)) if item.get('ai_score') not in (None, '') else 0.0
        }

        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/mark_junk/<item_id>', methods=['POST'])
def mark_junk(item_id):
    try:
        db = lancedb.connect(DB_URI)
        table = db.open_table(TABLE_NAME)
        df = table.to_pandas()
        df.loc[df['id'] == item_id, 'is_junk'] = True

        junk_item = df[df['id'] == item_id].copy()
        if not junk_item.empty:
            junk_item['is_junk'] = True
            junk_item['id'] = f"{item_id}_junk_{datetime.now().timestamp()}"
            table.add(junk_item)

        return jsonify({'status': 'marked as junk'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8545, debug=False)
