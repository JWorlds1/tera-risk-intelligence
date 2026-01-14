# Graduelle Fein-Granulare Animationslogik

## Übersicht

Diese Implementierung fügt eine **graduelle, feingranulare Animationslogik** für H3-Grid-Polygone hinzu. Die Animationen sind sequenziell, smooth und performance-optimiert.

## Features

### 1. **Sequenzielle Polygon-Animation**
- Polygone werden **nicht alle auf einmal** gerendert
- **Staggered Animation**: Jedes Polygon startet mit einer kleinen Verzögerung (25ms)
- **Batch-Processing**: 8 Polygone animieren gleichzeitig für optimale Performance

### 2. **Graduelle Übergänge**
- **Höhen-Animation**: Polygone wachsen von 0 zur Zielhöhe (Extrusion)
- **Farb-Interpolation**: Smooth Übergang von transparent zu voller Farbe
- **Alpha-Animation**: Graduelles Einblenden (0.1 → 0.85)

### 3. **Easing-Funktionen**
- **easeOutCubic**: Smooth, natürliche Bewegung
- **easeInOutQuad**: Sanfter Start und Ende
- **easeOutExpo**: Dynamischer Effekt

### 4. **Layer-Übergänge**
- Beim Wechseln zwischen Layern (Composite, Hazard, Exposure, Vulnerability)
- **Smooth Color Transitions**: Farben interpolieren graduell
- **Keine abrupten Sprünge**: Alle Übergänge sind animiert

## Technische Details

### Animation Engine (`animation_engine.ts`)

```typescript
const animationEngine = new GradualAnimationEngine({
  duration: 1200,        // 1.2s pro Polygon
  staggerDelay: 25,      // 25ms zwischen Polygonen (feingranular)
  batchSize: 8,          // 8 Polygone gleichzeitig
});
```

### Integration in `map_app.ts`

1. **Initial Rendering**: Polygone starten bei Höhe 0 und Alpha 0.1
2. **Animation Start**: Nach 500ms (während Kamera-Bewegung) startet die Animation
3. **Sequenzielle Animation**: Jedes Polygon animiert mit 25ms Verzögerung
4. **Layer Switching**: Farbübergänge werden ebenfalls animiert

## Performance-Optimierungen

- **requestAnimationFrame**: Nutzt Browser-optimierte Animation-Loop
- **Batch Processing**: Mehrere Polygone gleichzeitig
- **Early Termination**: Animationen werden gestoppt, wenn neue gestartet werden
- **Memory Management**: Abgeschlossene Animationen werden automatisch entfernt

## CSS-Animationen

Zusätzliche CSS-Animationen für UI-Elemente:
- **fadeInScale**: Sanftes Einblenden von Panels
- **pulse**: Subtile Puls-Animation für Metriken
- **Smooth Transitions**: Alle UI-Interaktionen sind animiert

## Verwendung

Die Animationen starten automatisch beim:
1. **Rendern eines neuen H3-Grids** (`_renderH3Grid`)
2. **Wechseln zwischen Layern** (`_updateLayerVisualization`)

## Konfiguration

Die Animations-Parameter können in `map_app.ts` angepasst werden:

```typescript
this.animationEngine = new GradualAnimationEngine({
  duration: 1200,        // Dauer pro Polygon (ms)
  staggerDelay: 25,      // Verzögerung zwischen Polygonen (ms)
  batchSize: 8,          // Anzahl gleichzeitiger Animationen
});
```

## Beispiel

```typescript
// Polygone werden automatisch animiert
this.animationEngine.animatePolygons([
  {
    element: polygon1,
    targetHeight: 200,
    targetColor: 'rgba(255, 0, 0, 0.85)',
    targetAlpha: 0.85,
  },
  // ... weitere Polygone
]);
```

## Browser-Kompatibilität

- **requestAnimationFrame**: Unterstützt in allen modernen Browsern
- **Performance**: Optimiert für 60 FPS
- **Fallback**: Bei Fehlern werden Polygone sofort gerendert (ohne Animation)


