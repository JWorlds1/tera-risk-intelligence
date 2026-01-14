# 💾 Storage-Lösung für Geospatial Intelligence

## 🔍 Problem-Analyse

**Swift (Object Storage):** 401 Unauthorized - Application Credentials haben keine Berechtigung
**Cinder (Block Storage):** ✅ Verfügbar und funktioniert

## ✅ Empfohlene Lösung: Hybrid Storage

### Strategie:

```
┌─────────────────────────────────────────────────┐
│  Lokaler Speicher (Aktive Daten)               │
│  ─────────────────────────────────────────────  │
│  data/                                          │
│  ├── climate_conflict.db                        │
│  ├── json/                                      │
│  ├── csv/                                       │
│  ├── parquet/                                   │
│  └── analytics/                                 │
│                                                 │
│  → Schneller Zugriff                           │
│  → Aktive Verarbeitung                         │
└─────────────────────────────────────────────────┘
                    │
                    │ Backup/Sync
                    ▼
┌─────────────────────────────────────────────────┐
│  OpenStack Block Storage (Backups)              │
│  ─────────────────────────────────────────────  │
│  Volumes:                                       │
│  ├── geospatial-backup-01 (100 GB)             │
│  ├── geospatial-backup-02 (100 GB)             │
│  └── ...                                        │
│                                                 │
│  → Archivierung                                 │
│  → Disaster Recovery                            │
└─────────────────────────────────────────────────┘
```

## 📊 Ressourcenverteilung (900 GB verfügbar)

### Option 1: Lokaler Speicher + OpenStack Backups (EMPFOHLEN)

```
Lokal (Development/Production):
├── 600 GB - Aktive Daten
│   ├── SQLite Datenbank
│   ├── Gecrawlte Daten (JSON, CSV, Parquet)
│   └── Cache
│
└── 300 GB - Reserve für Verarbeitung

OpenStack Block Storage (Backups):
├── Volume 1: 200 GB - Tägliche Backups
├── Volume 2: 200 GB - Wöchentliche Backups
└── Volume 3: 500 GB - Monatliche Archive
```

### Option 2: Direkter Block Storage (wenn Server verfügbar)

```
OpenStack Server + Volumes:
├── Server: m1.small (2 vCPU, 8 GB RAM)
├── Volume 1: 600 GB - crawled-data
├── Volume 2: 200 GB - processed-data
├── Volume 3: 50 GB - database-backups
└── Volume 4: 50 GB - embeddings
```

## 🛠️ Implementierung

### 1. Lokaler Speicher (Bereits vorhanden)

Ihr aktuelles System speichert bereits lokal:
- `data/climate_conflict.db` - SQLite Datenbank
- `data/json/` - JSON Exporte
- `data/csv/` - CSV Exporte
- `data/parquet/` - Parquet Dateien

### 2. OpenStack Backup-Integration

```python
from backend.openstack.storage_solution import HybridStorageSolution

storage = HybridStorageSolution()

# Erstelle Backup-Volume
storage.create_backup_volume("geospatial-backup-01", size_gb=200)

# Zeige Storage-Zusammenfassung
storage.show_storage_summary()
```

### 3. Automatische Backups

```bash
# Tägliches Backup-Script
python3 backend/openstack/storage_solution.py --create-volume geospatial-daily-backup --volume-size 200
```

## 📋 Nächste Schritte

### Schritt 1: Prüfe aktuelle Daten
```bash
python3 backend/openstack/storage_solution.py --summary
```

### Schritt 2: Erstelle Backup-Volumes
```bash
# Für tägliche Backups
python3 backend/openstack/storage_solution.py --create-volume geospatial-daily-backup --volume-size 200

# Für wöchentliche Archive
python3 backend/openstack/storage_solution.py --create-volume geospatial-weekly-archive --volume-size 500
```

### Schritt 3: Liste Volumes
```bash
python3 backend/openstack/storage_solution.py --list-volumes
```

## 🔄 Workflow

### Täglicher Workflow:

1. **Crawling** → Speichere lokal in `data/`
2. **Verarbeitung** → Parquet, CSV, Analysen
3. **Backup** → Upload zu OpenStack Volume (täglich)
4. **Archivierung** → Wöchentliche Archive zu größerem Volume

### Backup-Strategie:

```
Täglich:
  - SQLite DB → OpenStack Volume
  - Neue gecrawlte Daten → OpenStack Volume

Wöchentlich:
  - Vollständiges Archiv → Größeres Volume
  - Komprimierte Backups

Monatlich:
  - Langzeit-Archiv → Separates Volume
```

## 💡 Vorteile dieser Lösung:

✅ **Keine Swift-Berechtigung nötig** - Nutzt Cinder (Block Storage)
✅ **Schneller lokaler Zugriff** - Für aktive Verarbeitung
✅ **Sichere Backups** - Auf OpenStack Storage
✅ **Skalierbar** - Volumes können erweitert werden
✅ **Kosteneffizient** - Nur für Backups, nicht für aktive Daten

## 🚀 Für HPC-Worker später:

Wenn Sie später HPC-Worker haben:
- HPC-Worker können direkt auf OpenStack Volumes zugreifen
- Oder Daten von lokalen Backups kopieren
- Volumes können an HPC-Server angehängt werden

## 📝 Zusammenfassung:

**Aktuell:** Lokaler Speicher für aktive Daten ✅
**Backup:** OpenStack Block Storage Volumes ✅
**Später:** HPC-Worker können auf Volumes zugreifen ✅

Diese Lösung funktioniert **sofort** ohne zusätzliche Berechtigungen!

