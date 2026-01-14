#!/usr/bin/env python3
"""
OpenStack Test - Robuste Version ohne Versionsprüfung
"""
import sys
import yaml
from pathlib import Path

def test_connection():
    """Testet die OpenStack Verbindung"""
    print("=" * 60)
    print("OpenStack Verbindungstest")
    print("=" * 60)
    
    # Prüfe Config
    config_path = Path.home() / ".config" / "openstack" / "clouds.yaml"
    if not config_path.exists():
        print(f"✗ Konfiguration nicht gefunden: {config_path}")
        return False
    
    print(f"✓ Konfiguration gefunden: {config_path}")
    
    # Prüfe Imports
    try:
        from openstack import connection
        print("✓ openstacksdk importiert")
    except ImportError as e:
        print(f"✗ openstacksdk nicht installiert: {e}")
        print("Installiere mit: pip install openstacksdk")
        return False
    
    # Teste Verbindung Methode 1
    print("\nVersuche Verbindung (Methode 1)...")
    try:
        conn = connection.Connection(
            cloud='openstack',
            config_dir=str(Path.home() / ".config" / "openstack")
        )
        conn.authorize()
        print("✓ Verbindung erfolgreich!")
    except Exception as e:
        print(f"✗ Methode 1 fehlgeschlagen: {str(e)[:150]}")
        
        # Teste Verbindung Methode 2
        print("\nVersuche Verbindung (Methode 2)...")
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            cloud = config["clouds"]["openstack"]
            auth = cloud["auth"]
            
            conn = connection.Connection(
                auth_url=auth["auth_url"],
                application_credential_id=auth["application_credential_id"],
                application_credential_secret=auth["application_credential_secret"],
                region_name=cloud["region_name"],
                interface=cloud["interface"],
                identity_api_version=cloud.get("identity_api_version", 3),
                auth_type=cloud.get("auth_type", "v3applicationcredential")
            )
            conn.authorize()
            print("✓ Verbindung erfolgreich!")
        except Exception as e2:
            print(f"✗ Methode 2 fehlgeschlagen: {str(e2)[:150]}")
            return False
    
    # Teste Services
    print("\n" + "=" * 60)
    print("Teste OpenStack Services...")
    print("=" * 60)
    
    # Server
    try:
        servers = list(conn.compute.servers())
        print(f"\n✓ Compute Service: {len(servers)} Server gefunden")
        if servers:
            print("\nServer:")
            for s in servers[:10]:
                ip = ""
                try:
                    addresses = s.addresses or {}
                    for net_name, addr_list in addresses.items():
                        if addr_list:
                            for addr in addr_list:
                                if addr.get("version") == 4:
                                    ip = addr.get("addr", "")
                                    break
                            if ip:
                                break
                except:
                    pass
                print(f"  - {s.name:30} {s.status:10} IP: {ip}")
    except Exception as e:
        print(f"✗ Server-Liste Fehler: {str(e)[:100]}")
    
    # Flavors
    try:
        flavors = list(conn.compute.flavors())
        print(f"\n✓ Flavors: {len(flavors)} verfügbar")
        if flavors:
            print("\nFlavors (erste 10):")
            for f in flavors[:10]:
                print(f"  - {f.name:20} {f.vcpus:3} vCPUs  {f.ram:6} MB RAM  {f.disk:4} GB Disk")
    except Exception as e:
        print(f"✗ Flavors Fehler: {str(e)[:100]}")
    
    # Images
    try:
        images = list(conn.compute.images())
        print(f"\n✓ Images: {len(images)} verfügbar")
        if images:
            print("\nImages (erste 10):")
            for img in images[:10]:
                print(f"  - {img.name:40} {img.status}")
    except Exception as e:
        print(f"✗ Images Fehler: {str(e)[:100]}")
    
    # Networks
    try:
        networks = list(conn.network.networks())
        print(f"\n✓ Networks: {len(networks)} verfügbar")
    except Exception as e:
        print(f"✗ Networks Fehler: {str(e)[:100]}")
    
    print("\n" + "=" * 60)
    print("✓ VERBINDUNGSTEST ERFOLGREICH!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nAbgebrochen vom Benutzer")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

