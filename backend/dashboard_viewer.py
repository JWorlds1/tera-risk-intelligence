#!/usr/bin/env python3
"""
Einfaches Web-Dashboard zum Anzeigen der extrahierten Daten
"""
from flask import Flask, render_template_string, jsonify, request
from pathlib import Path
import sqlite3
from datetime import datetime
from typing import Dict, List, Any
import json

app = Flask(__name__)

DB_PATH = Path("./data/climate_conflict.db")


def get_db_connection():
    """Datenbankverbindung erstellen"""
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """Hauptseite mit Dashboard"""
    return render_template_string(DASHBOARD_TEMPLATE)


@app.route('/api/stats')
def get_stats():
    """API: Datenbank-Statistiken"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database not found'}), 404
    
    try:
        cursor = conn.cursor()
        
        # Total records
        cursor.execute("SELECT COUNT(*) as count FROM records")
        total_records = cursor.fetchone()['count']
        
        # Records per source
        cursor.execute("""
            SELECT source_name, COUNT(*) as count
            FROM records
            GROUP BY source_name
        """)
        records_by_source = {row['source_name']: row['count'] for row in cursor.fetchall()}
        
        # Recent records (last 24h)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM records
            WHERE fetched_at > datetime('now', '-1 day')
        """)
        records_last_24h = cursor.fetchone()['count']
        
        # Latest crawl jobs
        cursor.execute("""
            SELECT * FROM crawl_jobs
            ORDER BY created_at DESC
            LIMIT 5
        """)
        latest_jobs = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'total_records': total_records,
            'records_by_source': records_by_source,
            'records_last_24h': records_last_24h,
            'latest_jobs': latest_jobs
        })
    finally:
        conn.close()


@app.route('/api/records')
def get_records():
    """API: Records abrufen"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database not found'}), 404
    
    try:
        source = request.args.get('source', None)
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        cursor = conn.cursor()
        
        query = "SELECT * FROM records WHERE 1=1"
        params = []
        
        if source:
            query += " AND source_name = ?"
            params.append(source)
        
        query += " ORDER BY fetched_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        records = [dict(row) for row in cursor.fetchall()]
        
        # Enrich with topics
        for record in records:
            cursor.execute("SELECT topic FROM record_topics WHERE record_id = ?", (record['id'],))
            record['topics'] = [r['topic'] for r in cursor.fetchall()]
        
        return jsonify({'records': records})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/records/<int:record_id>')
def get_record_detail(record_id):
    """API: Einzelnen Record abrufen"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database not found'}), 404
    
    try:
        cursor = conn.cursor()
        
        # Get record
        cursor.execute("SELECT * FROM records WHERE id = ?", (record_id,))
        record = cursor.fetchone()
        
        if not record:
            return jsonify({'error': 'Record not found'}), 404
        
        record_dict = dict(record)
        
        # Get topics
        cursor.execute("SELECT topic FROM record_topics WHERE record_id = ?", (record_id,))
        record_dict['topics'] = [r['topic'] for r in cursor.fetchall()]
        
        # Get links
        cursor.execute("SELECT link_url FROM record_links WHERE record_id = ?", (record_id,))
        record_dict['links'] = [r['link_url'] for r in cursor.fetchall()]
        
        # Get source-specific data
        source_name = record_dict['source_name']
        if source_name == 'NASA':
            cursor.execute("SELECT * FROM nasa_records WHERE record_id = ?", (record_id,))
            nasa_data = cursor.fetchone()
            if nasa_data:
                record_dict['nasa_data'] = dict(nasa_data)
        elif source_name == 'UN Press':
            cursor.execute("SELECT * FROM un_press_records WHERE record_id = ?", (record_id,))
            un_data = cursor.fetchone()
            if un_data:
                record_dict['un_data'] = dict(un_data)
        elif source_name == 'WFP':
            cursor.execute("SELECT * FROM wfp_records WHERE record_id = ?", (record_id,))
            wfp_data = cursor.fetchone()
            if wfp_data:
                record_dict['wfp_data'] = dict(wfp_data)
        elif source_name == 'World Bank':
            cursor.execute("SELECT * FROM worldbank_records WHERE record_id = ?", (record_id,))
            wb_data = cursor.fetchone()
            if wb_data:
                record_dict['worldbank_data'] = dict(wb_data)
        
        return jsonify(record_dict)
    finally:
        conn.close()


