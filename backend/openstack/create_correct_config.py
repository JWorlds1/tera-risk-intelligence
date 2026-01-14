#!/usr/bin/env python3
"""Erstellt korrekte OpenStack Konfiguration basierend auf der gegebenen clouds.yaml"""
import yaml
import os
from pathlib import Path

# Korrekte Konfiguration
clouds_config = {
    "clouds": {
        "openstack": {
            "auth": {
                "auth_url": "https://h-da.cloud:13000",
                "application_credential_id": "ba44dda4814e443faba80ae101d704a8",
                "application_credential_secret": "Wesen"
            },
            "region_name": "eu-central",
            "interface": "public",
            "identity_api_version": 3,
            "auth_type": "v3applicationcredential"
        }
    }
}

# Erstelle Config-Verzeichnis
config_dir = Path.home() / ".config" / "openstack"
config_dir.mkdir(parents=True, exist_ok=True)

clouds_yaml = config_dir / "clouds.yaml"

# Speichere clouds.yaml
with open(clouds_yaml, 'w') as f:
    yaml.dump(clouds_config, f, default_flow_style=False, sort_keys=False)

print(f"✓ Konfiguration erstellt:")
print(f"  Cloud Name: openstack")
print(f"  Auth URL: https://h-da.cloud:13000")
print(f"  Region: eu-central")
print(f"  Config: {clouds_yaml}")

