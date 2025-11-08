#!/usr/bin/env python3
"""
Simple Corrections Handler
==========================
Handles reclassification submissions and stores them for learning
"""

import sqlite3
import json
import http.server
import socketserver
from urllib.parse import parse_qs, urlparse
import uuid
from datetime import datetime
import time

PORT = 8560
DB_PATH = 'twitter_intelligence_24h.db'

def store_correction(tweet_id, hawk_dove, bull_bear, sentiment, market_impact, confidence, reasoning):
    """Store a human correction in the database"""
    
    # Retry logic for database locks
    max_retries = 5
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30.0)
            cursor = conn.cursor()
            
            # Get original classification
            original = cursor.execute('''
                SELECT active_hawk_dove, active_bull_bear, active_sentiment, 
                       active_market_impact, model_confidence, model_version
                FROM tweet_classifications 
                WHERE tweet_id = ?
            ''', (tweet_id,)).fetchone()
            
            if not original:
                conn.close()
                return False, "Tweet not found in classifications"
            
            # Calculate correction metrics
            correction_magnitude = abs(float(hawk_dove) - (original[0] or 0)) + \
                                 abs(float(bull_bear) - (original[1] or 0)) + \
                                 abs(float(sentiment) - (original[2] or 0)) + \
                                 abs(float(market_impact) - (original[3] or 0))
            
            overall_agreement = max(0, 1.0 - (correction_magnitude / 4.0))
            
            # Create correction record
            correction_id = str(uuid.uuid4())
            
            # Ensure table exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS human_corrections (
                    correction_id TEXT PRIMARY KEY,
                    tweet_id TEXT NOT NULL,
                    correction_timestamp TEXT NOT NULL,
                    original_hawk_dove REAL,
                    original_bull_bear REAL,
                    original_sentiment REAL,
                    original_market_impact REAL,
                    corrected_hawk_dove REAL,
                    corrected_bull_bear REAL,
                    corrected_sentiment REAL,
                    corrected_market_impact REAL,
                    human_confidence INTEGER,
                    correction_reasoning TEXT,
                    correction_magnitude REAL,
                    overall_agreement_score REAL,
                    learning_weight REAL DEFAULT 1.0,
                    used_in_training BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Insert correction
            cursor.execute('''
                INSERT INTO human_corrections (
                    correction_id, tweet_id, correction_timestamp,
                    original_hawk_dove, original_bull_bear, original_sentiment, original_market_impact,
                    corrected_hawk_dove, corrected_bull_bear, corrected_sentiment, corrected_market_impact,
                    human_confidence, correction_reasoning, correction_magnitude, overall_agreement_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                correction_id, tweet_id, datetime.now().isoformat(),
                original[0], original[1], original[2], original[3],
                float(hawk_dove), float(bull_bear), float(sentiment), float(market_impact),
                int(confidence), reasoning, correction_magnitude, overall_agreement
            ))
            
            # Update tweet_classifications with human corrections
            cursor.execute('''
                UPDATE tweet_classifications SET
                    human_hawk_dove = ?, human_bull_bear = ?, human_sentiment = ?, human_market_impact = ?,
                    human_confidence = ?, corrected_at = ?, correction_notes = ?,
                    active_hawk_dove = ?, active_bull_bear = ?, active_sentiment = ?, active_market_impact = ?,
                    active_source = 'human', updated_at = ?
                WHERE tweet_id = ?
            ''', (
                float(hawk_dove), float(bull_bear), float(sentiment), float(market_impact),
                int(confidence), datetime.now().isoformat(), reasoning,
                float(hawk_dove), float(bull_bear), float(sentiment), float(market_impact),
                datetime.now().isoformat(), tweet_id
            ))
            
            conn.commit()
            conn.close()
            
            return True, f"Correction {correction_id} stored successfully"
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(1)
                continue
            return False, f"Database error: {e}"
        except Exception as e:
            return False, f"Error: {e}"
    
    return False, "Failed after retries"

class CorrectionsHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/submit-correction':
            # Handle form submission from reclassification interface
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            form_data = parse_qs(post_data)
            
            # Extract form data
            tweet_id = form_data.get('tweet_id', [''])[0]
            hawk_dove = form_data.get('hawk_dove', ['0'])[0]
            bull_bear = form_data.get('bull_bear', ['0'])[0]
            sentiment = form_data.get('sentiment', ['0'])[0]
            market_impact = form_data.get('market_impact', ['0.5'])[0]
            confidence = form_data.get('confidence', ['3'])[0]
            reasoning = form_data.get('reasoning', [''])[0]
            
            # Store the correction
            success, message = store_correction(tweet_id, hawk_dove, bull_bear, sentiment, market_impact, confidence, reasoning)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            if success:
                response_html = f"""
                <html><head><title>Correction Stored</title>
                <style>body {{ font-family: Arial; background: #0f1419; color: #0f0; text-align: center; padding: 50px; }}</style>
                </head><body>
                    <h1>🎉 Human Correction Stored!</h1>
                    <p><strong>Tweet ID:</strong> {tweet_id}</p>
                    <p><strong>Hawk/Dove:</strong> {hawk_dove}</p>
                    <p><strong>Bull/Bear:</strong> {bull_bear}</p>
                    <p><strong>Sentiment:</strong> {sentiment}</p>
                    <p><strong>Market Impact:</strong> {market_impact}</p>
                    <p><strong>Confidence:</strong> {confidence}/5</p>
                    <p><strong>Reasoning:</strong> {reasoning}</p>
                    <p style="color: #0ff; margin-top: 30px;">✅ {message}</p>
                    <p><a href="http://34.72.141.217:8513" style="color: #0f0; background: #333; padding: 10px 20px; text-decoration: none; border-radius: 5px;">← Back to Classified Tweets</a></p>
                    <p><a href="http://34.72.141.217:8561" style="color: #ff0; background: #333; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🎛️ Model Management</a></p>
                    <script>setTimeout(() => {{ window.location.href = 'http://34.72.141.217:8513'; }}, 5000);</script>
                </body></html>
                """
            else:
                response_html = f"""
                <html><head><title>Error</title>
                <style>body {{ font-family: Arial; background: #001; color: #f00; text-align: center; padding: 50px; }}</style>
                </head><body>
                    <h1>❌ Error Storing Correction</h1>
                    <p>{message}</p>
                    <p><a href="javascript:history.back()" style="color: #f00;">← Go Back</a></p>
                </body></html>
                """
            
            self.wfile.write(response_html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
        <html><head><title>SAGE Corrections API</title></head><body>
        <h1>🧠 SAGE Corrections API</h1>
        <p>Backend for storing human corrections</p>
        <p>Status: Running and ready</p>
        </body></html>
        """
        self.wfile.write(html.encode())

if __name__ == '__main__':
    print(f"🧠 SAGE Corrections Handler")
    print(f"🌐 URL: http://localhost:{PORT}")
    print(f"📝 Endpoint: POST /submit-correction")
    
    try:
        with socketserver.TCPServer(("", PORT), CorrectionsHandler) as httpd:
            print(f"✅ Server running on port {PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"❌ Error: {e}")






