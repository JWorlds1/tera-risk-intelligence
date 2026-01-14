# 🗺️ Frontend-Integration Guide

## Übersicht

Dieser Guide erklärt, wie die generierten Daten im Frontend verwendet werden können für:
- **Interaktive Karten** (GeoJSON)
- **Frühwarnsystem** (Echtzeit-Warnungen)
- **Klimaanpassungs-Empfehlungen** (Kontextuelle Maßnahmen)
- **Kausale Zusammenhänge** (Visualisierung von Einflüssen)

## Datenstruktur

### 1. Vollständige Daten (`complete_data.json`)

```json
{
  "metadata": {
    "generated_at": "2024-01-15T10:30:00",
    "total_locations": 50,
    "version": "1.0"
  },
  "locations": [
    {
      "location_id": "IN_mumbai",
      "location_name": "Mumbai",
      "country_code": "IN",
      "coordinates": [19.0760, 72.8777],
      "risk_score": 0.75,
      "risk_level": "HIGH",
      "urgency_score": 0.65,
      "climate_data": {...},
      "early_warning": {...},
      "adaptation_recommendations": [...],
      "causal_relationships": [...]
    }
  ],
  "global_statistics": {...},
  "causal_network": {...}
}
```

### 2. GeoJSON für Karten (`map_data.geojson`)

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [72.8777, 19.0760]
      },
      "properties": {
        "name": "Mumbai",
        "country_code": "IN",
        "risk_level": "HIGH",
        "risk_score": 0.75,
        "urgency_score": 0.65
      }
    }
  ]
}
```

### 3. Frühwarnsystem (`early_warning.json`)

```json
{
  "locations": [
    {
      "id": "IN_mumbai",
      "name": "Mumbai",
      "early_warning": {
        "signals": [
          {
            "type": "HIGH_RISK",
            "severity": "HIGH",
            "message": "Hohes Risiko erkannt",
            "indicators": ["heat_waves", "floods"]
          }
        ],
        "warning_level": "HIGH",
        "requires_immediate_action": false
      }
    }
  ]
}
```

### 4. Klimaanpassungs-Empfehlungen (`adaptation_recommendations.json`)

```json
{
  "recommendations_by_location": {
    "IN_mumbai": {
      "recommendations": [
        {
          "type": "heat_adaptation",
          "priority": "HIGH",
          "title": "Hitzeschutz-Maßnahmen",
          "actions": [
            "Grünflächen schaffen",
            "Kühlsysteme installieren"
          ],
          "timeframe": "kurzfristig",
          "cost_estimate": "mittel",
          "effectiveness": 0.8
        }
      ]
    }
  }
}
```

### 5. Kausale Zusammenhänge (`causal_relationships.json`)

```json
{
  "network": {
    "nodes": [
      {"id": "US", "type": "location"},
      {"id": "IN", "type": "location"}
    ],
    "edges": [
      {
        "source": "US",
        "target": "IN",
        "type": "causal",
        "strength": 0.6,
        "impact_direction": "negative",
        "description": "Emissionen aus US tragen zu Klimafolgen bei"
      }
    ]
  }
}
```

## Frontend-Integration

### 1. Karten-Integration (Leaflet/Mapbox)

```javascript
// Lade GeoJSON
fetch('/data/frontend/map_data.geojson')
  .then(res => res.json())
  .then(geojson => {
    // Füge Layer zur Karte hinzu
    L.geoJSON(geojson, {
      pointToLayer: (feature, latlng) => {
        const riskLevel = feature.properties.risk_level;
        const color = getRiskColor(riskLevel);
        
        return L.circleMarker(latlng, {
          radius: 8,
          fillColor: color,
          color: '#fff',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.8
        });
      },
      onEachFeature: (feature, layer) => {
        const props = feature.properties;
        layer.bindPopup(`
          <h3>${props.name}</h3>
          <p>Risk Level: ${props.risk_level}</p>
          <p>Urgency: ${props.urgency_score}</p>
        `);
      }
    }).addTo(map);
  });

function getRiskColor(level) {
  const colors = {
    'CRITICAL': '#d32f2f',
    'HIGH': '#f57c00',
    'MEDIUM': '#fbc02d',
    'LOW': '#388e3c',
    'MINIMAL': '#1976d2'
  };
  return colors[level] || '#999';
}
```

### 2. Frühwarnsystem-Integration

```javascript
// Lade Frühwarn-Daten
fetch('/data/frontend/early_warning.json')
  .then(res => res.json())
  .then(data => {
    data.locations.forEach(location => {
      const warning = location.early_warning;
      
      if (warning.requires_immediate_action) {
        // Zeige sofortige Warnung
        showImmediateWarning(location);
      } else if (warning.warning_level === 'HIGH') {
        // Zeige Warnung in Dashboard
        showWarning(location);
      }
    });
  });

