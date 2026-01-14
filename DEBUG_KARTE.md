# 🐛 Debug-Anleitung für Karte

## Problem: Karte zeigt keine Daten

### Mögliche Ursachen:

1. **JavaScript-Fehler**
   - Öffne Browser-Konsole (F12)
   - Prüfe auf Fehler in der Console

2. **Karte wird nicht initialisiert**
   - Prüfe ob `initMap()` aufgerufen wird
   - Prüfe ob `map` Variable gesetzt ist

3. **API gibt keine Daten zurück**
   - Teste: `curl http://localhost:PORT/api/map-data`
   - Prüfe ob `points` Array vorhanden ist

4. **Leaflet nicht geladen**
   - Prüfe ob Leaflet CSS/JS geladen wird
   - Prüfe Netzwerk-Tab im Browser

## Debug-Schritte:

### 1. Browser-Konsole prüfen
```javascript
// In Browser-Konsole eingeben:
console.log('Map:', map);
console.log('Markers:', markers);
```

### 2. API testen
```bash
curl http://localhost:55199/api/map-data | python -m json.tool
```

### 3. Manuelle Initialisierung testen
```javascript
// In Browser-Konsole:
initMap();
loadMapData();
```

## Was wurde verbessert:

1. ✅ Bessere Fehlerbehandlung
2. ✅ Console-Logging hinzugefügt
3. ✅ Robuste Initialisierung
4. ✅ Prüfung ob Karte existiert
5. ✅ Timeout für DOM-Bereitschaft

## Nächste Schritte:

1. Seite neu laden (F5 oder Ctrl+R)
2. Browser-Konsole öffnen (F12)
3. Prüfe auf Fehler-Meldungen
4. Teste manuell: `initMap()` in Konsole

