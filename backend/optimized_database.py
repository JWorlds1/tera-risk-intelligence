#!/usr/bin/env python3
"""
Optimierte Datenbank-Operationen mit Batch-Inserts
"""
import sqlite3
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import json

from schemas import PageRecord


class OptimizedDatabaseManager:
    """Optimierte Datenbank-Operationen mit Batch-Processing"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = Path(__file__).parent / "data" / "climate_conflict.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self):
        """Erstelle Datenbank-Verbindung"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def insert_records_batch_optimized(
        self,
        records: List[PageRecord],
        batch_size: int = 100
    ) -> Dict[str, int]:
        """Optimiertes Batch-Insert mit Transaktionen"""
        stats = {'new': 0, 'updated': 0, 'total': len(records)}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Stelle sicher dass Tabelle existiert
            self._ensure_tables_exist(cursor)
            
            # Verarbeite in Batches
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                # Batch Insert mit INSERT OR IGNORE / UPDATE
                for record in batch:
                    try:
                        # Prüfe ob Record existiert
                        cursor.execute(
                            "SELECT id FROM records WHERE url = ?",
                            (record.url,)
                        )
                        existing = cursor.fetchone()
                        
                        if existing:
                            # Update
                            record_id = existing[0]
                            self._update_record(cursor, record_id, record)
                            stats['updated'] += 1
                        else:
                            # Insert
                            record_id = self._insert_record(cursor, record)
                            stats['new'] += 1
                        
                        # Insert Topics, Links, Images in Batch
                        if record_id:
                            self._insert_related_data_batch(cursor, record_id, record)
                    
                    except Exception as e:
                        print(f"Fehler beim Einfügen von Record {record.url}: {e}")
                        continue
                
                # Commit nach jedem Batch
                conn.commit()
        
        return stats
    
    def _ensure_tables_exist(self, cursor):
        """Stelle sicher dass alle Tabellen existieren"""
        # Records Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                source_domain TEXT,
                source_name TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                title TEXT,
                summary TEXT,
                publish_date TEXT,
                region TEXT,
                content_type TEXT,
                language TEXT DEFAULT 'en',
                full_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Topics Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS record_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER,
                topic TEXT,
                FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE,
                UNIQUE(record_id, topic)
            )
        """)
        
        # Links Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS record_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER,
                link_url TEXT,
                link_text TEXT,
                FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
            )
        """)
        
        # Images Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS record_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER,
                image_url TEXT,
                alt_text TEXT,
                FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
            )
        """)
        
        # Indizes für Performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_records_url ON records(url)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_records_source ON records(source_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_records_fetched ON records(fetched_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_topics_record ON record_topics(record_id)
        """)
    
    def _insert_record(self, cursor, record: PageRecord) -> int:
        """Füge einen Record ein"""
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
            record.fetched_at or datetime.now(),
            record.title,
            record.summary,
            record.publish_date.isoformat() if record.publish_date else None,
            record.region,
            record.content_type,
            record.language or 'en',
            record.full_text
        ))
        return cursor.lastrowid
    
    def _update_record(self, cursor, record_id: int, record: PageRecord):
        """Update einen Record"""
        cursor.execute("""
            UPDATE records SET
                source_domain = ?,
                source_name = ?,
                fetched_at = ?,
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
            record.source_domain,
            record.source_name,
            record.fetched_at or datetime.now(),
            record.title,
            record.summary,
            record.publish_date.isoformat() if record.publish_date else None,
            record.region,
            record.content_type,
            record.language or 'en',
            record.full_text,
            record_id
        ))
    
    def _insert_related_data_batch(
        self,
        cursor,
        record_id: int,
        record: PageRecord
    ):
        """Füge verwandte Daten (Topics, Links, Images) in Batch ein"""
        # Topics
        if record.topics:
            topics_data = [(record_id, topic) for topic in record.topics]
            cursor.executemany("""
                INSERT OR IGNORE INTO record_topics (record_id, topic)
                VALUES (?, ?)
            """, topics_data)
        
        # Links (falls vorhanden)
        if hasattr(record, 'links') and record.links:
            links_data = [
                (record_id, link.get('url', ''), link.get('text', ''))
                for link in record.links
            ]
            cursor.executemany("""
                INSERT INTO record_links (record_id, link_url, link_text)
                VALUES (?, ?, ?)
            """, links_data)
        
        # Images (falls vorhanden)
        if hasattr(record, 'images') and record.images:
            images_data = [
                (record_id, img.get('url', ''), img.get('alt', ''))
                for img in record.images
            ]
            cursor.executemany("""
                INSERT INTO record_images (record_id, image_url, alt_text)
                VALUES (?, ?, ?)
            """, images_data)
    
    def insert_enrichments_batch(
        self,
        enrichments: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """Füge Enrichments in Batch ein"""
        saved_count = 0
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Erstelle Tabelle falls nicht vorhanden
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS batch_enrichment (
                    record_id INTEGER PRIMARY KEY,
                    datapoints TEXT,
                    ipcc_metrics TEXT,
                    extracted_numbers TEXT,
                    firecrawl_data TEXT,
                    enrichment_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
                )
            """)
            
            # Batch Insert
            for i in range(0, len(enrichments), batch_size):
                batch = enrichments[i:i + batch_size]
                
                enrichment_data = []
                for enrichment in batch:
                    record_id = enrichment.get('record_id')
                    if not record_id:
                        continue
                    
                    enrichment_data.append((
                        record_id,
                        json.dumps(enrichment.get('enrichment', {}).get('datapoints', {})),
                        json.dumps(enrichment.get('enrichment', {}).get('ipcc_metrics', {})),
                        json.dumps(enrichment.get('enrichment', {}).get('extracted_numbers', {})),
                        json.dumps(enrichment.get('enrichment', {}).get('firecrawl_data', {}))
                    ))
                
                if enrichment_data:
                    cursor.executemany("""
                        INSERT OR REPLACE INTO batch_enrichment (
                            record_id, datapoints, ipcc_metrics,
                            extracted_numbers, firecrawl_data
                        ) VALUES (?, ?, ?, ?, ?)
                    """, enrichment_data)
                    
                    saved_count += len(enrichment_data)
                
                # Commit nach jedem Batch
                conn.commit()
        
        return saved_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Gebe Datenbank-Statistiken"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Gesamt Records
            cursor.execute("SELECT COUNT(*) FROM records")
            stats['total_records'] = cursor.fetchone()[0]
            
            # Records pro Quelle
            cursor.execute("""
                SELECT source_name, COUNT(*) as count
                FROM records
                GROUP BY source_name
            """)
            stats['records_by_source'] = {
                row[0]: row[1] for row in cursor.fetchall()
            }
            
            # Enrichments
            cursor.execute("SELECT COUNT(*) FROM batch_enrichment")
            stats['total_enrichments'] = cursor.fetchone()[0]
            
            # Records mit Region
            cursor.execute("SELECT COUNT(*) FROM records WHERE region IS NOT NULL")
            stats['records_with_region'] = cursor.fetchone()[0]
            
            return stats



