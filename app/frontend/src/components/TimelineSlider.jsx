import React, { useState, useEffect } from "react"

/**
 * TimelineSlider - Temporal Risk Animation Component
 * Allows users to project risks into the future (2024-2100)
 * and switch between IPCC SSP scenarios.
 */
export default function TimelineSlider({ onYearChange, onScenarioChange, currentYear = 2026, currentScenario = "SSP2-4.5" }) {
  const [year, setYear] = useState(currentYear)
  const [scenario, setScenario] = useState(currentScenario)
  const [isPlaying, setIsPlaying] = useState(false)
  
  const scenarios = [
    { id: "SSP1-1.9", label: "🌱 SSP1-1.9", desc: "Nachhaltigkeit (+1.5°C)", color: "#22c55e" },
    { id: "SSP2-4.5", label: "📊 SSP2-4.5", desc: "Mittlerer Weg (+2.7°C)", color: "#eab308" },
    { id: "SSP5-8.5", label: "🔥 SSP5-8.5", desc: "Fossil-intensiv (+4.4°C)", color: "#ef4444" }
  ]
  
  // Animation loop
  useEffect(() => {
    if (!isPlaying) return
    const interval = setInterval(() => {
      setYear(y => {
        const next = y >= 2100 ? 2024 : y + 5
        return next
      })
    }, 1500)
    return () => clearInterval(interval)
  }, [isPlaying])
  
  // Notify parent on changes
  useEffect(() => {
    onYearChange?.(year)
  }, [year, onYearChange])
  
  useEffect(() => {
    onScenarioChange?.(scenario)
  }, [scenario, onScenarioChange])
  
  // Calculate color based on year
  const getYearColor = () => {
    const progress = (year - 2024) / (2100 - 2024)
    if (progress < 0.33) return "#22c55e"
    if (progress < 0.66) return "#eab308"
    return "#ef4444"
  }
  
  return (
    <div style={{
      background: "rgba(0,0,0,0.85)",
      borderRadius: 12,
      padding: 16,
      marginTop: 12,
      border: "1px solid #333"
    }}>
      {/* Header */}
      <div style={{ 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "center",
        marginBottom: 12 
      }}>
        <div style={{ fontSize: 10, color: "#00ffff", letterSpacing: 2 }}>
          ⏳ ZEITPROJEKTION
        </div>
        <div style={{ 
          fontSize: 24, 
          fontWeight: 700, 
          color: getYearColor(),
          fontFamily: "monospace"
        }}>
          {year}
        </div>
      </div>
      
      {/* Timeline Slider */}
      <div style={{ marginBottom: 16 }}>
        <input
          type="range"
          min={2024}
          max={2100}
          step={1}
          value={year}
          onChange={(e) => setYear(parseInt(e.target.value))}
          style={{
            width: "100%",
            accentColor: getYearColor(),
            height: 8,
            cursor: "pointer"
          }}
        />
        <div style={{ 
          display: "flex", 
          justifyContent: "space-between", 
          fontSize: 9, 
          color: "#666",
          marginTop: 4 
        }}>
          <span>2024</span>
          <span>2040</span>
          <span>2060</span>
          <span>2080</span>
          <span>2100</span>
        </div>
      </div>
      
      {/* Play/Pause Button */}
      <button
        onClick={() => setIsPlaying(!isPlaying)}
        style={{
          width: "100%",
          padding: "8px 16px",
          background: isPlaying ? "#ef4444" : "#22c55e",
          border: "none",
          borderRadius: 6,
          color: "#fff",
          fontWeight: 600,
          cursor: "pointer",
          marginBottom: 12,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 8
        }}
      >
        {isPlaying ? "⏸ Animation stoppen" : "▶ Zeitreise starten"}
      </button>
      
      {/* Scenario Buttons */}
      <div style={{ fontSize: 10, color: "#888", marginBottom: 8 }}>
        IPCC SZENARIO:
      </div>
      <div style={{ display: "flex", gap: 6 }}>
        {scenarios.map(s => (
          <button
            key={s.id}
            onClick={() => setScenario(s.id)}
            style={{
              flex: 1,
              padding: "8px 4px",
              background: scenario === s.id ? s.color : "#222",
              border: scenario === s.id ? `2px solid ${s.color}` : "1px solid #444",
              borderRadius: 6,
              color: scenario === s.id ? "#fff" : "#888",
              fontSize: 9,
              cursor: "pointer",
              transition: "all 0.2s"
            }}
            title={s.desc}
          >
            {s.label}
          </button>
        ))}
      </div>
      
      {/* Current Scenario Description */}
      <div style={{ 
        marginTop: 12, 
        padding: 8, 
        background: "#111", 
        borderRadius: 6,
        fontSize: 10,
        color: "#888"
      }}>
        <strong style={{ color: scenarios.find(s => s.id === scenario)?.color }}>
          {scenario}:
        </strong> {scenarios.find(s => s.id === scenario)?.desc}
      </div>
    </div>
  )
}
