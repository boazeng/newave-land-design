import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import MapControls from './MapControls'
import LayersPanel from './LayersPanel'
import CadastreLayer from './CadastreLayer'
import SearchPanel from '../Search/SearchPanel'
import DistrictsLayer from './DistrictsLayer'
import DatabaseLayersPanel from './DatabaseLayersPanel'
import DatabaseMarkers from './DatabaseMarkers'
import PlansLayer from './PlansLayer'

const DB_OPTIONS = [
  { value: 'plans_tanai_saf',      label: 'תנאי סף',         color: '#7c3aed', bg: '#f5f3ff' },
  { value: 'plans_milui_tnaim',    label: 'מילוי תנאים',     color: '#16a34a', bg: '#f0fdf4' },
  { value: 'plans_bdika_tichnunit',label: 'בדיקה תכנונית',   color: '#92400e', bg: '#fef3c7' },
]

function PlanFilterPanel({ plansDb, setPlansDb, plansFilter, setPlansFilter }) {
  const posRef = useRef(null)
  const [pos, setPos] = useState({ top: 80, left: 56 })
  const dragging = useRef(false)
  const startRef = useRef({})

  const activeDb = DB_OPTIONS.find(d => d.value === plansDb) || DB_OPTIONS[0]

  const onMouseDown = (e) => {
    if (e.target.tagName === 'SELECT' || e.target.tagName === 'OPTION') return
    dragging.current = true
    startRef.current = { mx: e.clientX, my: e.clientY, top: pos.top, left: pos.left }
    e.preventDefault()
  }

  useEffect(() => {
    const onMove = (e) => {
      if (!dragging.current) return
      setPos({
        top: startRef.current.top + (e.clientY - startRef.current.my),
        left: startRef.current.left + (e.clientX - startRef.current.mx),
      })
    }
    const onUp = () => { dragging.current = false }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp) }
  }, [])

  return (
    <div
      ref={posRef}
      onMouseDown={onMouseDown}
      style={{
        position: 'absolute', top: pos.top, left: pos.left,
        zIndex: 1000, background: 'white', borderRadius: 12,
        boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
        border: `2px solid ${activeDb.color}`,
        padding: '10px 12px', minWidth: 170, direction: 'rtl',
        cursor: 'grab', userSelect: 'none',
      }}
    >
      <div style={{ fontWeight: 700, fontSize: 11, color: activeDb.color, marginBottom: 6 }}>
        מאגר תוכניות
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 8 }}>
        {DB_OPTIONS.map(db => (
          <button
            key={db.value}
            onClick={() => setPlansDb(db.value)}
            style={{
              padding: '4px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600,
              border: `1.5px solid ${db.color}`, cursor: 'pointer', textAlign: 'right',
              background: plansDb === db.value ? db.color : db.bg,
              color: plansDb === db.value ? 'white' : db.color,
              transition: 'all 0.15s',
            }}
          >
            {db.label}
          </button>
        ))}
      </div>
      <div style={{ fontWeight: 700, fontSize: 11, color: '#6b7280', marginBottom: 4 }}>סינון</div>
      <select
        value={plansFilter}
        onChange={e => setPlansFilter(e.target.value)}
        style={{
          width: '100%', padding: '3px 6px', border: `1px solid ${activeDb.color}`,
          borderRadius: 6, fontSize: 11, background: 'white', cursor: 'pointer',
        }}
      >
        <option value="all">הכל</option>
        <option value="not_reviewed">לא נבדק</option>
        <option value="reviewed">נבדק</option>
        <option value="continue">המשך טיפול</option>
        <option value="high">עדיפות גבוהה</option>
        <option value="medium">עדיפות בינונית</option>
        <option value="low">עדיפות נמוכה</option>
      </select>
    </div>
  )
}

// Israel bounds
const ISRAEL_BOUNDS = [
  [29.45, 34.25], // South-West
  [33.35, 35.90], // North-East
]

const ISRAEL_CENTER = [31.5, 34.85]
const DEFAULT_ZOOM = 8
const MIN_ZOOM = 7
const MAX_ZOOM = 22

// Layer definitions
const INITIAL_LAYERS = [
  {
    id: 'districts',
    name: 'מחוזות תכנון',
    description: 'תחומי מחוזות תכנון ובנייה',
    visible: false,
  },
  {
    id: 'blocks',
    name: 'גושים',
    description: 'גבולות גושי רישום (זום 12+)',
    visible: false,
  },
  {
    id: 'parcels',
    name: 'חלקות',
    description: 'חלקות רישום בתוך גושים (זום 15+)',
    visible: false,
  },
  {
    id: 'plans',
    name: 'תוכניות בתכנון ועדות מחוזיות',
    description: 'תוכניות מ-MAVAT בוועדות המחוזיות (זום 11+)',
    visible: false,
  },
]

