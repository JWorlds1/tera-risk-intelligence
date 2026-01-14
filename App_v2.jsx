import React, { useRef, useState, useEffect, useCallback } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

/*
 * TERA v2.0 - EARTH INTELLIGENCE PLATFORM
 * 
 * Features:
 * - Real-time Earth Cycle visualization
 * - Physical model integration (Energy, Water, Carbon)
 * - Adaptive H3 tessellation
 * - Global coverage
 * - Professional UI/UX
 */

const API_BASE = 'http://localhost:8080/api'

// =====================================================
// CONFIGURATION
// =====================================================

const CYCLE_MODES = {
  risk: { name: 'Risiko', icon: '⚠️', unit: '', colorScale: ['#00ff88', '#ffff00', '#ff8800', '#ff0000'] },
  temperature: { name: 'Temperatur', icon: '🌡️', unit: '°C', colorScale: ['#0000ff', '#00ffff', '#ffff00', '#ff0000'] },
  precipitation: { name: 'Niederschlag', icon: '🌧️', unit: 'mm', colorScale: ['#ffffcc', '#a1dab4', '#41b6c4', '#225ea8'] },
  soil_moisture: { name: 'Bodenfeuchte', icon: '💧', unit: '%', colorScale: ['#8b4513', '#daa520', '#90ee90', '#006400'] },
  ndvi: { name: 'Vegetation', icon: '🌿', unit: '', colorScale: ['#8b4513', '#f4a460', '#90ee90', '#006400'] },
  gpp: { name: 'Photosynthese', icon: '☀️', unit: 'gC/m²', colorScale: ['#440154', '#31688e', '#35b779', '#fde725'] },
  net_radiation: { name: 'Netto-Strahlung', icon: '☀️', unit: 'W/m²', colorScale: ['#313695', '#ffffbf', '#d73027'] }
}

const CITIES = [
  { name: 'Berlin', lat: 52.52, lon: 13.41, region: 'Europe' },
  { name: 'Miami', lat: 25.76, lon: -80.19, region: 'Americas' },
  { name: 'Tokyo', lat: 35.68, lon: 139.65, region: 'Asia' },
  { name: 'Jakarta', lat: -6.21, lon: 106.85, region: 'Asia' },
  { name: 'Cairo', lat: 30.04, lon: 31.24, region: 'Africa' },
  { name: 'Lagos', lat: 6.52, lon: 3.38, region: 'Africa' },
  { name: 'Mumbai', lat: 19.08, lon: 72.88, region: 'Asia' },
  { name: 'São Paulo', lat: -23.55, lon: -46.63, region: 'Americas' },
  { name: 'Sydney', lat: -33.87, lon: 151.21, region: 'Oceania' },
  { name: 'London', lat: 51.51, lon: -0.13, region: 'Europe' },
  { name: 'New York', lat: 40.71, lon: -74.01, region: 'Americas' },
  { name: 'Singapore', lat: 1.35, lon: 103.82, region: 'Asia' },
]

// =====================================================
// ANIMATED HOPF FIBRATION LOGO
// =====================================================

function HopfLogo({ size = 60 }) {
  const ref = useRef(null)
  
  useEffect(() => {
    const canvas = ref.current
    const ctx = canvas?.getContext('2d')
    if (!ctx) return
    
    let animationId
    let time = 0
    
    const draw = () => {
      time += 0.015
      
      // Clear with fade effect
      ctx.fillStyle = 'rgba(8, 8, 12, 0.15)'
      ctx.fillRect(0, 0, size, size)
      
      const cx = size / 2
      const cy = size / 2
      
      // Draw fibration rings
      for (let i = 0; i < 16; i++) {
        const phase = (i / 16) * Math.PI * 2
        const radius = size * 0.28 + Math.sin(time * 2 + phase) * size * 0.05
        const tilt = time * 0.3 + phase
        
        ctx.beginPath()
        ctx.strokeStyle = `hsla(${180 + i * 10 + time * 20}, 100%, 60%, ${0.4 + Math.sin(time + phase) * 0.2})`
        ctx.lineWidth = 1.5
        ctx.ellipse(cx, cy, radius, radius * 0.3, tilt, 0, Math.PI * 2)
        ctx.stroke()
      }
      
      // Center glow
      const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, size * 0.15)
      gradient.addColorStop(0, 'rgba(0, 255, 255, 0.8)')
      gradient.addColorStop(0.5, 'rgba(0, 200, 255, 0.3)')
      gradient.addColorStop(1, 'transparent')
      
      ctx.beginPath()
      ctx.fillStyle = gradient
      ctx.arc(cx, cy, size * 0.15, 0, Math.PI * 2)
      ctx.fill()
      
      // Core
      ctx.beginPath()
      ctx.fillStyle = '#00ffff'
      ctx.shadowColor = '#00ffff'
      ctx.shadowBlur = 15
      ctx.arc(cx, cy, 3, 0, Math.PI * 2)
      ctx.fill()
      ctx.shadowBlur = 0
      
      animationId = requestAnimationFrame(draw)
    }
    
    draw()
    return () => cancelAnimationFrame(animationId)
  }, [size])
  
  return <canvas ref={ref} width={size} height={size} style={{ borderRadius: '50%' }} />
}

