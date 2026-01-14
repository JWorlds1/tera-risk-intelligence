# database.py - Zentrale Datenbank für alle extrahierten Daten
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import contextmanager
import structlog
from dataclasses import asdict

from schemas import PageRecord, NASARecord, UNPressRecord, WFPRecord, WorldBankRecord

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """Zentrale Datenbank-Verwaltung für alle Datenquellen"""
    
    def __init__(self, db_path: str = "./data/climate_conflict.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager für Datenbankverbindungen"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Initialisiere Datenbank-Schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Haupttabelle für alle Records
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    source_domain TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    fetched_at TIMESTAMP NOT NULL,
                    title TEXT,
                    summary TEXT,
                    publish_date TEXT,
                    region TEXT,
                    content_type TEXT,
                    language TEXT DEFAULT 'en',
                    full_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(url)
                )
            """)
            
            # Tabelle für Topics/Tags
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS record_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id INTEGER NOT NULL,
                    topic TEXT NOT NULL,
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE,
                    UNIQUE(record_id, topic)
                )
            """)
            
            # Tabelle für Links
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS record_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id INTEGER NOT NULL,
                    link_url TEXT NOT NULL,
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
                )
            """)
            
            # Tabelle für Bilder
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS record_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id INTEGER NOT NULL,
                    image_url TEXT NOT NULL,
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
                )
            """)
            
            # NASA-spezifische Daten
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nasa_records (
                    record_id INTEGER PRIMARY KEY,
                    environmental_indicators TEXT,  -- JSON array
                    satellite_source TEXT,
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
                )
            """)
            
            # UN Press-spezifische Daten
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS un_press_records (
                    record_id INTEGER PRIMARY KEY,
                    meeting_coverage BOOLEAN DEFAULT 0,
                    security_council BOOLEAN DEFAULT 0,
                    speakers TEXT,  -- JSON array
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
                )
            """)
            
            # WFP-spezifische Daten
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wfp_records (
                    record_id INTEGER PRIMARY KEY,
                    crisis_type TEXT,
                    affected_population TEXT,
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
                )
            """)
            
            # World Bank-spezifische Daten
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS worldbank_records (
                    record_id INTEGER PRIMARY KEY,
                    country TEXT,
                    sector TEXT,
                    project_id TEXT,
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
                )
            """)
            
            # Crawling-Jobs und Status
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crawl_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL,
                    urls_count INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',  -- pending, running, completed, failed
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    records_extracted INTEGER DEFAULT 0,
                    records_new INTEGER DEFAULT 0,
                    records_updated INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Geospatial Tabellen
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS geo_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id INTEGER NOT NULL,
                    location_type TEXT NOT NULL,  -- 'country', 'region', 'city', 'point'
                    name TEXT NOT NULL,
                    country_code TEXT,  -- ISO 3166-1 alpha-2
                    country_code_3 TEXT, -- ISO 3166-1 alpha-3
                    latitude REAL,
                    longitude REAL,
                    geojson TEXT,  -- GeoJSON für Polygone
                    bbox_min_lat REAL,
                    bbox_max_lat REAL,
                    bbox_min_lon REAL,
                    bbox_max_lon REAL,
                    confidence REAL DEFAULT 0.0,
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS region_mapping (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    region_name TEXT UNIQUE NOT NULL,
                    normalized_name TEXT,
                    country_codes TEXT,  -- JSON array
                    geojson TEXT,
                    bbox TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS geocoding_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_text TEXT UNIQUE NOT NULL,
                    country_code TEXT,
                    latitude REAL,
                    longitude REAL,
                    geojson TEXT,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Erweitere records Tabelle um geospatial Felder
            try:
                cursor.execute("ALTER TABLE records ADD COLUMN primary_country_code TEXT")
            except sqlite3.OperationalError:
                pass  # Spalte existiert bereits
            
            try:
                cursor.execute("ALTER TABLE records ADD COLUMN primary_latitude REAL")
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute("ALTER TABLE records ADD COLUMN primary_longitude REAL")
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute("ALTER TABLE records ADD COLUMN geo_confidence REAL")
            except sqlite3.OperationalError:
                pass
            
            # Regionale Anreicherungsdaten
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regional_enrichment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    region_name TEXT NOT NULL,
                    country_codes TEXT,  -- JSON array
                    total_records INTEGER DEFAULT 0,
                    enriched_records INTEGER DEFAULT 0,
                    average_risk_score REAL DEFAULT 0.0,
                    risk_distribution TEXT,  -- JSON
                    sources_distribution TEXT,  -- JSON
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    enrichment_data TEXT,  -- JSON mit detaillierten Daten
                    UNIQUE(region_name)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regional_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    region_name TEXT NOT NULL,
                    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    risk_level TEXT,
                    risk_score REAL,
                    indicators TEXT,  -- JSON array
                    predictions_data TEXT,  -- JSON
                    UNIQUE(region_name, prediction_date)
                )
            """)
            
            # Kontexträume für Länder
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS country_context_spaces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    country_code TEXT UNIQUE NOT NULL,
                    country_name TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    risk_score REAL DEFAULT 0.0,
                    risk_level TEXT DEFAULT 'MINIMAL',
                    climate_indicators TEXT,  -- JSON array
                    conflict_indicators TEXT,  -- JSON array
                    future_risks TEXT,  -- JSON array
                    context_summary TEXT,
                    data_sources TEXT,  -- JSON array
                    geojson TEXT,  -- GeoJSON für Länder-Polygone
                    bbox TEXT,  -- JSON bounding box
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Indizes für Performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_source ON records(source_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_domain ON records(source_domain)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_publish_date ON records(publish_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_region ON records(region)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_fetched_at ON records(fetched_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_country_code ON records(primary_country_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_records_coordinates ON records(primary_latitude, primary_longitude)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_crawl_jobs_status ON crawl_jobs(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_crawl_jobs_source ON crawl_jobs(source_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_geo_locations_record ON geo_locations(record_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_geo_locations_coordinates ON geo_locations(latitude, longitude)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_spaces_country ON country_context_spaces(country_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_spaces_risk ON country_context_spaces(risk_level)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_spaces_coordinates ON country_context_spaces(latitude, longitude)")
            
            logger.info("Database initialized successfully")
    
    def insert_record(self, record: PageRecord) -> Optional[tuple]:
        """Füge einen Record in die Datenbank ein. Returns (record_id, is_new) oder None"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Prüfe ob URL bereits existiert
            cursor.execute("SELECT id FROM records WHERE url = ?", (record.url,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                record_id = existing['id']
                cursor.execute("""
                    UPDATE records SET
                        title = ?,
                        summary = ?,
                        publish_date = ?,
                        region = ?,
                        content_type = ?,
                        language = ?,
                        full_text = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    record.title,
                    record.summary,
                    record.publish_date,
                    record.region,
                    record.content_type,
                    record.language,
                    getattr(record, 'full_text', None),
                    record_id
                ))
                is_new = False
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO records (
                        url, source_domain, source_name, fetched_at,
                        title, summary, publish_date, region,
                        content_type, language, full_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.url,
                    record.source_domain,
                    record.source_name,
                    record.fetched_at,
                    record.title,
                    record.summary,
                    record.publish_date,
                    record.region,
                    record.content_type,
                    record.language,
                    getattr(record, 'full_text', None)
                ))
                record_id = cursor.lastrowid
                is_new = True
            
            # Insert topics (entferne Duplikate)
            cursor.execute("DELETE FROM record_topics WHERE record_id = ?", (record_id,))
            unique_topics = list(set(record.topics)) if record.topics else []  # Entferne Duplikate
            for topic in unique_topics:
                if topic:  # Nur nicht-leere Topics
                    cursor.execute(
                        "INSERT OR IGNORE INTO record_topics (record_id, topic) VALUES (?, ?)",
                        (record_id, topic)
                    )
            
            # Insert links
            cursor.execute("DELETE FROM record_links WHERE record_id = ?", (record_id,))
            for link in record.links:
                cursor.execute(
                    "INSERT INTO record_links (record_id, link_url) VALUES (?, ?)",
                    (record_id, link)
                )
            
            # Insert images
            cursor.execute("DELETE FROM record_images WHERE record_id = ?", (record_id,))
            for image_url in record.image_urls:
                cursor.execute(
                    "INSERT INTO record_images (record_id, image_url) VALUES (?, ?)",
                    (record_id, image_url)
                )
            
            # Insert source-specific data
            if isinstance(record, NASARecord):
                cursor.execute("DELETE FROM nasa_records WHERE record_id = ?", (record_id,))
                cursor.execute("""
                    INSERT INTO nasa_records (record_id, environmental_indicators, satellite_source)
                    VALUES (?, ?, ?)
                """, (
                    record_id,
                    json.dumps(record.environmental_indicators),
                    record.satellite_source
                ))
            
            elif isinstance(record, UNPressRecord):
                cursor.execute("DELETE FROM un_press_records WHERE record_id = ?", (record_id,))
                cursor.execute("""
                    INSERT INTO un_press_records (record_id, meeting_coverage, security_council, speakers)
                    VALUES (?, ?, ?, ?)
                """, (
                    record_id,
                    1 if record.meeting_coverage else 0,
                    1 if record.security_council else 0,
                    json.dumps(record.speakers)
                ))
            
            elif isinstance(record, WFPRecord):
                cursor.execute("DELETE FROM wfp_records WHERE record_id = ?", (record_id,))
                cursor.execute("""
                    INSERT INTO wfp_records (record_id, crisis_type, affected_population)
                    VALUES (?, ?, ?)
                """, (record_id, record.crisis_type, record.affected_population))
            
            elif isinstance(record, WorldBankRecord):
                cursor.execute("DELETE FROM worldbank_records WHERE record_id = ?", (record_id,))
                cursor.execute("""
                    INSERT INTO worldbank_records (record_id, country, sector, project_id)
                    VALUES (?, ?, ?, ?)
                """, (record_id, record.country, record.sector, record.project_id))
            
            return (record_id, is_new)
    
    def insert_records_batch(self, records: List[PageRecord]) -> Dict[str, int]:
        """Füge mehrere Records in einem Batch ein"""
        stats = {'new': 0, 'updated': 0, 'total': len(records)}
        
        for record in records:
            result = self.insert_record(record)
            if result:
                record_id, is_new = result
                if is_new:
                    stats['new'] += 1
                else:
                    stats['updated'] += 1
        
        return stats
    
    def get_records(
        self,
        source_name: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: str = 'fetched_at DESC'
    ) -> List[Dict[str, Any]]:
        """Hole Records aus der Datenbank"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM records WHERE 1=1"
            params = []
            
            if source_name:
                query += " AND source_name = ?"
                params.append(source_name)
            
            query += f" ORDER BY {order_by}"
            
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to dicts and enrich with related data
            records = []
            for row in rows:
                record = dict(row)
                
                # Get topics
                cursor.execute("SELECT topic FROM record_topics WHERE record_id = ?", (row['id'],))
                record['topics'] = [r['topic'] for r in cursor.fetchall()]
                
                # Get links
                cursor.execute("SELECT link_url FROM record_links WHERE record_id = ?", (row['id'],))
                record['links'] = [r['link_url'] for r in cursor.fetchall()]
                
                # Get images
                cursor.execute("SELECT image_url FROM record_images WHERE record_id = ?", (row['id'],))
                record['image_urls'] = [r['image_url'] for r in cursor.fetchall()]
                
                # Get source-specific data
                if row['source_name'] == 'NASA':
                    cursor.execute("SELECT * FROM nasa_records WHERE record_id = ?", (row['id'],))
                    nasa_data = cursor.fetchone()
                    if nasa_data:
                        record['nasa_data'] = dict(nasa_data)
                        if record['nasa_data'].get('environmental_indicators'):
                            record['nasa_data']['environmental_indicators'] = json.loads(
                                record['nasa_data']['environmental_indicators']
                            )
                
                elif row['source_name'] == 'UN Press':
                    cursor.execute("SELECT * FROM un_press_records WHERE record_id = ?", (row['id'],))
                    un_data = cursor.fetchone()
                    if un_data:
                        record['un_data'] = dict(un_data)
                        if record['un_data'].get('speakers'):
                            record['un_data']['speakers'] = json.loads(record['un_data']['speakers'])
                
                elif row['source_name'] == 'WFP':
                    cursor.execute("SELECT * FROM wfp_records WHERE record_id = ?", (row['id'],))
                    wfp_data = cursor.fetchone()
                    if wfp_data:
                        record['wfp_data'] = dict(wfp_data)
                
                elif row['source_name'] == 'World Bank':
                    cursor.execute("SELECT * FROM worldbank_records WHERE record_id = ?", (row['id'],))
                    wb_data = cursor.fetchone()
                    if wb_data:
                        record['worldbank_data'] = dict(wb_data)
                
                records.append(record)
            
            return records
    
    def create_crawl_job(self, source_name: str, urls_count: int) -> int:
        """Erstelle einen neuen Crawl-Job"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO crawl_jobs (source_name, urls_count, status)
                VALUES (?, ?, 'pending')
            """, (source_name, urls_count))
            return cursor.lastrowid
    
    def update_crawl_job(
        self,
        job_id: int,
        status: str,
        records_extracted: int = 0,
        records_new: int = 0,
        records_updated: int = 0,
        error_message: Optional[str] = None
    ):
        """Update einen Crawl-Job"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            update_fields = ["status = ?"]
            params = [status]
            
            if status == 'running' and not error_message:
                update_fields.append("started_at = CURRENT_TIMESTAMP")
            elif status in ['completed', 'failed']:
                update_fields.append("completed_at = CURRENT_TIMESTAMP")
            
            if records_extracted > 0:
                update_fields.append("records_extracted = ?")
                params.append(records_extracted)
            
            if records_new > 0:
                update_fields.append("records_new = ?")
                params.append(records_new)
            
            if records_updated > 0:
                update_fields.append("records_updated = ?")
                params.append(records_updated)
            
            if error_message:
                update_fields.append("error_message = ?")
                params.append(error_message)
            
            params.append(job_id)
            
            cursor.execute(
                f"UPDATE crawl_jobs SET {', '.join(update_fields)} WHERE id = ?",
                params
            )
    
    def get_crawl_jobs(
        self,
        source_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Hole Crawl-Jobs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM crawl_jobs WHERE 1=1"
            params = []
            
            if source_name:
                query += " AND source_name = ?"
                params.append(source_name)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Hole Datenbank-Statistiken"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total records
            cursor.execute("SELECT COUNT(*) as count FROM records")
            stats['total_records'] = cursor.fetchone()['count']
            
            # Records per source
            cursor.execute("""
                SELECT source_name, COUNT(*) as count
                FROM records
                GROUP BY source_name
            """)
            stats['records_by_source'] = {row['source_name']: row['count'] for row in cursor.fetchall()}
            
            # Recent records (last 24h)
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM records
                WHERE fetched_at > datetime('now', '-1 day')
            """)
            stats['records_last_24h'] = cursor.fetchone()['count']
            
            # Records with coordinates
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM records
                WHERE primary_latitude IS NOT NULL 
                AND primary_longitude IS NOT NULL
            """)
            stats['records_with_coordinates'] = cursor.fetchone()['count']
            
            # Records by country code
            cursor.execute("""
                SELECT primary_country_code, COUNT(*) as count
                FROM records
                WHERE primary_country_code IS NOT NULL
                GROUP BY primary_country_code
                ORDER BY count DESC
                LIMIT 10
            """)
            stats['records_by_country'] = {row['primary_country_code']: row['count'] for row in cursor.fetchall()}
            
            # Crawl jobs statistics
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM crawl_jobs
                GROUP BY status
            """)
            stats['crawl_jobs_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Latest crawl job
            cursor.execute("""
                SELECT * FROM crawl_jobs
                ORDER BY created_at DESC
                LIMIT 1
            """)
            latest = cursor.fetchone()
            if latest:
                stats['latest_crawl_job'] = dict(latest)
            
            return stats

