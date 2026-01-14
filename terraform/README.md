# OpenStack Terraform Deployment für H-DA Cloud

Dieses Terraform-Projekt ermöglicht die automatisierte Verwaltung von OpenStack-Instanzen auf der H-DA Cloud.

## 🚀 Schnellstart

```bash
# 1. In das Terraform-Verzeichnis wechseln
cd terraform

# 2. Verfügbare Ressourcen anzeigen
python scripts/list_openstack_resources.py

# 3. Konfiguration erstellen
cp terraform.tfvars.example terraform.tfvars
# Passe die Werte in terraform.tfvars an

# 4. Server erstellen
make apply

# 5. Per SSH verbinden
make ssh
```

## 📋 Voraussetzungen

- **Terraform** >= 1.0.0
- **Python** >= 3.8 (für Hilfsskripte)
- **OpenStack CLI** (optional, für manuelle Befehle)

### Installation

```bash
# Terraform installieren (macOS)
brew install terraform

# Oder auf Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# OpenStack SDK für Python
pip install openstacksdk rich
```

## 📁 Projektstruktur

```
terraform/
├── provider.tf          # OpenStack Provider Konfiguration
├── versions.tf          # Terraform & Provider Versionen
├── variables.tf         # Input Variablen
├── main.tf              # Hauptressourcen (Server, Security Groups, etc.)
├── outputs.tf           # Output Werte (IPs, SSH-Befehle, etc.)
├── data.tf              # Data Sources für verfügbare Ressourcen
├── cleanup.tf           # Referenz für Cleanup-Operationen
├── terraform.tfvars.example  # Beispiel-Konfiguration
├── Makefile             # Komfortable Befehle
├── keys/                # Generierte SSH Keys (gitignored)
└── scripts/
    ├── list_openstack_resources.py  # Zeigt verfügbare Ressourcen
    └── delete_all_instances.py      # Löscht alle Instanzen
```

## ⚙️ Konfiguration

### OpenStack Credentials

Die Authentifizierung erfolgt über Application Credentials aus der `clouds.yaml`:

```yaml
# ~/.config/openstack/clouds.yaml
clouds:
  openstack:
    auth:
      auth_url: https://h-da.cloud:13000
      application_credential_id: "ba44dda4814e443faba80ae101d704a8"
      application_credential_secret: "Wesen"
    region_name: "eu-central"
    interface: "public"
    identity_api_version: 3
    auth_type: "v3applicationcredential"
```

### terraform.tfvars

Kopiere `terraform.tfvars.example` zu `terraform.tfvars` und passe an:

```hcl
# Server Konfiguration
server_name = "mein-server"
image_name  = "Ubuntu 22.04"
flavor_name = "m1.small"

# Netzwerk
network_name       = "private-network"
assign_floating_ip = true
floating_ip_pool   = "public"

# SSH
ssh_key_name     = "mein-key"
generate_ssh_key = true
```

## 🔧 Verfügbare Befehle

| Befehl | Beschreibung |
|--------|--------------|
| `make init` | Terraform initialisieren |
| `make plan` | Änderungen vorschauen |
| `make apply` | Server erstellen |
| `make destroy` | Alle Ressourcen löschen |
| `make ssh` | SSH-Verbindung herstellen |
| `make output` | Server-Informationen anzeigen |
| `make list-resources` | OpenStack Ressourcen auflisten |
| `make clean` | Terraform State löschen |

## 🖥️ Verfügbare Flavors (typisch)

| Flavor | vCPUs | RAM | Disk |
|--------|-------|-----|------|
| m1.tiny | 1 | 512 MB | 1 GB |
| m1.small | 1 | 2 GB | 20 GB |
| m1.medium | 2 | 4 GB | 40 GB |
| m1.large | 4 | 8 GB | 80 GB |
| m1.xlarge | 8 | 16 GB | 160 GB |

> **Tipp:** Führe `python scripts/list_openstack_resources.py` aus, um die tatsächlich verfügbaren Flavors zu sehen!

## 🔑 SSH Zugang

Nach dem Deployment wird automatisch ein SSH-Key generiert:

```bash
# Key-Pfad anzeigen
terraform output ssh_key_path

# SSH-Befehl anzeigen
terraform output ssh_command

# Oder direkt verbinden
make ssh
```

Der generierte Key liegt unter `keys/geospatial-key.pem`.

## 🗑️ Alle Instanzen löschen

### Option 1: Terraform (empfohlen)

```bash
make destroy
```

### Option 2: Python-Skript (für alle Server)

```bash
python scripts/delete_all_instances.py
```

### Option 3: OpenStack CLI

```bash
# Einzelnen Server löschen
openstack --os-cloud openstack server delete <server_name>

# Alle Server löschen
openstack --os-cloud openstack server list -f value -c ID | xargs -I {} openstack --os-cloud openstack server delete {}
```

## 🛠️ Troubleshooting

### Verbindungsfehler

```bash
# Prüfe clouds.yaml
cat ~/.config/openstack/clouds.yaml

# Teste Verbindung
openstack --os-cloud openstack server list
```

### Image/Flavor nicht gefunden

```bash
# Zeige verfügbare Ressourcen
python scripts/list_openstack_resources.py
```

### SSH-Verbindung fehlgeschlagen

1. Prüfe ob Floating IP zugewiesen ist
2. Warte auf Server-Start (cloud-init kann 2-3 Minuten dauern)
3. Prüfe Security Groups

```bash
# Server-Status
openstack --os-cloud openstack server show <server_name>

# Security Groups prüfen
openstack --os-cloud openstack security group rule list ssh-access
```

## 📊 Outputs nach dem Deployment

Nach `make apply` erhältst du:

- **server_id**: OpenStack Server ID
- **server_floating_ip**: Öffentliche IP für SSH
- **ssh_command**: Fertiger SSH-Befehl
- **connection_info**: Alle Verbindungsdetails

## 🔒 Sicherheit

- SSH-Keys werden lokal generiert und sind in `.gitignore`
- `terraform.tfvars` enthält sensible Daten und ist gitignored
- Security Group erlaubt nur SSH (22), HTTP (80), HTTPS (443)

## 📚 Weiterführende Links

- [Terraform OpenStack Provider Docs](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs)
- [OpenStack SDK Python](https://docs.openstack.org/openstacksdk/latest/)
- [H-DA Cloud Dokumentation](https://h-da.cloud)