# Dashboard HTML Template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Climate Conflict Data Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }
        .records-container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .record-item {
            border-bottom: 1px solid #eee;
            padding: 20px 0;
        }
        .record-item:last-child {
            border-bottom: none;
        }
        .record-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        .record-meta {
            display: flex;
            gap: 20px;
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .record-summary {
            color: #555;
            line-height: 1.6;
            margin-bottom: 10px;
        }
        .record-topics {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .topic-tag {
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
        }
        .source-badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
            font-weight: bold;
        }
        .source-nasa { background: #e3f2fd; color: #1976d2; }
        .source-un { background: #fff3e0; color: #f57c00; }
        .source-worldbank { background: #e8f5e9; color: #388e3c; }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 20px;
        }
        .refresh-btn:hover {
            background: #5568d3;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌍 Climate Conflict Data Dashboard</h1>
            <p>Extraktion & Analyse von Klima-Konflikt Daten</p>
        </div>
        
        <div class="stats-grid" id="stats">
            <div class="stat-card">
                <h3>Gesamt Records</h3>
                <div class="value" id="total-records">-</div>
            </div>
            <div class="stat-card">
                <h3>Records (24h)</h3>
                <div class="value" id="records-24h">-</div>
            </div>
            <div class="stat-card">
                <h3>NASA Records</h3>
                <div class="value" id="nasa-records">-</div>
            </div>
            <div class="stat-card">
                <h3>UN Press Records</h3>
                <div class="value" id="un-records">-</div>
            </div>
            <div class="stat-card">
                <h3>World Bank Records</h3>
                <div class="value" id="wb-records">-</div>
            </div>
        </div>
        
        <div class="records-container">
            <h2 style="margin-bottom: 20px;">Neueste Records</h2>
            <div id="records-list" class="loading">Lade Daten...</div>
            <button class="refresh-btn" onclick="loadData()">🔄 Aktualisieren</button>
        </div>
    </div>
    
    <script>
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                document.getElementById('total-records').textContent = data.total_records || 0;
                document.getElementById('records-24h').textContent = data.records_last_24h || 0;
                document.getElementById('nasa-records').textContent = data.records_by_source?.NASA || 0;
                document.getElementById('un-records').textContent = data.records_by_source?.['UN Press'] || 0;
                document.getElementById('wb-records').textContent = data.records_by_source?.['World Bank'] || 0;
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        async function loadRecords() {
            try {
                const response = await fetch('/api/records?limit=20');
                const data = await response.json();
                
                const recordsList = document.getElementById('records-list');
                
                if (!data.records || data.records.length === 0) {
                    recordsList.innerHTML = '<div class="loading">Keine Records gefunden. Starte die Pipeline!</div>';
                    return;
                }
                
                recordsList.innerHTML = data.records.map(record => {
                    const sourceClass = {
                        'NASA': 'source-nasa',
                        'UN Press': 'source-un',
                        'World Bank': 'source-worldbank'
                    }[record.source_name] || '';
                    
                    return `
                        <div class="record-item">
                            <div class="record-title">
                                <span class="source-badge ${sourceClass}">${record.source_name}</span>
                                ${record.title || 'Kein Titel'}
                            </div>
                            <div class="record-meta">
                                <span>📅 ${record.publish_date || 'N/A'}</span>
                                <span>🌍 ${record.region || 'N/A'}</span>
                                <span>🕐 ${new Date(record.fetched_at).toLocaleString('de-DE')}</span>
                            </div>
                            ${record.summary ? `<div class="record-summary">${record.summary.substring(0, 200)}...</div>` : ''}
                            ${record.topics && record.topics.length > 0 ? `
                                <div class="record-topics">
                                    ${record.topics.map(topic => `<span class="topic-tag">${topic}</span>`).join('')}
                                </div>
                            ` : ''}
                        </div>
                    `;
                }).join('');
            } catch (error) {
                console.error('Error loading records:', error);
                document.getElementById('records-list').innerHTML = '<div class="loading">Fehler beim Laden der Daten</div>';
            }
        }
        
        function loadData() {
            loadStats();
            loadRecords();
        }
        
        // Initial load
        loadData();
        
        // Auto-refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    # Prüfe ob Flask installiert ist
    try:
        from flask import request
    except ImportError:
        print("Flask nicht installiert. Installiere...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'flask'])
        from flask import request
    
    print("🌍 Climate Conflict Dashboard startet...")
    print(f"📊 Datenbank: {DB_PATH}")
    print("🌐 Dashboard verfügbar unter: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