function showWarning(location) {
  const warningDiv = document.createElement('div');
  warningDiv.className = 'warning-alert';
  warningDiv.innerHTML = `
    <h4>⚠️ ${location.name}</h4>
    <p>${location.early_warning.signals[0].message}</p>
    <p>Urgency: ${location.urgency_score}</p>
  `;
  document.getElementById('warnings').appendChild(warningDiv);
}
```

### 3. Klimaanpassungs-Empfehlungen

```javascript
// Lade Anpassungs-Empfehlungen
fetch('/data/frontend/adaptation_recommendations.json')
  .then(res => res.json())
  .then(data => {
    const locationId = 'IN_mumbai';
    const recommendations = data.recommendations_by_location[locationId];
    
    recommendations.recommendations.forEach(rec => {
      renderRecommendation(rec);
    });
  });

function renderRecommendation(rec) {
  const card = document.createElement('div');
  card.className = `recommendation-card priority-${rec.priority.toLowerCase()}`;
  card.innerHTML = `
    <h3>${rec.title}</h3>
    <p>${rec.description}</p>
    <ul>
      ${rec.actions.map(action => `<li>${action}</li>`).join('')}
    </ul>
    <div class="meta">
      <span>Zeitraum: ${rec.timeframe}</span>
      <span>Kosten: ${rec.cost_estimate}</span>
      <span>Effektivität: ${(rec.effectiveness * 100).toFixed(0)}%</span>
    </div>
  `;
  document.getElementById('recommendations').appendChild(card);
}
```

### 4. Kausale Zusammenhänge Visualisierung

```javascript
// Lade kausale Zusammenhänge
fetch('/data/frontend/causal_relationships.json')
  .then(res => res.json())
  .then(data => {
    // Visualisiere mit D3.js oder Cytoscape
    visualizeCausalNetwork(data.network);
  });

function visualizeCausalNetwork(network) {
  // Beispiel mit D3.js Force-Directed Graph
  const svg = d3.select('#causal-network');
  
  const simulation = d3.forceSimulation(network.nodes)
    .force('link', d3.forceLink(network.edges).id(d => d.id))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2));
  
  // Zeichne Edges
  const link = svg.append('g')
    .selectAll('line')
    .data(network.edges)
    .enter().append('line')
    .attr('stroke', d => d.impact_direction === 'negative' ? '#d32f2f' : '#388e3c')
    .attr('stroke-width', d => d.strength * 5);
  
  // Zeichne Nodes
  const node = svg.append('g')
    .selectAll('circle')
    .data(network.nodes)
    .enter().append('circle')
    .attr('r', 10)
    .call(d3.drag());
  
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);
    
    node
      .attr('cx', d => d.x)
      .attr('cy', d => d.y);
  });
}
```

## Daten-Generierung

### Script ausführen

```bash
# Generiere Frontend-Daten für alle kritischen Länder
python3 backend/generate_frontend_data.py
```

### Output-Verzeichnis

```
data/frontend/
├── complete_data.json          # Vollständige Daten
├── map_data.geojson            # GeoJSON für Karten
├── early_warning.json          # Frühwarnsystem
├── adaptation_recommendations.json  # Anpassungs-Empfehlungen
└── causal_relationships.json   # Kausale Zusammenhänge
```

## Datenfelder-Erklärung

### Risk Levels
- **CRITICAL**: Sofortige Maßnahmen erforderlich
- **HIGH**: Hohe Priorität, kurzfristige Maßnahmen
- **MEDIUM**: Mittlere Priorität, mittelfristige Maßnahmen
- **LOW**: Niedrige Priorität, langfristige Maßnahmen
- **MINIMAL**: Minimale Risiken

### Urgency Score
- **0.0-0.3**: Niedrige Dringlichkeit
- **0.3-0.6**: Mittlere Dringlichkeit
- **0.6-0.8**: Hohe Dringlichkeit
- **0.8-1.0**: Kritische Dringlichkeit

### Relationship Types
- **causal**: Kausaler Zusammenhang (A verursacht B)
- **correlative**: Korrelativer Zusammenhang (A und B korrelieren)
- **influence**: Einfluss-Beziehung (A beeinflusst B)

### Impact Direction
- **negative**: Negativer Einfluss
- **positive**: Positiver Einfluss
- **mixed**: Gemischter Einfluss

## Beispiel-Output

Siehe `backend/example_frontend_output.json` für vollständiges Beispiel.

## Nächste Schritte

1. **Karten-Integration**: Nutze `map_data.geojson` für interaktive Karten
2. **Frühwarnsystem**: Implementiere Echtzeit-Warnungen basierend auf `early_warning.json`
3. **Anpassungs-Empfehlungen**: Zeige kontextuelle Empfehlungen für jede Region
4. **Kausale Visualisierung**: Visualisiere Zusammenhänge zwischen Regionen
5. **Echtzeit-Updates**: Nutze `next_update` für automatische Aktualisierungen



