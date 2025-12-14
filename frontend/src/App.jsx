import React, { useRef, useState, useEffect } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

/*
 * TERA - COMPREHENSIVE RISK INTELLIGENCE
 * Detailed reports + Justified mapping + Contextual analysis
 */

const PRESETS = ['Miami', 'Jakarta', 'Tokyo', 'Venice', 'Cairo', 'Kyiv', 'Mumbai', 'Singapore', 'Berlin', 'Lagos']

const RISK_INFO = {
  coastal_flood: { color: '#00bfff', icon: '🌊', name: 'Küstenflut', desc: 'Überschwemmung durch Meeresanstieg und Sturmfluten' },
  flood: { color: '#1e90ff', icon: '💧', name: 'Überschwemmung', desc: 'Fluviale und pluviale Überschwemmungen' },
  urban_flood: { color: '#4169e1', icon: '🏙️', name: 'Urban Flood', desc: 'Überlastung der städtischen Entwässerung' },
  drought: { color: '#ff8c00', icon: '☀️', name: 'Dürre', desc: 'Wassermangel und Desertifikation' },
  heat_stress: { color: '#ff4500', icon: '🌡️', name: 'Hitzestress', desc: 'Extreme Temperaturen und Wärmeinseleffekt' },
  seismic: { color: '#9932cc', icon: '🌋', name: 'Seismisch', desc: 'Erdbeben und tektonische Aktivität' },
  conflict: { color: '#dc143c', icon: '⚔️', name: 'Konflikt', desc: 'Bewaffnete Konflikte und Instabilität' },
  stable: { color: '#32cd32', icon: '✓', name: 'Stabil', desc: 'Niedriges Risiko, gute Anpassungsfähigkeit' }
}

// Hopf Fibration Logo
function HopfLogo() {
  const ref = useRef(null)
  useEffect(() => {
    const c = ref.current, ctx = c?.getContext('2d')
    if (!ctx) return
    let id, t = 0
    const draw = () => {
      t += 0.012
      ctx.fillStyle = '#080808'
      ctx.fillRect(0, 0, 55, 55)
      for (let i = 0; i < 14; i++) {
        const p = (i/14) * Math.PI * 2
        const r = 16 + Math.sin(t*2 + p) * 3
        ctx.beginPath()
        ctx.strokeStyle = `hsla(${175 + i*8}, 100%, 55%, ${0.3 + Math.sin(t + p) * 0.15})`
        ctx.lineWidth = 1
        ctx.ellipse(27.5, 27.5, r, r*0.28, t*0.25 + p, 0, Math.PI*2)
        ctx.stroke()
      }
      ctx.beginPath()
      ctx.fillStyle = '#00ffff'
      ctx.shadowColor = '#00ffff'
      ctx.shadowBlur = 12
      ctx.arc(27.5, 27.5, 2, 0, Math.PI*2)
      ctx.fill()
      ctx.shadowBlur = 0
      id = requestAnimationFrame(draw)
    }
    draw()
    return () => cancelAnimationFrame(id)
  }, [])
  return <canvas ref={ref} width={55} height={55} style={{ borderRadius: '50%' }} />
}

