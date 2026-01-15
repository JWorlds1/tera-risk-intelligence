import React, { useState } from 'react'

export default function ExportButton({ city, year = 2026, scenario = 'SSP2-4.5' }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const handleExport = async () => {
    if (!city) return
    
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(
        `http://141.100.238.104:8080/api/extended/export-pdf?city=${encodeURIComponent(city)}&year=${year}&scenario=${encodeURIComponent(scenario)}`
      )
      
      if (!response.ok) {
        throw new Error('PDF generation failed')
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `TERA_${city}_${year}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      a.remove()
    } catch (err) {
      setError(err.message)
      console.error('Export error:', err)
    } finally {
      setLoading(false)
    }
  }
  
  if (!city) return null
  
  return (
    <div style={{ marginTop: 12 }}>
      <button
        onClick={handleExport}
        disabled={loading}
        style={{
          width: '100%',
          padding: '12px 16px',
          background: loading ? '#333' : 'linear-gradient(135deg, #00ffff 0%, #0099ff 100%)',
          border: 'none',
          borderRadius: 8,
          color: '#000',
          fontWeight: 700,
          fontSize: 12,
          cursor: loading ? 'wait' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
          transition: 'all 0.3s'
        }}
      >
        {loading ? (
          <>
            <span style={{ animation: 'spin 1s linear infinite' }}>⏳</span>
            Generiere PDF...
          </>
        ) : (
          <>
            📄 PDF Report herunterladen
          </>
        )}
      </button>
      
      {error && (
        <div style={{ 
          marginTop: 8, 
          padding: 8, 
          background: '#ff444433', 
          borderRadius: 4,
          fontSize: 10,
          color: '#ff4444'
        }}>
          ⚠️ {error}
        </div>
      )}
      
      <style>{
        `@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`
      }</style>
    </div>
  )
}
