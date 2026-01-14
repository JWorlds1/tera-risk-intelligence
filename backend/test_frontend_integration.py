#!/usr/bin/env python3
"""
Test-Script für Frontend-Integration
Prüft ob alle API-Endpunkte funktionieren und Daten verfügbar sind
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:5000"

def test_api_endpoint(endpoint, description):
    """Teste einen API-Endpunkt"""
    print(f"\n🔍 Teste: {description}")
    print(f"   Endpoint: {endpoint}")
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Erfolg: {len(str(data))} Bytes")
            return True, data
        else:
            print(f"   ❌ Fehler: Status {response.status_code}")
            print(f"   Antwort: {response.text[:200]}")
            return False, None
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️  Server nicht erreichbar. Starte web_app.py!")
        return False, None
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return False, None

def test_frontend_files():
    """Prüfe ob Frontend-Dateien existieren"""
    print("\n📁 Prüfe Frontend-Dateien:")
    
    frontend_dir = Path("./data/frontend")
    required_files = [
        "complete_data.json",
        "map_data.geojson",
        "early_warning.json",
        "adaptation_recommendations.json",
        "causal_relationships.json"
    ]
    
    all_exist = True
    for filename in required_files:
        filepath = frontend_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"   ✅ {filename} ({size:,} Bytes)")
        else:
            print(f"   ❌ {filename} fehlt!")
            all_exist = False
    
    return all_exist

def main():
    print("=" * 60)
    print("🧪 Frontend-Integration Test")
    print("=" * 60)
    
    # 1. Prüfe Dateien
    files_ok = test_frontend_files()
    
    if not files_ok:
        print("\n⚠️  Frontend-Dateien fehlen!")
        print("   Führe aus: python3 backend/generate_frontend_data.py")
        return
    
    # 2. Teste API-Endpunkte
    print("\n" + "=" * 60)
    print("🌐 Teste API-Endpunkte")
    print("=" * 60)
    
    endpoints = [
        ("/api/frontend/map-data", "GeoJSON für Karte"),
        ("/api/frontend/complete-data", "Vollständige Frontend-Daten"),
        ("/api/frontend/early-warnings", "Frühwarnsystem-Daten"),
        ("/api/frontend/adaptation-recommendations", "Anpassungs-Empfehlungen"),
        ("/api/frontend/regions", "Regionale Gruppierung"),
    ]
    
    results = []
    for endpoint, description in endpoints:
        success, data = test_api_endpoint(endpoint, description)
        results.append((endpoint, success, data))
    
    # 3. Teste Location-Details
    print("\n" + "=" * 60)
    print("📍 Teste Location-Details")
    print("=" * 60)
    
    # Hole erste Location-ID
    complete_data_path = Path("./data/frontend/complete_data.json")
    if complete_data_path.exists():
        with open(complete_data_path, 'r') as f:
            complete_data = json.load(f)
        
        if complete_data.get('locations') and len(complete_data['locations']) > 0:
            first_location = complete_data['locations'][0]
            location_id = first_location.get('location_id')
            
            if location_id:
                success, data = test_api_endpoint(
                    f"/api/frontend/location/{location_id}",
                    f"Details für {first_location.get('location_name')}"
                )
                results.append((f"/api/frontend/location/{location_id}", success, data))
    
    # 4. Zusammenfassung
    print("\n" + "=" * 60)
    print("📊 Zusammenfassung")
    print("=" * 60)
    
    successful = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"\n✅ Erfolgreich: {successful}/{total}")
    print(f"❌ Fehlgeschlagen: {total - successful}/{total}")
    
    if successful == total:
        print("\n🎉 Alle Tests erfolgreich!")
        print("\n📝 Nächste Schritte:")
        print("   1. Starte Frontend: python3 backend/web_app.py")
        print("   2. Öffne Browser: http://localhost:5000")
        print("   3. Wähle 'Frontend GeoJSON' in der Karte")
        print("   4. Öffne Seitenleiste für Warnungen")
    else:
        print("\n⚠️  Einige Tests fehlgeschlagen!")
        print("   Prüfe ob web_app.py läuft: python3 backend/web_app.py")

if __name__ == "__main__":
    main()