export default function App() {
  const mapDiv = useRef(null)
  const map = useRef(null)
  
  const [input, setInput] = useState('Miami')
  const [loading, setLoading] = useState(false)
  const [city, setCity] = useState('')
  const [report, setReport] = useState(null)
  const [cells, setCells] = useState(0)
  const [phase, setPhase] = useState('')
  const [zoneStats, setZoneStats] = useState({})

  function animateHexagons(features) {
    if (!map.current || !features.length) return
    const src = map.current.getSource('hex')
    if (!src) return
    
    // Calculate zone statistics
    const stats = {}
    features.forEach(f => {
      const zone = f.properties.zone || 'unknown'
      const risk = f.properties.primary_risk || 'stable'
      if (!stats[zone]) stats[zone] = { count: 0, totalIntensity: 0, risk, reasons: new Set() }
      stats[zone].count++
      stats[zone].totalIntensity += f.properties.intensity || 0
      if (f.properties.zone_reason) stats[zone].reasons.add(f.properties.zone_reason)
    })
    Object.keys(stats).forEach(z => {
      stats[z].avgIntensity = stats[z].totalIntensity / stats[z].count
      stats[z].reasons = Array.from(stats[z].reasons)[0] || ''
    })
    setZoneStats(stats)
    
    let frame = 0
    const total = 90
    
    function animate() {
      frame++
      const t = Math.min(frame / total, 1)
      const eased = 1 - Math.pow(1 - t, 3)
      
      if (t < 0.2) setPhase('KARTIERUNG')
      else if (t < 0.4) setPhase('TESSELLIERUNG')
      else if (t < 0.6) setPhase('RISIKOANALYSE')
      else if (t < 0.8) setPhase('3D EXTRUSION')
      else if (t < 1) setPhase('KALIBRIERUNG')
      else setPhase('')
      
      const animated = features.map((f, i) => {
        const delay = (i % 70) / 70 * 0.35
        const progress = Math.max(0, Math.min(1, (t - delay) / (1 - delay)))
        const height = progress * progress * (f.properties.intensity || 0.5) * 450
        return { ...f, properties: { ...f.properties, height } }
      })
      
      src.setData({ type: 'FeatureCollection', features: animated })
      
      if (frame < total) {
        requestAnimationFrame(animate)
      } else {
        const final = features.map(f => ({
          ...f,
          properties: { ...f.properties, height: (f.properties.intensity || 0.5) * 450 }
        }))
        src.setData({ type: 'FeatureCollection', features: final })
      }
    }
    requestAnimationFrame(animate)
  }

  async function analyze(name) {
    if (!map.current) return
    setLoading(true)
    setCity(name)
    setPhase('VERBINDUNG')
    setZoneStats({})
    
    try {
      const res = await fetch('/api/analysis/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ location: name })
      })
      const data = await res.json()
      setReport(data)
      
      let zoom = 12
      if (data.bbox) {
        const size = Math.max(Math.abs(data.bbox[1]-data.bbox[0]), Math.abs(data.bbox[3]-data.bbox[2]))
        zoom = size > 0.5 ? 10 : size > 0.2 ? 11 : size > 0.1 ? 12 : 13
      }
      
      map.current.flyTo({
        center: [data.longitude, data.latitude],
        zoom,
        pitch: 55,
        bearing: 10,
        duration: 2500
      })
      
      setTimeout(async () => {
        setPhase('LADE ZELLEN')
        const hexRes = await fetch(`/api/analysis/risk-map?city=${encodeURIComponent(name)}&resolution=10`)
        const hexData = await hexRes.json()
        setCells(hexData.features?.length || 0)
        if (hexData.features?.length) {
          animateHexagons(hexData.features)
        }
      }, 2700)
      
    } catch (e) {
      console.error(e)
      setPhase('FEHLER')
    }
    setLoading(false)
  }

  useEffect(() => {
    if (map.current) return
    
    map.current = new maplibregl.Map({
      container: mapDiv.current,
      style: {
        version: 8,
        sources: {
          satellite: {
            type: 'raster',
            tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
            tileSize: 256
          }
        },
        layers: [{ id: 'satellite', type: 'raster', source: 'satellite' }]
      },
      center: [-80.19, 25.76],
      zoom: 12,
      pitch: 55,
      bearing: 10
    })
    
    map.current.addControl(new maplibregl.NavigationControl())
    
    map.current.on('load', () => {
      map.current.addSource('hex', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      })
      
      map.current.addLayer({
        id: 'hex3d',
        type: 'fill-extrusion',
        source: 'hex',
        paint: {
          'fill-extrusion-color': [
            'match', ['get', 'primary_risk'],
            'coastal_flood', '#00bfff',
            'flood', '#1e90ff',
            'urban_flood', '#4169e1',
            'drought', '#ff8c00',
            'heat_stress', '#ff4500',
            'seismic', '#9932cc',
            'conflict', '#dc143c',
            'stable', '#32cd32',
            '#6495ed'
          ],
          'fill-extrusion-height': ['get', 'height'],
          'fill-extrusion-base': 0,
          'fill-extrusion-opacity': 0.88,
          'fill-extrusion-vertical-gradient': true
        }
      })
      
      map.current.addLayer({
        id: 'hexline',
        type: 'line',
        source: 'hex',
        paint: { 'line-color': '#00ffff', 'line-width': 0.5, 'line-opacity': 0.4 }
      })
      
      analyze('Miami')
    })
    
    // Detailed popup on click
    map.current.on('click', 'hex3d', (e) => {
      if (!e.features?.[0]) return
      const p = e.features[0].properties
      const info = RISK_INFO[p.primary_risk] || { color: '#6495ed', icon: '📍', name: p.primary_risk, desc: '' }
      const pct = ((p.intensity||0)*100).toFixed(0)
      
      new maplibregl.Popup({ maxWidth: '420px' })
        .setLngLat(e.lngLat)
        .setHTML(`
          <div style="background:#0a0a0a;color:#fff;padding:20px;border-radius:14px;font-family:system-ui;border:3px solid ${info.color}">
            <div style="display:flex;align-items:center;gap:14px;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid #333">
              <span style="font-size:42px;filter:drop-shadow(0 0 8px ${info.color})">${info.icon}</span>
              <div style="flex:1">
                <div style="font-weight:700;color:${info.color};font-size:17px;letter-spacing:1px">${(p.zone || '').replace(/_/g, ' ')}</div>
                <div style="font-size:11px;color:#aaa;margin-top:3px">${info.name} - ${info.desc}</div>
              </div>
              <div style="text-align:right">
                <div style="font-size:36px;font-weight:700;color:${info.color}">${pct}%</div>
                <div style="font-size:9px;color:#666">RISIKO</div>
              </div>
            </div>
            
            <div style="font-size:11px;color:#00ffff;margin-bottom:8px;letter-spacing:1px">📋 BEGRÜNDUNG</div>
            <div style="font-size:12px;color:#ddd;line-height:1.8;background:#111;padding:14px;border-radius:10px;border-left:4px solid ${info.color};margin-bottom:14px">
              ${p.zone_reason || 'Detaillierte Analyse wird durchgeführt...'}
            </div>
            
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:10px">
              <div style="background:#111;padding:10px;border-radius:6px">
                <div style="color:#666;margin-bottom:4px">KLIMARISIKO</div>
                <div style="color:#00bfff;font-size:14px;font-weight:bold">${((p.climate_risk||0)*100).toFixed(0)}%</div>
              </div>
              <div style="background:#111;padding:10px;border-radius:6px">
                <div style="color:#666;margin-bottom:4px">3D HÖHE</div>
                <div style="color:#fff;font-size:14px;font-weight:bold">${((p.intensity||0)*450).toFixed(0)}m</div>
              </div>
            </div>
          </div>
        `)
        .addTo(map.current)
    })
    
    map.current.on('mouseenter', 'hex3d', () => map.current.getCanvas().style.cursor = 'pointer')
    map.current.on('mouseleave', 'hex3d', () => map.current.getCanvas().style.cursor = '')
  }, [])

  const riskPct = report ? (report.risk_score * 100).toFixed(0) : '0'
  const climatePct = report ? (report.climate_risk * 100).toFixed(0) : '0'
  const conflictPct = report ? (report.conflict_risk * 100).toFixed(0) : '0'
  const riskColor = parseFloat(riskPct) > 60 ? '#dc143c' : parseFloat(riskPct) > 40 ? '#ff8c00' : parseFloat(riskPct) > 25 ? '#ffd700' : '#32cd32'

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#050505', fontFamily: 'system-ui', color: '#fff' }}>
      {/* MAP */}
      <div style={{ flex: 1, position: 'relative' }}>
        <div ref={mapDiv} style={{ width: '100%', height: '100%' }} />
        
        <div style={{ position: 'absolute', top: 20, left: 20, background: 'rgba(0,0,0,0.9)', padding: '8px 14px', borderRadius: 8, border: '1px solid #00ffff', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 14 }}>🛰️</span>
          <span style={{ color: '#00ffff', fontSize: 10, fontWeight: 'bold' }}>SATELLIT</span>
        </div>
        
        <div style={{ position: 'absolute', top: 20, right: 60, background: 'rgba(0,0,0,0.9)', padding: '14px 22px', borderRadius: 12, border: '1px solid #333' }}>
          <div style={{ fontSize: 28, color: '#00ffff', fontWeight: 700 }}>{cells.toLocaleString()}</div>
          <div style={{ fontSize: 9, color: '#666', letterSpacing: 1 }}>RISIKOZELLEN</div>
          {phase && <div style={{ fontSize: 10, color: '#00ffff', marginTop: 6 }}>⟳ {phase}</div>}
        </div>
        
        {city && (
          <div style={{ position: 'absolute', bottom: 25, left: '50%', transform: 'translateX(-50%)', background: 'rgba(0,0,0,0.9)', padding: '12px 35px', borderRadius: 25, border: '1px solid #333' }}>
            📍 {city.toUpperCase()} <span style={{ color: '#00ffff', marginLeft: 8, fontSize: 10 }}>[{report?.city_type}]</span>
          </div>
        )}
        
        {loading && (
          <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.92)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 65 }}>🛰️</div>
              <div style={{ color: '#00ffff', marginTop: 20, fontSize: 16, letterSpacing: 2 }}>ANALYSIERE {input.toUpperCase()}</div>
            </div>
          </div>
        )}
      </div>
      
      {/* DETAILED REPORT PANEL */}
      <div style={{ width: 420, background: '#080808', borderLeft: '1px solid #1a1a1a', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #1a1a1a', display: 'flex', alignItems: 'center', gap: 12 }}>
          <HopfLogo />
          <div>
            <div style={{ fontSize: 24, color: '#00ffff', letterSpacing: 5, fontWeight: 200 }}>TERA</div>
            <div style={{ fontSize: 7, color: '#555', letterSpacing: 1 }}>RISIKO INTELLIGENCE REPORT</div>
          </div>
        </div>
        
        {/* Search */}
        <div style={{ padding: '12px 20px', borderBottom: '1px solid #1a1a1a' }}>
          <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && analyze(input)}
              placeholder="Stadt eingeben..."
              style={{ flex: 1, padding: '11px 14px', background: '#111', border: '1px solid #333', borderRadius: 8, color: '#fff', fontSize: 13 }}
            />
            <button onClick={() => analyze(input)} disabled={loading}
              style={{ padding: '11px 18px', background: '#00ffff', border: 'none', borderRadius: 8, color: '#000', fontWeight: 700, cursor: 'pointer' }}>→</button>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {PRESETS.map(c => (
              <button key={c} onClick={() => { setInput(c); analyze(c) }}
                style={{ padding: '4px 9px', background: city === c ? '#00ffff22' : '#111', border: `1px solid ${city === c ? '#00ffff' : '#333'}`, borderRadius: 5, color: city === c ? '#00ffff' : '#777', fontSize: 9, cursor: 'pointer' }}>{c}</button>
            ))}
          </div>
        </div>
        
        {/* DETAILED REPORT */}
        <div style={{ flex: 1, overflow: 'auto', padding: '16px 20px' }}>
          {report ? (
            <>
              {/* Risk Summary */}
              <div style={{ textAlign: 'center', padding: 20, background: '#111', borderRadius: 14, marginBottom: 16, border: `2px solid ${riskColor}44` }}>
                <div style={{ fontSize: 58, fontWeight: 200, color: riskColor, lineHeight: 1 }}>{riskPct}%</div>
                <div style={{ fontSize: 9, color: '#666', letterSpacing: 2, marginTop: 6 }}>GESAMTRISIKO-INDEX</div>
                <div style={{ display: 'flex', justifyContent: 'center', gap: 30, marginTop: 18 }}>
                  <div><div style={{ fontSize: 24, color: '#00bfff' }}>{climatePct}%</div><div style={{ fontSize: 8, color: '#555' }}>🌡️ KLIMA</div></div>
                  <div><div style={{ fontSize: 24, color: '#dc143c' }}>{conflictPct}%</div><div style={{ fontSize: 8, color: '#555' }}>⚔️ KONFLIKT</div></div>
                </div>
              </div>
              
              {/* 2050 Projection */}
              <div style={{ padding: 14, background: 'linear-gradient(145deg, #0a1525, #150a20)', borderRadius: 12, border: '1px solid #00ffff22', marginBottom: 16 }}>
                <div style={{ fontSize: 9, color: '#00ffff', letterSpacing: 2, marginBottom: 8 }}>📊 PROGNOSE 2050 (IPCC SSP2-4.5)</div>
                <div style={{ fontSize: 11, color: '#bbb', lineHeight: 1.75 }}>{report.projection_2050}</div>
              </div>
              
              {/* Zone-by-Zone Report */}
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 9, color: '#00ffff', letterSpacing: 2, marginBottom: 12 }}>🗺️ ZONEN-ANALYSE (BEGRÜNDET)</div>
                <div style={{ fontSize: 10, color: '#888', marginBottom: 12, lineHeight: 1.5 }}>
                  Jede Zone zeigt: <span style={{ color: '#fff' }}>Farbe = Risikoart</span>, <span style={{ color: '#fff' }}>Höhe = Intensität</span>. 
                  Klicken Sie auf eine Zelle für Details.
                </div>
                
                {Object.entries(zoneStats).sort((a,b) => b[1].avgIntensity - a[1].avgIntensity).map(([zone, data]) => {
                  const info = RISK_INFO[data.risk] || { color: '#6495ed', icon: '📍', name: data.risk }
                  const pct = (data.avgIntensity * 100).toFixed(0)
                  return (
                    <div key={zone} style={{ background: '#111', borderLeft: `4px solid ${info.color}`, borderRadius: 8, padding: 14, marginBottom: 10 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <span style={{ fontSize: 22 }}>{info.icon}</span>
                          <div>
                            <div style={{ fontWeight: 600, fontSize: 12 }}>{zone.replace(/_/g, ' ')}</div>
                            <div style={{ fontSize: 9, color: info.color }}>{info.name}</div>
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: 22, fontWeight: 700, color: info.color }}>{pct}%</div>
                          <div style={{ fontSize: 8, color: '#666' }}>{data.count} Zellen</div>
                        </div>
                      </div>
                      <div style={{ fontSize: 11, color: '#aaa', lineHeight: 1.6, background: '#0a0a0a', padding: 10, borderRadius: 6 }}>
                        {data.reasons || `${info.name}: Analyse basierend auf IPCC AR6 Klimaprojektionen und lokalen Faktoren.`}
                      </div>
                    </div>
                  )
                })}
              </div>
              
              {/* Recommendations */}
              {report.recommendations && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 9, color: '#00ffff', letterSpacing: 2, marginBottom: 12 }}>🎯 HANDLUNGSEMPFEHLUNGEN</div>
                  {report.recommendations.slice(0, 3).map((rec, i) => {
                    const pColor = rec.priority === 'CRITICAL' ? '#dc143c' : rec.priority === 'HIGH' ? '#ffa500' : '#32cd32'
                    return (
                      <div key={i} style={{ background: '#111', borderLeft: `3px solid ${pColor}`, borderRadius: 6, padding: 12, marginBottom: 8 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                          <span style={{ fontSize: 8, padding: '2px 6px', background: `${pColor}22`, color: pColor, borderRadius: 3, fontWeight: 700 }}>{rec.priority}</span>
                          <span style={{ fontSize: 9, color: '#555' }}>{rec.timeline}</span>
                        </div>
                        <div style={{ fontSize: 11, fontWeight: 600 }}>{rec.action}</div>
                        <div style={{ fontSize: 9, color: '#666', marginTop: 4 }}>📖 {rec.source}</div>
                      </div>
                    )
                  })}
                </div>
              )}
              
              {/* Location Info */}
              <div style={{ padding: 12, background: '#111', borderRadius: 8 }}>
                <div style={{ fontSize: 9, color: '#555', letterSpacing: 1, marginBottom: 8 }}>📍 STANDORT</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '5px', fontSize: 10 }}>
                  <div><span style={{ color: '#555' }}>Stadt:</span> {report.location}</div>
                  <div><span style={{ color: '#555' }}>Land:</span> {report.country}</div>
                  <div><span style={{ color: '#555' }}>Typ:</span> <span style={{ color: '#00ffff' }}>{report.city_type}</span></div>
                  <div><span style={{ color: '#555' }}>Zellen:</span> <span style={{ color: '#00ffff' }}>{cells}</span></div>
                </div>
              </div>
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: 45, color: '#555' }}>
              <div style={{ fontSize: 50, marginBottom: 18 }}>🛰️</div>
              <div style={{ fontSize: 12 }}>Stadt eingeben für Analyse</div>
            </div>
          )}
        </div>
        
        {/* Legend */}
        <div style={{ padding: '10px 20px', borderTop: '1px solid #1a1a1a', background: '#050505' }}>
          <div style={{ fontSize: 8, color: '#555', marginBottom: 6 }}>FARBLEGENDE (Risikoart)</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px 10px' }}>
            {Object.entries(RISK_INFO).map(([k, { color, icon, name }]) => (
              <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <div style={{ width: 8, height: 8, background: color, borderRadius: 2 }} />
                <span style={{ fontSize: 7, color: '#666' }}>{name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
