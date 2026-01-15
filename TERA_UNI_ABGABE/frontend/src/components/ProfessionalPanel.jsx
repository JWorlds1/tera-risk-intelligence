import React from "react"

/*
 * Professional Analysis Panel
 * Zeigt Bayesian Uncertainty, Szenarien und Empfehlungen
 */

// Uncertainty Bar Component
function UncertaintyBar({ label, data, icon, color }) {
  if (!data) return null
  
  const mean = data.mean * 100
  const lower = data.ci_95_lower * 100
  const upper = data.ci_95_upper * 100
  const confidence = data.confidence * 100
  
  // Farbe basierend auf Risiko
  const riskColor = mean > 50 ? "#ff4444" : mean > 30 ? "#ffaa00" : "#44ff44"
  
  return (
    <div style={{ marginBottom: "12px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
        <span style={{ color: "#aaa", fontSize: "12px" }}>
          {icon} {label}
        </span>
        <span style={{ color: riskColor, fontWeight: "bold", fontSize: "14px" }}>
          {mean.toFixed(0)}% 
          <span style={{ color: "#666", fontWeight: "normal", fontSize: "11px" }}>
            [{lower.toFixed(0)}-{upper.toFixed(0)}%]
          </span>
        </span>
      </div>
      
      {/* Uncertainty Bar */}
      <div style={{ 
        position: "relative", 
        height: "8px", 
        background: "#222",
        borderRadius: "4px",
        overflow: "hidden"
      }}>
        {/* Uncertainty Range (transparent) */}
        <div style={{
          position: "absolute",
          left: `${lower}%`,
          width: `${upper - lower}%`,
          height: "100%",
          background: `${riskColor}33`,
          borderRadius: "4px"
        }} />
        
        {/* Mean Value (solid) */}
        <div style={{
          position: "absolute",
          left: 0,
          width: `${mean}%`,
          height: "100%",
          background: riskColor,
          borderRadius: "4px",
          transition: "width 0.5s ease"
        }} />
      </div>
      
      <div style={{ 
        fontSize: "10px", 
        color: "#666", 
        marginTop: "2px",
        fontStyle: "italic"
      }}>
        {data.interpretation} • Konfidenz: {confidence.toFixed(0)}%
      </div>
    </div>
  )
}

// Scenario Comparison Component
function ScenarioComparison({ scenarios }) {
  if (!scenarios) return null
  
  const scenarioOrder = ["SSP1-1.9", "SSP2-4.5", "SSP5-8.5"]
  const colors = {
    "SSP1-1.9": "#44ff88",
    "SSP2-4.5": "#ffaa44", 
    "SSP5-8.5": "#ff4444"
  }
  
  return (
    <div style={{
      background: "#111",
      borderRadius: "8px",
      padding: "12px",
      marginTop: "16px"
    }}>
      <div style={{ 
        color: "#00ffff", 
        fontSize: "12px", 
        marginBottom: "12px",
        borderBottom: "1px solid #333",
        paddingBottom: "8px"
      }}>
        📊 SZENARIO-VERGLEICH (IPCC SSP)
      </div>
      
      {scenarioOrder.map(key => {
        const scenario = scenarios[key]
        if (!scenario) return null
        
        const risk = Math.min(scenario.total_risk * 100, 100)
        const isActive = key === "SSP2-4.5"
        
        return (
          <div key={key} style={{ marginBottom: "10px" }}>
            <div style={{ 
              display: "flex", 
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "4px"
            }}>
              <span style={{ 
                color: isActive ? "#fff" : "#888",
                fontSize: "11px",
                fontWeight: isActive ? "bold" : "normal"
              }}>
                {key} {isActive && "← Aktuell"}
              </span>
              <span style={{ 
                color: colors[key],
                fontSize: "12px",
                fontWeight: "bold"
              }}>
                {risk.toFixed(0)}%
              </span>
            </div>
            
            <div style={{
              height: "6px",
              background: "#222",
              borderRadius: "3px",
              overflow: "hidden"
            }}>
              <div style={{
                width: `${risk}%`,
                height: "100%",
                background: colors[key],
                borderRadius: "3px",
                transition: "width 0.5s ease"
              }} />
            </div>
            
            <div style={{ 
              fontSize: "9px", 
              color: "#555",
              marginTop: "2px"
            }}>
              {scenario.description}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// Recommendations Component
function Recommendations({ recommendations }) {
  if (!recommendations || recommendations.length === 0) return null
  
  const priorityColors = {
    CRITICAL: "#ff4444",
    HIGH: "#ffaa00",
    MEDIUM: "#44aaff",
    LOW: "#44ff44"
  }
  
  return (
    <div style={{
      background: "#111",
      borderRadius: "8px",
      padding: "12px",
      marginTop: "16px"
    }}>
      <div style={{ 
        color: "#00ffff", 
        fontSize: "12px", 
        marginBottom: "12px",
        borderBottom: "1px solid #333",
        paddingBottom: "8px"
      }}>
        🎯 PRIORISIERTE EMPFEHLUNGEN
      </div>
      
      {recommendations.slice(0, 4).map((rec, idx) => (
        <div key={idx} style={{
          background: "#0a0a0a",
          borderRadius: "6px",
          padding: "10px",
          marginBottom: "8px",
          borderLeft: `3px solid ${priorityColors[rec.priority] || "#666"}`
        }}>
          <div style={{ 
            display: "flex", 
            justifyContent: "space-between",
            marginBottom: "4px"
          }}>
            <span style={{
              color: priorityColors[rec.priority],
              fontSize: "10px",
              fontWeight: "bold"
            }}>
              {rec.priority}
            </span>
            <span style={{ color: "#666", fontSize: "10px" }}>
              {rec.timeline}
            </span>
          </div>
          
          <div style={{ color: "#fff", fontSize: "12px" }}>
            {rec.action}
          </div>
          
          {rec.confidence && (
            <div style={{ color: "#555", fontSize: "10px", marginTop: "4px" }}>
              Konfidenz: {rec.confidence}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// Main Professional Panel
export default function ProfessionalPanel({ analysis }) {
  if (!analysis) return null
  
  const { 
    location, 
    total_risk, 
    climate_risk, 
    conflict_risk, 
    seismic_risk,
    scenarios,
    recommendations,
    sources
  } = analysis
  
  return (
    <div style={{
      background: "linear-gradient(180deg, #0a0a0a 0%, #111 100%)",
      borderRadius: "12px",
      padding: "16px",
      marginTop: "20px",
      border: "1px solid #222"
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "16px",
        borderBottom: "1px solid #333",
        paddingBottom: "12px"
      }}>
        <div>
          <div style={{ color: "#00ffff", fontSize: "10px", letterSpacing: "2px" }}>
            PROFESSIONAL ANALYSIS
          </div>
          <div style={{ color: "#fff", fontSize: "18px", fontWeight: "bold" }}>
            {location?.city}
          </div>
          <div style={{ color: "#666", fontSize: "11px" }}>
            {location?.country} • {location?.type}
          </div>
        </div>
        
        {/* Total Risk Badge */}
        <div style={{
          background: total_risk?.mean > 0.5 ? "#ff4444" : total_risk?.mean > 0.3 ? "#ffaa00" : "#44ff44",
          borderRadius: "50%",
          width: "60px",
          height: "60px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center"
        }}>
          <div style={{ color: "#000", fontSize: "18px", fontWeight: "bold" }}>
            {(total_risk?.mean * 100).toFixed(0)}%
          </div>
          <div style={{ color: "#000", fontSize: "8px" }}>
            GESAMT
          </div>
        </div>
      </div>
      
      {/* Risk Breakdown with Uncertainty */}
      <div style={{ marginBottom: "16px" }}>
        <div style={{ 
          color: "#888", 
          fontSize: "10px", 
          letterSpacing: "1px",
          marginBottom: "12px"
        }}>
          RISIKO-BREAKDOWN MIT 95% KONFIDENZINTERVALL
        </div>
        
        <UncertaintyBar 
          label="Klima" 
          data={climate_risk} 
          icon="🌡️"
        />
        <UncertaintyBar 
          label="Konflikt" 
          data={conflict_risk} 
          icon="⚔️"
        />
        <UncertaintyBar 
          label="Seismik" 
          data={seismic_risk} 
          icon="🌋"
        />
      </div>
      
      {/* Scenario Comparison */}
      <ScenarioComparison scenarios={scenarios} />
      
      {/* Recommendations */}
      <Recommendations recommendations={recommendations} />
      
      {/* Sources */}
      {sources && sources.length > 0 && (
        <div style={{
          marginTop: "16px",
          paddingTop: "12px",
          borderTop: "1px solid #222"
        }}>
          <div style={{ color: "#555", fontSize: "10px" }}>
            DATENQUELLEN: {sources.join(" • ")}
          </div>
        </div>
      )}
    </div>
  )
}