// =====================================================
// EARTH CYCLE PANEL
// =====================================================

function CyclePanel({ data, mode }) {
  if (!data) return null
  
  const modeConfig = CYCLE_MODES[mode] || CYCLE_MODES.risk
  
  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(20,25,35,0.95), rgba(10,15,25,0.98))',
      borderRadius: '16px',
      padding: '20px',
      border: '1px solid rgba(0,255,255,0.2)',
      backdropFilter: 'blur(10px)',
    }}>
      {/* Energy Budget */}
      <div style={{ marginBottom: '20px' }}>
        <h4 style={{ color: '#00ffff', margin: '0 0 12px 0', fontSize: '14px', letterSpacing: '2px' }}>
          ☀️ ENERGIE-BUDGET
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <MetricBox label="SW Absorbed" value={data.energy_budget?.sw_absorbed} unit="W/m²" />
          <MetricBox label="Net Radiation" value={data.energy_budget?.net_radiation} unit="W/m²" />
          <MetricBox label="Latent Heat" value={data.energy_budget?.latent_heat} unit="W/m²" />
          <MetricBox label="Sensible Heat" value={data.energy_budget?.sensible_heat} unit="W/m²" />
        </div>
      </div>
      
      {/* Water Cycle */}
      <div style={{ marginBottom: '20px' }}>
        <h4 style={{ color: '#00aaff', margin: '0 0 12px 0', fontSize: '14px', letterSpacing: '2px' }}>
          💧 WASSER-ZYKLUS
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <MetricBox label="ET" value={data.water_cycle?.evapotranspiration} unit="mm/d" color="#00aaff" />
          <MetricBox label="Bodenfeuchte" value={data.water_cycle?.soil_moisture} unit="%" color="#00aaff" />
          <MetricBox label="Runoff" value={data.water_cycle?.runoff} unit="mm/d" color="#00aaff" />
          <MetricBox label="Balance" value={data.water_cycle?.water_balance} unit="mm" color="#00aaff" />
        </div>
      </div>
      
      {/* Carbon Cycle */}
      <div>
        <h4 style={{ color: '#00ff88', margin: '0 0 12px 0', fontSize: '14px', letterSpacing: '2px' }}>
          🌿 CARBON-ZYKLUS
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <MetricBox label="GPP" value={data.carbon_cycle?.gpp} unit="gC/m²" color="#00ff88" />
          <MetricBox label="NEE" value={data.carbon_cycle?.nee} unit="gC/m²" color="#00ff88" />
          <MetricBox label="NDVI" value={data.carbon_cycle?.ndvi} unit="" color="#00ff88" />
          <MetricBox label="LAI" value={data.carbon_cycle?.lai} unit="m²/m²" color="#00ff88" />
        </div>
      </div>
    </div>
  )
}

function MetricBox({ label, value, unit, color = '#00ffff' }) {
  const displayValue = value !== undefined && value !== null 
    ? (typeof value === 'number' ? value.toFixed(1) : value)
    : '—'
  
  return (
    <div style={{
      background: 'rgba(0,0,0,0.3)',
      padding: '10px',
      borderRadius: '8px',
      borderLeft: `3px solid ${color}`,
    }}>
      <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)', marginBottom: '4px' }}>
        {label}
      </div>
      <div style={{ fontSize: '18px', color, fontWeight: 'bold' }}>
        {displayValue}
        <span style={{ fontSize: '10px', opacity: 0.6, marginLeft: '4px' }}>{unit}</span>
      </div>
    </div>
  )
}

