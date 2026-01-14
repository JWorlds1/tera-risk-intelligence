# OpenStack Integration Setup

Diese Anleitung erklärt, wie Sie den OpenStack Client für Ihr Geospatial Intelligence Projekt einrichten.

## Voraussetzungen

- Python 3.8+
- Zugriff auf einen OpenStack Cloud (z.B. HDA Cloud)
- OpenStack Benutzerdaten (Username, Password, Project, etc.)

## Installation

Die OpenStack Client Abhängigkeiten sind bereits in `backend/requirements.txt` enthalten. Installieren Sie sie mit:

```bash
pip install -r backend/requirements.txt
```

Oder installieren Sie nur die OpenStack Pakete:

```bash
pip install python-openstackclient openstacksdk python-novaclient python-glanceclient python-neutronclient python-cinderclient python-keystoneclient
```

## Konfiguration

### Schritt 1: Interaktives Setup

Führen Sie das Setup-Script aus:

```bash
python backend/openstack/setup.py
```

Das Script fragt Sie nach:
- **OpenStack Identity URL** (z.B. `https://identity.hda-cloud.de:5000/v3`)
- **Project Name** (Ihr Projekt-Name)
- **Project Domain Name** (meist `default`)
- **Username** (Ihr Benutzername)
- **User Domain Name** (meist `default`)
- **Password** (wird sicher abgefragt)
- **Region Name** (z.B. `RegionOne`)
- **Interface** (public/internal/admin)

Die Konfiguration wird gespeichert in:
- `~/.config/openstack/clouds.yaml` (ohne Passwort)
- `~/.config/openstack/secure.yaml` (mit Passwort, optional)

### Schritt 2: Verbindung testen

Testen Sie die Verbindung:

```bash
python backend/openstack/test_connection.py
```

Oder mit einem spezifischen Cloud-Namen:

```bash
python backend/openstack/test_connection.py hda-cloud
```

### Schritt 3: Ressourcen auflisten

Liste alle verfügbaren Ressourcen auf:

```bash
python backend/openstack/list_resources.py
```

## Verwendung im Code

### Einfache Verwendung

```python
from backend.openstack import OpenStackClient

# Client initialisieren
client = OpenStackClient(cloud_name="hda-cloud")

# Verbindung herstellen
if client.connect():
    # Server auflisten
    servers = client.list_servers()
    for server in servers:
        print(f"Server: {server['name']} - Status: {server['status']}")
    
    # Neuen Server erstellen
    server = client.create_server(
        name="my-server",
        image="Ubuntu 22.04",
        flavor="m1.small",
        network="private-network"
    )
```

### Erweiterte Verwendung

```python
from backend.openstack import OpenStackClient, OpenStackConfigManager

# Konfiguration verwalten
config_manager = OpenStackConfigManager()

# Konfiguration laden
config = config_manager.load_config()

# Validieren
if config_manager.validate_config(config):
    print("Konfiguration ist gültig")

# Client mit benutzerdefiniertem Config-Verzeichnis
client = OpenStackClient(
    cloud_name="hda-cloud",
    config_dir="/custom/path"
)
```

## Verfügbare Operationen

### Server-Management

- `list_servers(detailed=False)` - Liste alle Server
- `get_server(server_id)` - Hole Server-Details
- `create_server(...)` - Erstelle neuen Server
- `delete_server(server_id)` - Lösche Server

### Ressourcen-Auflistung

- `list_images()` - Liste alle Images
- `list_flavors()` - Liste alle Flavors
- `list_networks()` - Liste alle Networks
- `list_security_groups()` - Liste alle Security Groups

### Visualisierung

- `print_servers_table(servers)` - Zeige Server in schöner Tabelle

## Beispiel: Server für HPC-Berechnungen erstellen

```python
from backend.openstack import OpenStackClient

client = OpenStackClient(cloud_name="hda-cloud")

if client.connect():
    # Erstelle Server für HPC-Berechnungen
    server = client.create_server(
        name="hpc-worker-01",
        image="Ubuntu 22.04",
        flavor="m1.large",  # Mehr RAM/CPU für HPC
        network="private-network",
        key_name="my-ssh-key",
        security_groups=["default", "hpc-access"],
        user_data="""
        #!/bin/bash
        apt-get update
        apt-get install -y python3-pip
        pip3 install mpi4py numpy pandas
        """
    )
    
    if server:
        print(f"Server erstellt: {server['id']}")
```

## Umgebungsvariablen (Alternative)

Statt `clouds.yaml` können Sie auch Umgebungsvariablen verwenden:

```bash
export OS_AUTH_URL=https://identity.hda-cloud.de:5000/v3
export OS_PROJECT_NAME=my-project
export OS_PROJECT_DOMAIN_NAME=default
export OS_USERNAME=my-username
export OS_USER_DOMAIN_NAME=default
export OS_PASSWORD=my-password
export OS_REGION_NAME=RegionOne
```

## Troubleshooting

### Verbindungsfehler

1. Prüfen Sie die `clouds.yaml` Datei:
   ```bash
   cat ~/.config/openstack/clouds.yaml
   ```

2. Testen Sie mit dem OpenStack CLI:
   ```bash
   openstack --os-cloud hda-cloud server list
   ```

3. Prüfen Sie SSL-Zertifikate:
   - Setzen Sie `verify: false` in `clouds.yaml` wenn nötig

### Authentifizierungsfehler

- Stellen Sie sicher, dass Username, Password und Project korrekt sind
- Prüfen Sie die Domain-Namen (Project Domain, User Domain)
- Kontaktieren Sie Ihren OpenStack Administrator

### Ressourcen nicht gefunden

- Prüfen Sie, ob Sie die richtige Region verwenden
- Stellen Sie sicher, dass Sie die richtigen Berechtigungen haben
- Liste verfügbare Ressourcen mit `list_resources.py`

## Integration mit dem Projekt

Die OpenStack Integration kann für folgende Zwecke verwendet werden:

1. **HPC-Worker-Instanzen**: Automatische Erstellung von Compute-Instanzen für verteilte Berechnungen
2. **Datenbank-Instanzen**: PostgreSQL-Instanzen für strukturierte Daten
3. **Storage-Volumes**: Zusätzlicher Speicher für große Datensätze
4. **Networking**: Konfiguration von Netzwerken für Cluster-Kommunikation

## Weitere Ressourcen

- [OpenStack Python SDK Dokumentation](https://docs.openstack.org/openstacksdk/latest/)
- [OpenStack API Quick Start](https://docs.openstack.org/api-quick-start/)
- [OpenStackClient Dokumentation](https://docs.openstack.org/python-openstackclient/latest/)

## Support

Bei Problemen:
1. Prüfen Sie die Logs in `~/.config/openstack/`
2. Testen Sie mit dem OpenStack CLI direkt
3. Kontaktieren Sie Ihren OpenStack Administrator (HDA)

