# 📊 Datenverarbeitungs-Guide für Frontend

## Übersicht

Dieser Guide erklärt die **Datenverarbeitung** von Rohdaten zu Frontend-ready Format für:
- **Karten-Visualisierung**
- **Frühwarnsystem**
- **Klimaanpassungs-Empfehlungen**
- **Kausale/Korrelative Analyse**

## Datenfluss

```
Rohdaten (Crawling)
    ↓
Meta-Extraktion (Text, Zahlen, Bilder)
    ↓
Vektorkontextraum (Embeddings)
    ↓
Sensorfusion (Kombination aller Quellen)
    ↓
LLM-Inference (Predictions)
    ↓
Frontend-Verarbeitung
    ↓
GeoJSON + Strukturierte Daten
```

## Output-Struktur

### Für jede Location:

```json
{
  "location_id": "IN_mumbai",
  "location_name": "Mumbai",
  "coordinates": [19.0760, 72.8777],
  
  // 1. RISIKO-DATEN
  "risk_score": 0.75,
  "risk_level": "HIGH",
  "urgency_score": 0.65,
  
  // 2. KLIMA-DATEN (Echte Zahlen)
  "climate_data": {
    "temperatures": {
      "values": [28.5, 29.2, 30.1],  // Echte Temperaturen
      "average": 29.27,
      "anomaly": 1.5,  // vs. IPCC Baseline
      "unit": "celsius"
    },
    "precipitation": {
      "values": [1200, 1500, 1800],  // Echte Niederschlags-Daten
      "average": 1500,
      "anomaly": 15.0,
      "unit": "mm"
    },
    "population": {
      "affected": 5000000,  // Echte Bevölkerungs-Daten
      "total_estimates": [12000000, 15000000]
    },
    "financial": {
      "funding_amount": 50000000,  // Echte Finanz-Daten
      "amounts": [10000000, 25000000, 50000000]
    },
    "risk_indicators": ["heat_waves", "floods", "sea_level_rise"],
    "conflict_indicators": ["migration", "resource_scarcity"]
  },
  
  // 3. FRÜHWARNSYSTEM
  "early_warning": {
    "signals": [
      {
        "type": "HIGH_RISK",
        "severity": "HIGH",
        "message": "Hohes Risiko erkannt: 0.75",
        "indicators": ["heat_waves", "floods"],
        "timestamp": "2024-01-15T10:30:00"
      }
    ],
    "warning_level": "HIGH",
    "requires_immediate_action": false,
    "urgency_score": 0.65
  },
  
  // 4. KLIMAANPASSUNGS-EMPFEHLUNGEN (Kontextuell)
  "adaptation_recommendations": [
    {
      "type": "heat_adaptation",
      "priority": "HIGH",
      "title": "Hitzeschutz-Maßnahmen",
      "description": "Mumbai erlebt erhöhte Temperaturen...",
      "actions": [
        "Grünflächen und Schattenplätze schaffen",
        "Kühlsysteme in öffentlichen Gebäuden installieren",
        "Hitzewarnsysteme etablieren",
        "Wasserversorgung sicherstellen"
      ],
      "timeframe": "kurzfristig",
      "cost_estimate": "mittel",
      "effectiveness": 0.8,
      "region_specific": true
    }
  ],
  
  // 5. KAUSALE/KORRELATIVE ZUSAMMENHÄNGE
  "causal_relationships": [
    {
      "source_location": "US",
      "target_location": "IN",
      "relationship_type": "causal",
      "strength": 0.6,
      "description": "Emissionen aus US tragen zu Klimafolgen in Mumbai bei",
      "evidence": [
        "Globale CO2-Emissionen",
        "IPCC AR6 Daten",
        "Klimamodell-Projektionen"
      ],
      "impact_direction": "negative",
      "impact_type": "emissions",
      "mitigation_potential": "high",
      "recommendations": [
        "US sollte Emissionsreduktion erhöhen",
        "Klimafinanzierung für Mumbai bereitstellen",
        "Technologie-Transfer unterstützen"
      ]
    },
    {
      "source_location": "GLOBAL",
      "target_location": "IN",
      "relationship_type": "causal",
      "strength": 0.8,
      "description": "Globale Klimaveränderungen beeinflussen Mumbai",
      "impact_direction": "negative",
      "mitigation_potential": "global"
    }
  ],
  
  // 6. METADATEN
  "last_updated": "2024-01-15T10:30:00",
  "next_update": "2024-01-16T10:30:00",
  "data_quality": {
    "completeness": 0.75,
    "quality_level": "HIGH"
  }
}
```