// =====================================================
// RISK GAUGE
// =====================================================

function RiskGauge({ score, drivers }) {
  const percentage = Math.min(100, score * 100)
  const color = score > 0.7 ? '#ff0000' : score > 0.4 ? '#ff8800' : score > 0.2 ? '#ffff00' : '#00ff88'
  
  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(20,25,35,0.95), rgba(10,15,25,0.98))',
      borderRadius: '16px',
      padding: '20px',
      border: '1px solid rgba(0,255,255,0.2)',
      textAlign: 'center',
    }}>
      <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)', marginBottom: '10px', letterSpacing: '2px' }}>
        GESAMTRISIKO-INDEX
      </div>
      
      <div style={{ 
        fontSize: '64px', 
        fontWeight: 'bold', 
        color,
        textShadow: `0 0 30px ${color}`,
        lineHeight: 1,
      }}>
        {percentage.toFixed(0)}%
      </div>
      
      {/* Progress bar */}
      <div style={{
        height: '8px',
        background: 'rgba(255,255,255,0.1)',
        borderRadius: '4px',
        margin: '15px 0',
        overflow: 'hidden',
      }}>
        <div style={{
          height: '100%',
          width: `${percentage}%`,
          background: `linear-gradient(90deg, #00ff88, ${color})`,
          borderRadius: '4px',
          transition: 'width 0.5s ease',
        }} />
      </div>
      
      {/* Risk drivers */}
      {drivers && drivers.length > 0 && (
        <div style={{ marginTop: '15px' }}>
          <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)', marginBottom: '8px' }}>
            RISIKO-TREIBER
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'center' }}>
            {drivers.map((driver, i) => (
              <span key={i} style={{
                background: 'rgba(255,100,100,0.2)',
                color: '#ff8888',
                padding: '4px 10px',
                borderRadius: '12px',
                fontSize: '11px',
              }}>
                {driver.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// =====================================================
// MODE SELECTOR
// =====================================================

function ModeSelector({ mode, setMode }) {
  return (
    <div style={{
      display: 'flex',
      gap: '8px',
      flexWrap: 'wrap',
      marginBottom: '15px',
    }}>
      {Object.entries(CYCLE_MODES).map(([key, config]) => (
        <button
          key={key}
          onClick={() => setMode(key)}
          style={{
            background: mode === key ? 'rgba(0,255,255,0.2)' : 'rgba(255,255,255,0.05)',
            border: mode === key ? '1px solid #00ffff' : '1px solid rgba(255,255,255,0.1)',
            color: mode === key ? '#00ffff' : 'rgba(255,255,255,0.7)',
            padding: '8px 14px',
            borderRadius: '20px',
            cursor: 'pointer',
            fontSize: '12px',
            transition: 'all 0.2s',
          }}
        >
          {config.icon} {config.name}
        </button>
      ))}
    </div>
  )
}

// =====================================================
// CITY SELECTOR
// =====================================================

function CitySelector({ onSelect, currentCity }) {
  const [isOpen, setIsOpen] = useState(false)
  
  const regions = [...new Set(CITIES.map(c => c.region))]
  
  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          background: 'rgba(0,255,255,0.1)',
          border: '1px solid rgba(0,255,255,0.3)',
          color: '#00ffff',
          padding: '12px 20px',
          borderRadius: '25px',
          cursor: 'pointer',
          fontSize: '14px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          width: '100%',
        }}
      >
        <span>📍</span>
        <span style={{ flex: 1, textAlign: 'left' }}>{currentCity || 'Stadt wählen...'}</span>
        <span style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
      </button>
      
      {isOpen && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          marginTop: '8px',
          background: 'rgba(15,20,30,0.98)',
          border: '1px solid rgba(0,255,255,0.2)',
          borderRadius: '12px',
          overflow: 'hidden',
          zIndex: 1000,
          maxHeight: '300px',
          overflowY: 'auto',
        }}>
          {regions.map(region => (
            <div key={region}>
              <div style={{
                padding: '8px 15px',
                fontSize: '10px',
                color: 'rgba(255,255,255,0.4)',
                background: 'rgba(0,0,0,0.3)',
                letterSpacing: '2px',
              }}>
                {region.toUpperCase()}
              </div>
              {CITIES.filter(c => c.region === region).map(city => (
                <button
                  key={city.name}
                  onClick={() => {
                    onSelect(city)
                    setIsOpen(false)
                  }}
                  style={{
                    display: 'block',
                    width: '100%',
                    padding: '12px 15px',
                    background: 'transparent',
                    border: 'none',
                    color: city.name === currentCity ? '#00ffff' : 'white',
                    textAlign: 'left',
                    cursor: 'pointer',
                    fontSize: '14px',
                  }}
                  onMouseEnter={(e) => e.target.style.background = 'rgba(0,255,255,0.1)'}
                  onMouseLeave={(e) => e.target.style.background = 'transparent'}
                >
                  {city.name}
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// =====================================================
// MAIN APP
// =====================================================

export default function App() {
  const mapContainer = useRef(null)
  const map = useRef(null)
  
  const [selectedCity, setSelectedCity] = useState(CITIES[0])
  const [cycleData, setCycleData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState('risk')
  const [cellCount, setCellCount] = useState(0)
  const [status, setStatus] = useState('Initialisiere...')

  // Initialize map
  useEffect(() => {
    if (map.current) return
    
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'carto-dark': {
            type: 'raster',
            tiles: ['https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png'],
            tileSize: 256,
            attribution: '© CARTO'
          }
        },
        layers: [{
          id: 'carto-dark-layer',
          type: 'raster',
          source: 'carto-dark',
          minzoom: 0,
          maxzoom: 20
        }]
      },
      center: [selectedCity.lon, selectedCity.lat],
      zoom: 10,
      pitch: 45,
      bearing: -15,
    })
    
    map.current.addControl(new maplibregl.NavigationControl(), 'top-left')
    
    map.current.on('load', () => {
      setStatus('Karte geladen')
      
      // Add hexagon source
      map.current.addSource('hexagons', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      })
      
      // 3D Hexagon layer
      map.current.addLayer({
        id: 'hexagons-3d',
        type: 'fill-extrusion',
        source: 'hexagons',
        paint: {
          'fill-extrusion-color': ['get', 'fill_color'],
          'fill-extrusion-height': ['get', 'height'],
          'fill-extrusion-base': 0,
          'fill-extrusion-opacity': 0.8,
        }
      })
      
      // Hexagon outline
      map.current.addLayer({
        id: 'hexagons-outline',
        type: 'line',
        source: 'hexagons',
        paint: {
          'line-color': 'rgba(0,255,255,0.4)',
          'line-width': 0.5,
        }
      })
      
      // Click handler
      map.current.on('click', 'hexagons-3d', async (e) => {
        if (e.features?.[0]) {
          const props = e.features[0].properties
          const h3Index = props.h3_index
          
          if (h3Index) {
            setStatus(`Lade Daten für ${h3Index}...`)
            try {
              const response = await fetch(`${API_BASE}/cycles/cell/${h3Index}`)
              const data = await response.json()
              setCycleData(data)
              setStatus('Zelldaten geladen')
            } catch (err) {
              console.error(err)
              setStatus('Fehler beim Laden')
            }
          }
        }
      })
      
      // Cursor
      map.current.on('mouseenter', 'hexagons-3d', () => {
        map.current.getCanvas().style.cursor = 'pointer'
      })
      map.current.on('mouseleave', 'hexagons-3d', () => {
        map.current.getCanvas().style.cursor = ''
      })
      
      // Initial load
      loadCityData(selectedCity)
    })
    
    return () => map.current?.remove()
  }, [])

  // Load city data
  const loadCityData = useCallback(async (city) => {
    if (!map.current) return
    
    setLoading(true)
    setStatus(`Analysiere ${city.name}...`)
    setCycleData(null)
    
    // Fly to city
    map.current.flyTo({
      center: [city.lon, city.lat],
      zoom: 11,
      pitch: 50,
      bearing: Math.random() * 30 - 15,
      duration: 2000,
    })
    
    try {
      // Get bounding box
      const delta = 0.15
      const minLat = city.lat - delta
      const maxLat = city.lat + delta
      const minLon = city.lon - delta
      const maxLon = city.lon + delta
      
      setStatus('Lade Erdzyklen-Daten...')
      
      // Fetch from Earth Cycles API
      const response = await fetch(
        `${API_BASE}/cycles/cells?min_lat=${minLat}&min_lon=${minLon}&max_lat=${maxLat}&max_lon=${maxLon}&zoom=11`
      )
      
      if (!response.ok) throw new Error('API Error')
      
      const data = await response.json()
      
      if (data.geojson?.features) {
        setCellCount(data.geojson.features.length)
        setStatus(`${data.geojson.features.length} Zellen geladen`)
        
        // Animate hexagons appearing
        animateHexagons(data.geojson)
        
        // Load center cell details
        const centerResponse = await fetch(
          `${API_BASE}/cycles/location?lat=${city.lat}&lon=${city.lon}`
        )
        const centerData = await centerResponse.json()
        setCycleData(centerData)
      }
      
    } catch (err) {
      console.error('Error loading data:', err)
      setStatus('Fehler - Verwende Fallback')
      
      // Fallback: Use analysis API
      try {
        const fallbackResponse = await fetch(`${API_BASE}/analysis/analyze?city=${city.name}`)
        const fallbackData = await fallbackResponse.json()
        
        if (fallbackData.hexagons) {
          setCellCount(fallbackData.hexagons.length)
          animateHexagonsLegacy(fallbackData.hexagons)
        }
      } catch (e) {
        console.error('Fallback also failed:', e)
      }
    }
    
    setLoading(false)
  }, [])

  // Animate hexagons
  const animateHexagons = (geojson) => {
    if (!map.current) return
    
    const source = map.current.getSource('hexagons')
    if (!source) return
    
    // Start with zero height
    const features = geojson.features.map(f => ({
      ...f,
      properties: {
        ...f.properties,
        height: 0,
      }
    }))
    
    source.setData({ type: 'FeatureCollection', features })
    
    // Animate height
    let frame = 0
    const totalFrames = 60
    
    const animate = () => {
      frame++
      const progress = Math.min(frame / totalFrames, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      
      const animatedFeatures = geojson.features.map((f, i) => {
        const delay = (i / geojson.features.length) * 0.5
        const localProgress = Math.max(0, Math.min(1, (progress - delay) / (1 - delay)))
        const localEased = 1 - Math.pow(1 - localProgress, 3)
        
        return {
          ...f,
          properties: {
            ...f.properties,
            height: (f.properties.height || f.properties.risk_score * 500 || 100) * localEased,
          }
        }
      })
      
      source.setData({ type: 'FeatureCollection', features: animatedFeatures })
      
      if (frame < totalFrames) {
        requestAnimationFrame(animate)
      }
    }
    
    requestAnimationFrame(animate)
  }

  // Legacy hexagon animation (fallback)
  const animateHexagonsLegacy = (hexagons) => {
    if (!map.current) return
    
    const source = map.current.getSource('hexagons')
    if (!source) return
    
    const features = hexagons.map(hex => ({
      type: 'Feature',
      geometry: hex.geometry,
      properties: {
        h3_index: hex.h3,
        fill_color: hex.color || '#00ffff',
        height: (hex.intensity || 0.5) * 500,
        risk_score: hex.intensity || 0.5,
      }
    }))
    
    animateHexagons({ type: 'FeatureCollection', features })
  }

  // Handle city selection
  const handleCitySelect = (city) => {
    setSelectedCity(city)
    loadCityData(city)
  }

  return (
    <div style={{ 
      width: '100vw', 
      height: '100vh', 
      display: 'flex', 
      background: '#0a0a0f',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      color: 'white',
    }}>
      {/* Map */}
      <div ref={mapContainer} style={{ flex: 1, position: 'relative' }}>
        {/* Status overlay */}
        <div style={{
          position: 'absolute',
          top: '20px',
          left: '70px',
          background: 'rgba(0,0,0,0.7)',
          padding: '10px 20px',
          borderRadius: '20px',
          fontSize: '12px',
          color: loading ? '#ffaa00' : '#00ff88',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}>
          {loading && (
            <div style={{
              width: '12px',
              height: '12px',
              border: '2px solid transparent',
              borderTopColor: '#00ffff',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
            }} />
          )}
          {status}
          {cellCount > 0 && <span style={{ color: 'rgba(255,255,255,0.5)' }}>| {cellCount} Zellen</span>}
        </div>
        
        {/* City label */}
        <div style={{
          position: 'absolute',
          bottom: '30px',
          left: '30px',
          background: 'linear-gradient(135deg, rgba(0,0,0,0.8), rgba(0,0,0,0.6))',
          padding: '15px 25px',
          borderRadius: '12px',
          borderLeft: '4px solid #00ffff',
        }}>
          <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)', marginBottom: '5px' }}>
            STANDORT
          </div>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            📍 {selectedCity.name}
          </div>
          <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)', marginTop: '5px' }}>
            {selectedCity.lat.toFixed(2)}°, {selectedCity.lon.toFixed(2)}°
          </div>
        </div>
      </div>
      
      {/* Right Panel */}
      <div style={{
        width: '420px',
        height: '100vh',
        overflowY: 'auto',
        background: 'linear-gradient(180deg, #0d1117, #161b22)',
        borderLeft: '1px solid rgba(0,255,255,0.1)',
        padding: '20px',
      }}>
        {/* Header */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '15px', 
          marginBottom: '25px',
          paddingBottom: '20px',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}>
          <HopfLogo size={55} />
          <div>
            <div style={{ 
              fontSize: '24px', 
              fontWeight: 'bold', 
              letterSpacing: '4px',
              background: 'linear-gradient(90deg, #00ffff, #00ff88)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              TERA
            </div>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', letterSpacing: '1px' }}>
              EARTH INTELLIGENCE PLATFORM
            </div>
          </div>
        </div>
        
        {/* City Selector */}
        <div style={{ marginBottom: '20px' }}>
          <CitySelector 
            onSelect={handleCitySelect} 
            currentCity={selectedCity.name} 
          />
        </div>
        
        {/* Mode Selector */}
        <ModeSelector mode={mode} setMode={setMode} />
        
        {/* Risk Gauge */}
        {cycleData && (
          <div style={{ marginBottom: '20px' }}>
            <RiskGauge 
              score={cycleData.risk?.score || 0} 
              drivers={cycleData.risk?.drivers || []} 
            />
          </div>
        )}
        
        {/* Cycle Panels */}
        {cycleData && (
          <CyclePanel data={cycleData} mode={mode} />
        )}
        
        {/* Loading State */}
        {loading && !cycleData && (
          <div style={{
            textAlign: 'center',
            padding: '40px',
            color: 'rgba(255,255,255,0.5)',
          }}>
            <div style={{ fontSize: '40px', marginBottom: '15px' }}>🌍</div>
            <div>Berechne Erdzyklen...</div>
          </div>
        )}
        
        {/* Cycle Equations */}
        <div style={{
          marginTop: '20px',
          padding: '15px',
          background: 'rgba(0,0,0,0.3)',
          borderRadius: '12px',
          fontSize: '11px',
          color: 'rgba(255,255,255,0.4)',
          fontFamily: 'monospace',
        }}>
          <div style={{ marginBottom: '8px' }}>☀️ Rn = (SW↓ - SW↑) + (LW↓ - LW↑)</div>
          <div style={{ marginBottom: '8px' }}>💧 P - ET - R = ΔS</div>
          <div>🌿 NEE = Ra + Rh - GPP</div>
        </div>
        
        {/* Footer */}
        <div style={{
          marginTop: '20px',
          paddingTop: '20px',
          borderTop: '1px solid rgba(255,255,255,0.1)',
          fontSize: '10px',
          color: 'rgba(255,255,255,0.3)',
          textAlign: 'center',
        }}>
          TERA v2.0 | Physical Earth Model | Adaptive H3 Tessellation
          <br />
          Data: ERA5 · KNMI · Sentinel · NASA FIRMS
        </div>
      </div>
      
      {/* Global Styles */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        
        ::-webkit-scrollbar {
          width: 8px;
        }
        ::-webkit-scrollbar-track {
          background: rgba(0,0,0,0.2);
        }
        ::-webkit-scrollbar-thumb {
          background: rgba(0,255,255,0.3);
          border-radius: 4px;
        }
      `}</style>
    </div>
  )
}






















