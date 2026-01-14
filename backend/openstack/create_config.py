#!/usr/bin/env python3
"""Erstellt OpenStack Konfiguration mit gegebenen Credentials"""
import yaml
import os
from pathlib import Path

# Credentials
USERNAME = "stioarmou"
PASSWORD = "dezjom-bagvE1-rargyw"
PROJECT_NAME = "stioarmou"  # Oft gleich wie Username
PROJECT_DOMAIN = "default"
USER_DOMAIN = "default"
AUTH_URL = "https://identity.hda-cloud.de:5000/v3"  # Standard HDA Cloud URL
REGION = "RegionOne"

# Erstelle Config-Verzeichnis
config_dir = Path.home() / ".config" / "openstack"
config_dir.mkdir(parents=True, exist_ok=True)

clouds_yaml = config_dir / "clouds.yaml"
secure_yaml = config_dir / "secure.yaml"

# clouds.yaml (ohne Passwort)
clouds_config = {
    "clouds": {
        "hda-cloud": {
            "auth": {
                "auth_url": AUTH_URL,
                "project_name": PROJECT_NAME,
                "project_domain_name": PROJECT_DOMAIN,
                "username": USERNAME,
                "user_domain_name": USER_DOMAIN,
            },
            "region_name": REGION,
            "interface": "public",
            "verify": True,
        }
    }
}

# secure.yaml (mit Passwort)
secure_config = {
    "clouds": {
        "hda-cloud": {
            "auth": {
                "password": PASSWORD
            }
        }
    }
}

# Speichere clouds.yaml
with open(clouds_yaml, 'w') as f:
    yaml.dump(clouds_config, f, default_flow_style=False, sort_keys=False)

# Speichere secure.yaml
with open(secure_yaml, 'w') as f:
    yaml.dump(secure_config, f, default_flow_style=False, sort_keys=False)

# Setze sichere Berechtigungen für secure.yaml
os.chmod(secure_yaml, 0o600)

print(f"✓ Konfiguration erstellt:")
print(f"  {clouds_yaml}")
print(f"  {secure_yaml}")

