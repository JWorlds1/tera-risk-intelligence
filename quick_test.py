#!/usr/bin/env python3
"""Schneller OpenStack Test"""
import sys
from pathlib import Path

try:
    from openstack import connection
    
    print("=" * 60)
    print("OpenStack Quick Test")
    print("=" * 60)
    print("\n1. Lade Konfiguration...")
    
    conn = connection.Connection(
        cloud='openstack',
        config_dir=str(Path.home() / ".config" / "openstack")
    )
    
    print("2. Verbinde zu OpenStack...")
    conn.authorize()
    print("✓ Verbindung erfolgreich!")
    
    print("\n3. Liste Server auf...")
    servers = list(conn.compute.servers())
    print(f"✓ {len(servers)} Server gefunden")
    
    if servers:
        print("\nServer:")
        for s in servers:
            print(f"  - {s.name} ({s.status})")
    
    print("\n4. Liste Flavors auf...")
    flavors = list(conn.compute.flavors())
    print(f"✓ {len(flavors)} Flavors gefunden")
    
    print("\n5. Liste Images auf...")
    images = list(conn.compute.images())
    print(f"✓ {len(images)} Images gefunden")
    
    print("\n" + "=" * 60)
    print("✓ ALLES FUNKTIONIERT!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Fehler: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