## Karten-Integration

### GeoJSON Format

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [72.8777, 19.0760]  // [lon, lat]
      },
      "properties": {
        "name": "Mumbai",
        "country_code": "IN",
        "risk_level": "HIGH",
        "risk_score": 0.75,
        "urgency_score": 0.65,
        "popup_content": "<h3>Mumbai</h3><p>Risk: HIGH</p>"
      }
    }
  ]
}
```

### Leaflet Integration

```javascript
// Lade GeoJSON
fetch('data/frontend/map_data.geojson')
  .then(res => res.json())
  .then(geojson => {
    L.geoJSON(geojson, {
      pointToLayer: (feature, latlng) => {
        const riskLevel = feature.properties.risk_level;
        return L.circleMarker(latlng, {
          radius: getRadius(riskLevel),
          fillColor: getRiskColor(riskLevel),
          color: '#fff',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.8
        });
      },
      onEachFeature: (feature, layer) => {
        layer.bindPopup(createPopup(feature.properties));
      }
    }).addTo(map);
  });
```

## Frühwarnsystem

### Warnungs-Logik

```javascript
function checkEarlyWarnings(location) {
  const warning = location.early_warning;
  
  // Sofortige Aktion erforderlich?
  if (warning.requires_immediate_action) {
    showImmediateAlert(location);
    sendNotification(location);
  }
  
  // Hohe Dringlichkeit?
  if (warning.urgency_score > 0.6) {
    showHighPriorityWarning(location);
  }
  
  // Warnsignale vorhanden?
  if (warning.total_signals > 0) {
    displayWarningSignals(location);
  }
}
```

### Warnungs-Anzeige

```javascript
function displayWarningSignals(location) {
  location.early_warning.signals.forEach(signal => {
    const alert = document.createElement('div');
    alert.className = `alert alert-${signal.severity.toLowerCase()}`;
    alert.innerHTML = `
      <h4>⚠️ ${location.location_name}</h4>
      <p><strong>${signal.type}:</strong> ${signal.message}</p>
      <ul>
        ${signal.indicators.map(ind => `<li>${ind}</li>`).join('')}
      </ul>
      <p><small>Urgency Score: ${location.urgency_score}</small></p>
    `;
    document.getElementById('warnings-container').appendChild(alert);
  });
}
```

## Klimaanpassungs-Empfehlungen

### Empfehlungen anzeigen

```javascript
function displayAdaptationRecommendations(location) {
  const container = document.getElementById('recommendations');
  
  location.adaptation_recommendations.forEach(rec => {
    const card = createRecommendationCard(rec);
    container.appendChild(card);
  });
}

