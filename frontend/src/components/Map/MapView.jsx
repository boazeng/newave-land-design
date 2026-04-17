import { useEffect, useRef, useState, useCallback } from 'react'
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
    name: 'תכניות תכנון',
    description: 'תכניות בבדיקת תנאי סף - מעל 10,000 מ"ר (זום 11+)',
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
        />
      )}

      {/* Plans filter panel */}
      {layers.find(l => l.id === 'plans')?.visible && (
        <div className="absolute top-20 left-14 z-[1000] bg-white rounded-xl shadow-lg border border-purple-200 p-3 text-sm" style={{direction:'rtl'}}>
          <div className="font-bold text-purple-900 mb-2 text-xs">סינון תכניות</div>
          <select
            value={plansFilter}
            onChange={e => setPlansFilter(e.target.value)}
            className="w-full px-2 py-1.5 border border-purple-200 rounded-lg text-xs bg-white focus:ring-1 focus:ring-purple-400"
          >
            <option value="all">הכל</option>
            <option value="not_reviewed">לא נבדק</option>
            <option value="relevant">רלוונטי</option>
            <option value="high">עדיפות גבוהה</option>
            <option value="medium">עדיפות בינונית</option>
            <option value="low">עדיפות נמוכה</option>
          </select>
        </div>
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
