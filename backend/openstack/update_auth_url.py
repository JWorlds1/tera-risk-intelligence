#!/usr/bin/env python3
"""Aktualisiert die OpenStack Auth URL"""
import yaml
from pathlib import Path
import sys

config_dir = Path.home() / ".config" / "openstack"
clouds_yaml = config_dir / "clouds.yaml"

if len(sys.argv) < 2:
    print("Verwendung: python update_auth_url.py <neue-auth-url>")
    print("Beispiel: python update_auth_url.py https://keystone.example.com:5000/v3")
    sys.exit(1)

new_auth_url = sys.argv[1]

# Lade aktuelle Konfiguration
with open(clouds_yaml, 'r') as f:
    config = yaml.safe_load(f)

# Aktualisiere Auth URL
if "clouds" in config and "hda-cloud" in config["clouds"]:
    config["clouds"]["hda-cloud"]["auth"]["auth_url"] = new_auth_url
    
    # Speichere
    with open(clouds_yaml, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Auth URL aktualisiert zu: {new_auth_url}")
else:
    print("✗ Konfiguration nicht gefunden")
    sys.exit(1)

