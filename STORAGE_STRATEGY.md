# 📦 Storage-Strategie für Geospatial Intelligence Projekt

## 🎯 Ziel

**900 GB verfügbarer Speicher** für gecrawlte Daten optimal nutzen mit Fokus auf **maximale Arbeitsspeicher-Ressourcen**.

## 💾 OpenStack Storage-Optionen

### 1. Object Storage (Swift) - **EMPFOHLEN** ✅

**Vorteile:**
- ✅ Skalierbar bis zu mehreren TB
- ✅ Geeignet für viele kleine Dateien (gecrawlte Daten)
- ✅ Automatische Replikation und Backup
- ✅ Günstig für Archivierung
- ✅ REST API für einfache Integration
- ✅ Keine Limits auf Dateigröße

**Verwendung:**
- Gecrawlte HTML/JSON/CSV Dateien
- Bilder und Medien
- Archivierte Daten
- Backup der SQLite-Datenbank

### 2. Block Storage (Cinder) - Alternative

**Vorteile:**
- ✅ Höhere Performance
- ✅ Geeignet für Datenbanken
- ✅ Direkter Dateisystem-Zugriff

**Nachteile:**
- ❌ Weniger flexibel
- ❌ Teurer
- ❌ Feste Größe

**Verwendung:**
- PostgreSQL-Datenbank (falls Migration)
- Performance-kritische Daten

## 📊 Ressourcenverteilung (900 GB)

### Empfohlene Aufteilung:

```
┌─────────────────────────────────────────────────┐
│  OpenStack Object Storage (Swift)               │
│  ─────────────────────────────────────────────  │
│                                                  │
│  📁 Container: crawled-data                     │
│     └─ 600 GB (67%) - Gecrawlte Rohdaten       │
│        ├─ HTML/JSON Dateien                     │
│        ├─ Bilder                                │
│        └─ Medien                                │
│                                                  │
│  📁 Container: processed-data                   │
│     └─ 200 GB (22%) - Verarbeitete Daten        │
│        ├─ Parquet Dateien                       │
│        ├─ CSV Exporte                           │
│        └─ Analysen                              │
│                                                  │
│  📁 Container: database-backups                 │
│     └─ 50 GB (6%) - Datenbank-Backups          │
│        ├─ SQLite Snapshots                      │
│        └─ PostgreSQL Dumps                      │
│                                                  │
│  📁 Container: embeddings                       │
│     └─ 50 GB (5%) - Vektor-Embeddings          │
│        ├─ Text-Embeddings                       │
│        └─ Bild-Embeddings                       │
│                                                  │
└─────────────────────────────────────────────────┘

Gesamt: 900 GB
```

## 🏗️ Architektur-Integration

### Aktuelle Datenstruktur:

```
data/
├── climate_conflict.db          # SQLite Datenbank
├── json/                         # JSON Exporte
├── csv/                          # CSV Exporte
├── parquet/                      # Parquet Dateien
└── analytics/                    # Analysen
```

### Neue Struktur mit OpenStack:

```
Lokal (Development):
data/
├── climate_conflict.db          # SQLite (lokale Kopie)
└── cache/                        # Lokaler Cache

OpenStack Swift:
crawled-data/
├── raw/                          # Rohdaten
│   ├── nasa/                     # NASA Daten
│   ├── un_press/                 # UN Press Daten
│   └── worldbank/                # World Bank Daten
├── processed/                    # Verarbeitete Daten
└── metadata/                     # Metadaten

database-backups/
├── daily/                        # Tägliche Backups
└── weekly/                       # Wöchentliche Backups
```

## 🔄 Workflow-Integration

### 1. Crawling-Pipeline → OpenStack Storage

```python
# Nach erfolgreichem Crawling:
1. Speichere lokal (für schnellen Zugriff)
2. Upload zu OpenStack Swift (für Archivierung)
3. Update Metadaten in Datenbank
```

### 2. Automatischer Upload

```python
# Nach jedem Crawl-Job:
- Upload neue Dateien zu Swift
- Komprimiere große Dateien
- Erstelle Metadaten-Index
```

### 3. Datenbank-Backup

```python
# Täglich:
- SQLite → Swift Backup
- PostgreSQL Dump → Swift (falls Migration)
```

## 💻 Implementierung

### Storage Manager Integration

```python
from backend.openstack.storage_manager import OpenStackStorageManager

# Initialisierung
storage = OpenStackStorageManager()

# Nach Crawling
storage.upload_directory(
    local_dir="data/json",
    container_name="crawled-data",
    prefix="raw/nasa"
)

# Backup
storage.upload_file(
    local_path="data/climate_conflict.db",
    container_name="database-backups",
    object_name=f"daily/{date}.db"
)
```

## 📈 Performance-Optimierung

### Für maximale Arbeitsspeicher-Nutzung:

1. **Chunked Upload** für große Dateien
   - 100 MB Chunks
   - Parallele Uploads

2. **Kompression**
   - Gzip für Text-Dateien
   - Parquet für strukturierte Daten

3. **Caching-Strategie**
   - Lokaler Cache für häufig genutzte Daten
   - OpenStack für Archivierung

4. **Batch-Processing**
   - Upload in Batches
   - Retry-Logic

## 🎯 Nächste Schritte

1. ✅ **Storage-Optionen prüfen**
   ```bash
   python3 backend/openstack/check_storage.py
   ```

2. ✅ **Container erstellen**
   ```bash
   python3 backend/openstack/storage_manager.py --create-container crawled-data
   python3 backend/openstack/storage_manager.py --create-container processed-data
   python3 backend/openstack/storage_manager.py --create-container database-backups
   ```

3. ✅ **Integration in Crawling-Pipeline**
   - Storage Manager in Pipeline einbinden
   - Automatischer Upload nach Crawling

4. ✅ **Monitoring**
   - Storage-Usage Tracking
   - Automatische Alerts bei Quota

## 🔐 Sicherheit & Backup

- ✅ Automatische Replikation (Swift)
- ✅ Versionierung für wichtige Daten
- ✅ Tägliche Backups der Datenbank
- ✅ Verschlüsselung für sensible Daten

## 💰 Kosten-Optimierung

- ✅ Kompression reduziert Speicher
- ✅ Lifecycle-Policies (alte Daten → Archive)
- ✅ Intelligente Retention-Policies

