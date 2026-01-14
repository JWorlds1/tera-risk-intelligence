# ⚠️ Keine Fallback-Daten

## Wichtiger Hinweis

Die Pipeline verwendet **KEINE Fallback-Daten**. Es werden nur **echte, gesammelte Daten** verwendet.

## Verhalten

### Wenn keine Daten vorhanden sind:

- **Text**: Leere Liste `[]` wenn keine Text-Daten gefunden werden
- **Zahlen**: Leeres Dictionary `{}` oder leere Listen wenn keine numerischen Daten gefunden werden
- **Bilder**: Leere Liste `[]` wenn keine Bilder gefunden werden
- **Predictions**: Nur Felder mit echten Daten werden ausgegeben

### Validierung

Die Pipeline validiert, ob Daten vorhanden sind:

- ✅ **Daten vorhanden**: Pipeline läuft normal weiter
- ⚠️ **Keine Daten**: Pipeline zeigt Warnung, aber läuft weiter
- ❌ **Kritische Fehler**: Pipeline stoppt nur bei kritischen Fehlern

## Garantie für echte Daten

Um sicherzustellen, dass echte Daten vorhanden sind:

1. **Crawling**: Stelle sicher, dass URLs erreichbar sind
2. **Research**: Firecrawl-Suche muss Ergebnisse liefern
3. **Datenbank**: Records müssen vorhanden sein
4. **Validierung**: Test-Script prüft Datenverfügbarkeit

## Test-Script

Verwende das Test-Script um zu prüfen, welche Daten vorhanden sind:

```bash
python3 backend/test_global_pipeline.py
```

Das Script zeigt:
- Welche Länder Daten haben
- Welche Kategorien fehlen
- Datenqualität pro Land

## Output-Format

Wenn keine Daten vorhanden sind, sieht der Output so aus:

```json
{
  "stages": {
    "meta_extraction": {
      "text_chunks": [],
      "numerical_data": {},
      "image_urls": []
    }
  }
}
```

**Wichtig**: Leere Listen/Dictionaries bedeuten, dass keine Daten gefunden wurden.



