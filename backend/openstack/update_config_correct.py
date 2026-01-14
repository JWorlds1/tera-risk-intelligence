#!/usr/bin/env python3
"""Aktualisiert OpenStack Konfiguration mit korrekten Application Credentials"""
import yaml
import os
from pathlib import Path

# Korrekte Credentials
AUTH_URL = "https://h-da.cloud:13000"
AUTH_TYPE = "v3applicationcredential"
APPLICATION_CREDENTIAL_ID = "ba44dda4814e443faba80ae101d704a8"
APPLICATION_CREDENTIAL_SECRET = "Wesen"
REGION = "eu-central"
INTERFACE = "public"

# Erstelle Config-Verzeichnis
config_dir = Path.home() / ".config" / "openstack"
config_dir.mkdir(parents=True, exist_ok=True)

clouds_yaml = config_dir / "clouds.yaml"
secure_yaml = config_dir / "secure.yaml"

# clouds.yaml (ohne Secret)
clouds_config = {
    "clouds": {
        "hda-cloud": {
            "auth_type": AUTH_TYPE,
            "auth": {
                "auth_url": AUTH_URL,
                "application_credential_id": APPLICATION_CREDENTIAL_ID,
            },
            "region_name": REGION,
            "interface": INTERFACE,
            "verify": True,
        }
    }
}

# secure.yaml (mit Secret)
secure_config = {
    "clouds": {
        "hda-cloud": {
            "auth": {
                "application_credential_secret": APPLICATION_CREDENTIAL_SECRET
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

print(f"✓ Konfiguration aktualisiert:")
print(f"  Auth URL: {AUTH_URL}")
print(f"  Auth Type: {AUTH_TYPE}")
print(f"  Region: {REGION}")
print(f"  Config: {clouds_yaml}")
print(f"  Secure: {secure_yaml}")

