# OpenStack Verbindungstest - Anleitung

## Status
✅ Konfiguration erstellt: `~/.config/openstack/clouds.yaml`
✅ Alle Scripts erstellt

## Test durchführen

**WICHTIG:** Führen Sie diese Befehle in einem Terminal aus (nicht über Cursor's integriertes Terminal, da dort ein bekanntes Problem besteht).

### Option 1: Vollständiger Test (empfohlen)
```bash
cd /Users/qed97/Geospatial_Intelligence
python3 test_openstack_complete.py
```

### Option 2: Schneller Test
```bash
cd /Users/qed97/Geospatial_Intelligence
python3 quick_test.py
```

### Option 3: Mit OpenStack CLI
```bash
openstack --os-cloud openstack server list
openstack --os-cloud openstack flavor list
openstack --os-cloud openstack image list
```

### Option 4: Mit dem Setup-Script
```bash
cd /Users/qed97/Geospatial_Intelligence
python3 setup_and_test_openstack.py
```

## Was wurde konfiguriert:

- **Cloud Name:** `openstack`
- **Auth URL:** `https://h-da.cloud:13000`
- **Application Credential ID:** `ba44dda4814e443faba80ae101d704a8`
- **Region:** `eu-central`
- **Interface:** `public`
- **Auth Type:** `v3applicationcredential`

## Erwartete Ergebnisse:

Wenn alles funktioniert, sollten Sie sehen:
- ✓ Verbindung erfolgreich
- Liste aller Server
- Liste aller Flavors
- Liste aller Images

## Falls es nicht funktioniert:

1. **Prüfen Sie Ihre VPN-Verbindung** (WireGuard)
2. **Prüfen Sie die Konfiguration:**
   ```bash
   cat ~/.config/openstack/clouds.yaml
   ```
3. **Testen Sie die URL manuell:**
   ```bash
   curl -k https://h-da.cloud:13000
   ```

## Verfügbare Scripts:

- `test_openstack_complete.py` - Vollständiger Test mit allen Methoden
- `quick_test.py` - Schneller einfacher Test
- `setup_and_test_openstack.py` - Setup und Test kombiniert
- `backend/openstack/update_config.py` - Konfiguration ändern

## Nächste Schritte nach erfolgreichem Test:

1. Server erstellen für HPC-Berechnungen
2. Images und Flavors für Ihr Projekt auswählen
3. Integration in Ihr Geospatial Intelligence Projekt