function MapView() {
  const mapContainerRef = useRef(null)
  const mapRef = useRef(null)
  const markerRef = useRef(null)
  const [mapReady, setMapReady] = useState(false)
  const [currentZoom, setCurrentZoom] = useState(DEFAULT_ZOOM)
  const [isLayersPanelOpen, setIsLayersPanelOpen] = useState(false)
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [isDbLayersOpen, setIsDbLayersOpen] = useState(false)
  const [layers, setLayers] = useState(INITIAL_LAYERS)
  const [plansFilter, setPlansFilter] = useState('all')
  const [plansDb, setPlansDb] = useState('plans_tanai_saf')
  const [dbLayers, setDbLayers] = useState(() => {
    try {
      const saved = localStorage.getItem('dbLayerStyles')
      return saved ? JSON.parse(saved) : {}
    } catch { return {} }
  })

  const closeAllPanels = () => {
    setIsLayersPanelOpen(false)
    setIsSearchOpen(false)
    setIsDbLayersOpen(false)
  }

  useEffect(() => {
    if (mapRef.current) return

    const map = L.map(mapContainerRef.current, {
      center: ISRAEL_CENTER,
      zoom: DEFAULT_ZOOM,
      minZoom: MIN_ZOOM,
      maxZoom: MAX_ZOOM,
      maxBounds: ISRAEL_BOUNDS,
      maxBoundsViscosity: 1.0,
      zoomControl: false,
    })

    L.tileLayer('https://tile.openstreetmap.de/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxNativeZoom: 19,
      maxZoom: 22,
    }).addTo(map)

    map.on('zoomend', () => setCurrentZoom(map.getZoom()))

    mapRef.current = map
    setMapReady(true)

    return () => {
      map.remove()
      mapRef.current = null
      setMapReady(false)
    }
  }, [])

  const handleToggleLayer = useCallback((layerId) => {
    setLayers(prev => prev.map(layer =>
      layer.id === layerId ? { ...layer, visible: !layer.visible } : layer
    ))
  }, [])

  const handleDbLayerChange = useCallback((dbId, markerStyle) => {
    setDbLayers(prev => {
      const next = { ...prev }
      if (markerStyle) {
        next[dbId] = markerStyle
      } else {
        delete next[dbId]
      }
      localStorage.setItem('dbLayerStyles', JSON.stringify(next))
      return next
    })
  }, [])

  const handleSearchResult = useCallback((result) => {
    const map = mapRef.current
    if (!map) return

    if (markerRef.current) {
      map.removeLayer(markerRef.current)
    }

    if (result.bounds) {
      map.flyToBounds([
        [result.bounds[0], result.bounds[1]],
        [result.bounds[2], result.bounds[3]],
      ], { padding: [50, 50], maxZoom: 18 })
    } else {
      map.flyTo([result.lat, result.lng], 17)
    }

    const label = result.parcel
      ? `גוש ${result.gush} חלקה ${result.parcel}`
      : result.gush
        ? `גוש ${result.gush}`
        : result.display_name || ''

    const marker = L.marker([result.lat, result.lng])
      .addTo(map)
      .bindPopup(label)
      .openPopup()

    markerRef.current = marker
  }, [])

  const handleZoomIn = () => mapRef.current?.zoomIn()
  const handleZoomOut = () => mapRef.current?.zoomOut()
  const handleLocate = () => mapRef.current?.locate({ setView: true, maxZoom: 16 })
  const handleResetView = () => mapRef.current?.flyTo(ISRAEL_CENTER, DEFAULT_ZOOM)

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Districts layer */}
      {mapReady && (
        <DistrictsLayer
          map={mapRef.current}
          visible={layers.find(l => l.id === 'districts')?.visible || false}
        />
      )}

      {/* Cadastre layers */}
      {mapReady && layers.filter(l => l.id !== 'districts' && l.id !== 'plans').map(layer => (
        <CadastreLayer
          key={layer.id}
          map={mapRef.current}
          layerId={layer.id}
          visible={layer.visible}
        />
      ))}

      {/* Plans layer */}
      {mapReady && (
        <PlansLayer
          map={mapRef.current}
          visible={layers.find(l => l.id === 'plans')?.visible || false}
          filter={plansFilter}
          db={plansDb}
        />
      )}

      {/* Plans filter panel - draggable */}
      {layers.find(l => l.id === 'plans')?.visible && (
        <PlanFilterPanel
          plansDb={plansDb}
          setPlansDb={setPlansDb}
          plansFilter={plansFilter}
          setPlansFilter={setPlansFilter}
        />
      )}

      {/* Database markers */}
      {mapReady && Object.entries(dbLayers).map(([dbId, markerStyle]) => (
        <DatabaseMarkers
          key={dbId + '-' + markerStyle.id}
          map={mapRef.current}
          dbId={dbId}
          markerStyle={markerStyle}
        />
      ))}

      <MapControls
        zoom={currentZoom}
        minZoom={MIN_ZOOM}
        maxZoom={MAX_ZOOM}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onLocate={handleLocate}
        onResetView={handleResetView}
        onToggleLayers={() => {
          const opening = !isLayersPanelOpen
          setIsLayersPanelOpen(opening)
          if (opening) { setIsSearchOpen(false); setIsDbLayersOpen(false) }
        }}
        isLayersPanelOpen={isLayersPanelOpen}
        onToggleSearch={() => {
          const opening = !isSearchOpen
          setIsSearchOpen(opening)
          if (opening) { setIsLayersPanelOpen(false); setIsDbLayersOpen(false) }
        }}
        isSearchOpen={isSearchOpen}
        onToggleDbLayers={() => {
          const opening = !isDbLayersOpen
          setIsDbLayersOpen(opening)
          if (opening) { setIsLayersPanelOpen(false); setIsSearchOpen(false) }
        }}
        isDbLayersOpen={isDbLayersOpen}
      />

      {isLayersPanelOpen && (
        <LayersPanel
          layers={layers}
          onToggleLayer={handleToggleLayer}
          onClose={() => setIsLayersPanelOpen(false)}
        />
      )}

      {isSearchOpen && (
        <SearchPanel
          onResult={handleSearchResult}
          onClose={() => setIsSearchOpen(false)}
        />
      )}

      {isDbLayersOpen && (
        <DatabaseLayersPanel
          activeLayers={dbLayers}
          onLayerChange={handleDbLayerChange}
          onClose={() => setIsDbLayersOpen(false)}
        />
      )}
    </div>
  )
}

export default MapView
