import { useState, useEffect } from 'react'
import axios from 'axios'

const MARKER_STYLES = [
  { id: 'car-green', label: 'רכב ירוק', color: '#16a34a', icon: '🚗' },
  { id: 'pin-red', label: 'סיכה אדומה', color: '#dc2626', icon: '📍' },
  { id: 'pin-blue', label: 'סיכה כחולה', color: '#2563eb', icon: '📍' },
  { id: 'pin-green', label: 'סיכה ירוקה', color: '#16a34a', icon: '📍' },
  { id: 'circle-red', label: 'עיגול אדום', color: '#dc2626', icon: '⭕' },
  { id: 'circle-blue', label: 'עיגול כחול', color: '#2563eb', icon: '⭕' },
  { id: 'star', label: 'כוכב', color: '#f59e0b', icon: '⭐' },
  { id: 'square', label: 'ריבוע', color: '#7c3aed', icon: '🟪' },
]

const DATABASES = [
  {
    id: 'parking',
    label: 'מתקני חניה',
    endpoint: '/api/parking/ours',
  },
  {
    id: 'chargers',
    label: 'מטענים',
    endpoint: '/api/chargers/sites',
  },
]

function DatabaseLayersPanel({ onLayerChange, activeLayers, onClose }) {
  const [markerSelecting, setMarkerSelecting] = useState(null) // which db is selecting marker

  const handleToggle = (dbId) => {
    const current = activeLayers[dbId]
    if (current) {
      // Turn off
      onLayerChange(dbId, null)
    } else {
      // Show marker picker
      setMarkerSelecting(dbId)
    }
  }

  const handleMarkerSelect = (dbId, marker) => {
    onLayerChange(dbId, marker)
    setMarkerSelecting(null)
  }

  return (
    <div className="absolute top-4 right-4 z-[1000] w-80 bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-sky-200">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-sky-100">
        <h3 className="text-sm font-bold text-blue-900">בסיסי נתונים על המפה</h3>
        <button onClick={onClose} className="text-sky-300 hover:text-sky-600 text-lg leading-none">
          &times;
        </button>
      </div>

      {/* Database list */}
      <div className="p-4 flex flex-col gap-4">
        {DATABASES.map((db) => {
          const isActive = !!activeLayers[db.id]
          const activeMarker = activeLayers[db.id]

          return (
            <div key={db.id} className="flex flex-col gap-2">
              <label className="flex items-center gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={() => handleToggle(db.id)}
                  className="w-4 h-4 text-sky-500 rounded border-sky-300 focus:ring-sky-400 cursor-pointer"
                />
                <span className="text-base text-blue-900 group-hover:text-blue-700">
                  {db.label}
                </span>
                {isActive && activeMarker && (
                  <span
                    className="mr-auto text-xs px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: activeMarker.color + '20', color: activeMarker.color }}
                  >
                    {activeMarker.icon} {activeMarker.label}
                  </span>
                )}
              </label>

              {/* Marker style picker */}
              {markerSelecting === db.id && (
                <div className="mr-7 grid grid-cols-2 gap-2">
                  {MARKER_STYLES.map((marker) => (
                    <button
                      key={marker.id}
                      onClick={() => handleMarkerSelect(db.id, marker)}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg border border-sky-100
                                 hover:border-sky-300 hover:bg-sky-50 transition-colors text-sm"
                    >
                      <span style={{ color: marker.color }}>{marker.icon}</span>
                      <span className="text-blue-900">{marker.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default DatabaseLayersPanel