function createRecommendationCard(rec) {
  const card = document.createElement('div');
  card.className = `recommendation-card priority-${rec.priority.toLowerCase()}`;
  
  card.innerHTML = `
    <div class="card-header">
      <h3>${rec.title}</h3>
      <span class="badge badge-${rec.priority.toLowerCase()}">${rec.priority}</span>
    </div>
    <div class="card-body">
      <p>${rec.description}</p>
      <h4>Maßnahmen:</h4>
      <ul>
        ${rec.actions.map(action => `<li>${action}</li>`).join('')}
      </ul>
    </div>
    <div class="card-footer">
      <span>⏱️ ${rec.timeframe}</span>
      <span>💰 ${rec.cost_estimate}</span>
      <span>✓ ${(rec.effectiveness * 100).toFixed(0)}% Effektivität</span>
    </div>
  `;
  
  return card;
}
```

## Kausale Zusammenhänge

### Visualisierung

Die kausalen Zusammenhänge zeigen:
1. **Wie reichere Länder** negative Auswirkungen haben
2. **Regionale Zusammenhänge** zwischen Nachbarländern
3. **Globale Klimamuster** die alle betreffen

### Beispiel-Visualisierung

```javascript
// Netzwerk-Graph mit D3.js
function visualizeCausalNetwork(network) {
  const width = 800;
  const height = 600;
  
  const svg = d3.select('#causal-network')
    .append('svg')
    .attr('width', width)
    .attr('height', height);
  
  // Simulation
  const simulation = d3.forceSimulation(network.nodes)
    .force('link', d3.forceLink(network.edges).id(d => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2));
  
  // Edges (Verbindungen)
  const link = svg.append('g')
    .selectAll('line')
    .data(network.edges)
    .enter().append('line')
    .attr('stroke', d => {
      // Rot für negative, Grün für positive
      return d.impact_direction === 'negative' ? '#d32f2f' : '#388e3c';
    })
    .attr('stroke-width', d => d.strength * 5)
    .attr('opacity', 0.6);
  
  // Nodes (Länder)
  const node = svg.append('g')
    .selectAll('circle')
    .data(network.nodes)
    .enter().append('circle')
    .attr('r', 15)
    .attr('fill', '#1976d2')
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended));
  
  // Labels
  const label = svg.append('g')
    .selectAll('text')
    .data(network.nodes)
    .enter().append('text')
    .text(d => d.id)
    .attr('font-size', 12)
    .attr('dx', 20)
    .attr('dy', 5);
  
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);
    
    node
      .attr('cx', d => d.x)
      .attr('cy', d => d.y);
    
    label
      .attr('x', d => d.x)
      .attr('y', d => d.y);
  });
}
```

## Daten-Generierung

### Script ausführen

```bash
# Generiere Frontend-Daten
./backend/run_frontend_generation.sh

# Oder direkt
python3 backend/generate_frontend_data.py
```

### Output-Verzeichnis

```
data/frontend/
├── complete_data.json              # Vollständige Daten (alle Locations)
├── map_data.geojson                # GeoJSON für Karten
├── early_warning.json              # Frühwarnsystem-Daten
├── adaptation_recommendations.json # Klimaanpassungs-Empfehlungen
└── causal_relationships.json     # Kausale Zusammenhänge
```

## Beispiel-Output

Siehe `backend/example_frontend_output.json` für vollständiges Beispiel mit:
- Mumbai als Beispiel-Location
- Alle Datenfelder ausgefüllt
- Kausale Zusammenhänge zu US, CN, PK, GLOBAL
- Klimaanpassungs-Empfehlungen
- Frühwarnsignale

## Verwendung im Frontend

1. **Lade Daten**: `fetch('/data/frontend/complete_data.json')`
2. **Zeige auf Karte**: Nutze `map_data.geojson` für Leaflet/Mapbox
3. **Warnungen**: Prüfe `early_warning.json` für aktuelle Warnungen
4. **Empfehlungen**: Zeige `adaptation_recommendations.json` für jede Location
5. **Zusammenhänge**: Visualisiere `causal_relationships.json` als Netzwerk

## Nächste Schritte

1. ✅ **Daten generieren**: `python3 backend/generate_frontend_data.py`
2. ✅ **Output prüfen**: `data/frontend/complete_data.json`
3. ⏳ **Frontend integrieren**: Nutze GeoJSON für Karten
4. ⏳ **Warnungen anzeigen**: Implementiere Frühwarnsystem-UI
5. ⏳ **Empfehlungen zeigen**: Zeige kontextuelle Anpassungs-Maßnahmen



