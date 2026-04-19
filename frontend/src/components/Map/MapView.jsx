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
import PlanDetailPanel from './PlanDetailPanel'
import ParkingLayer from './ParkingLayer'
import ParkingDetailPanel from './ParkingDetailPanel'

const PARKING_CITIES = [
  { key: 'tel_aviv',  name: 'תל אביב-יפו', defaultColor: '#2563eb' },
  { key: 'ramat_gan', name: 'רמת גן',       defaultColor: '#16a34a' },
  { key: 'holon',     name: 'חולון',        defaultColor: '#dc2626' },
  { key: 'herzliya',  name: 'הרצליה',       defaultColor: '#9333ea' },
  { key: 'givatayim', name: 'גבעתיים',      defaultColor: '#ea580c' },
  { key: 'bat_yam',   name: 'בת ים',        defaultColor: '#0891b2' },
]

const PRESET_COLORS = ['#2563eb','#16a34a','#dc2626','#9333ea','#ea580c','#0891b2','#be185d','#854d0e']

function ParkingFilterPanel({ cityStates, setCityStates, onClose }) {
  const [pos, setPos] = useState({ top: 80, left: 56 })
  const dragging = useRef(false)
  const startRef = useRef({})

  const onMouseDown = (e) => {
    if (['INPUT','SELECT','OPTION','LABEL'].includes(e.target.tagName)) return
    dragging.current = true
    startRef.current = { mx: e.clientX, my: e.clientY, ...pos }
    e.preventDefault()
  }

  useEffect(() => {
    const onMove = (e) => {
      if (!dragging.current) return
      setPos({ top: startRef.current.top + (e.clientY - startRef.current.my), left: startRef.current.left + (e.clientX - startRef.current.mx) })
    }
    const onUp = () => { dragging.current = false }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp) }
  }, [])

  const toggle = (key) => setCityStates(prev => ({ ...prev, [key]: { ...prev[key], active: !prev[key].active } }))
  const setColor = (key, color) => setCityStates(prev => ({ ...prev, [key]: { ...prev[key], color } }))

  return (
    <div onMouseDown={onMouseDown} style={{
      position: 'absolute', top: pos.top, left: pos.left, zIndex: 1000,
      background: 'white', borderRadius: 10, boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
      border: '1px solid #e5e7eb', padding: '10px 12px', width: 220,
      direction: 'rtl', cursor: 'grab', userSelect: 'none',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <span style={{ fontWeight: 700, fontSize: 13, color: '#1e3a5f' }}>מתקני חניה</span>
        <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 18, color: '#9ca3af', cursor: 'pointer', lineHeight: 1 }}>×</button>
      </div>
      {PARKING_CITIES.map(city => {
        const st = cityStates[city.key] || { active: false, color: city.defaultColor }
        return (
          <div key={city.key} style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 6 }}>
            <input type="checkbox" checked={st.active} onChange={() => toggle(city.key)}
              style={{ cursor: 'pointer', accentColor: st.color, width: 14, height: 14 }} />
            <span style={{ flex: 1, fontSize: 12, color: st.active ? '#111' : '#9ca3af', cursor: 'pointer' }}
              onClick={() => toggle(city.key)}>{city.name}</span>
            <div style={{ display: 'flex', gap: 3 }}>
              {PRESET_COLORS.slice(0, 4).map(c => (
                <div key={c} onClick={() => setColor(city.key, c)} style={{
                  width: 14, height: 14, borderRadius: '50%', background: c, cursor: 'pointer',
                  border: st.color === c ? '2px solid #111' : '1.5px solid #ccc',
                }} />
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

const DB_OPTIONS = [
  { value: 'plans_tanai_saf',      label: 'תנאי סף',         color: '#7c3aed', bg: '#f5f3ff' },
  { value: 'plans_milui_tnaim',    label: 'מילוי תנאים',     color: '#16a34a', bg: '#f0fdf4' },
  { value: 'plans_bdika_tichnunit',label: 'בדיקה תכנונית',   color: '#92400e', bg: '#fef3c7' },
]

function PlanFilterPanel({ plansDbSet, setPlansDbSet, plansFilter, setPlansFilter, onClose }) {
  const posRef = useRef(null)
  const [pos, setPos] = useState({ top: 80, left: 56 })
  const dragging = useRef(false)
  const startRef = useRef({})

  const toggleDb = (val) => {
    setPlansDbSet(prev =>
      prev.includes(val) ? prev.filter(v => v !== val) : [...prev, val]
    )
  }

  const onMouseDown = (e) => {
    if (['SELECT', 'OPTION', 'INPUT', 'LABEL'].includes(e.target.tagName)) return
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
        border: '2px solid #e5e7eb',
        padding: '10px 12px', minWidth: 175, direction: 'rtl',
        cursor: 'grab', userSelect: 'none',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8, borderBottom: '1px solid #e5e7eb', paddingBottom: 6 }}>
        <span style={{ fontWeight: 700, fontSize: 12, color: '#374151' }}>⠿ מאגר תוכניות</span>
        {onClose && <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 18, color: '#9ca3af', cursor: 'pointer', lineHeight: 1 }}>×</button>}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 5, marginBottom: 10 }}>
        {DB_OPTIONS.map(db => {
          const active = plansDbSet.includes(db.value)
          return (
            <label key={db.value} style={{ display: 'flex', alignItems: 'center', gap: 7, cursor: 'pointer' }}
              onClick={() => toggleDb(db.value)}>
              <span style={{
                width: 14, height: 14, borderRadius: 3, flexShrink: 0,
                border: `2px solid ${db.color}`,
                background: active ? db.color : 'white',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {active && <span style={{ color: 'white', fontSize: 10, lineHeight: 1 }}>✓</span>}
              </span>
              <span style={{
                fontSize: 11, fontWeight: 600, color: active ? db.color : '#6b7280',
              }}>
                {db.label}
              </span>
              <span style={{
                marginRight: 'auto', width: 10, height: 3, borderRadius: 2,
                background: db.color, opacity: active ? 1 : 0.3,
              }} />
            </label>
          )
        })}
      </div>
      <div style={{ fontWeight: 600, fontSize: 10, color: '#9ca3af', marginBottom: 4 }}>סינון</div>
      <select
        value={plansFilter}
        onChange={e => setPlansFilter(e.target.value)}
        style={{
          width: '100%', padding: '3px 6px', border: '1px solid #d1d5db',
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
  {
    id: 'parking',
    name: 'מתקני חניה',
    description: 'בניינים עם מתקני חניה מפרוטוקולי ועדות',
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
  const [plansDbSet, setPlansDbSet] = useState(['plans_tanai_saf'])
  const [plansPanelOpen, setPlansPanelOpen] = useState(true)
  const [planPopup, setPlanPopup] = useState(null)
  const [parkingPanelOpen, setParkingPanelOpen] = useState(true)
  const [parkingDetail, setParkingDetail] = useState(null)
  const [parkingCities, setParkingCities] = useState(() =>
    Object.fromEntries(PARKING_CITIES.map(c => [c.key, { active: false, color: c.defaultColor }]))
  )
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
    if (layerId === 'plans') setPlansPanelOpen(true)
    if (layerId === 'parking') setParkingPanelOpen(true)
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
      {mapReady && layers.filter(l => l.id !== 'districts' && l.id !== 'plans' && l.id !== 'parking').map(layer => (
        <CadastreLayer
          key={layer.id}
          map={mapRef.current}
          layerId={layer.id}
          visible={layer.visible}
        />
      ))}

      {/* Plans layers - one per active DB */}
      {mapReady && DB_OPTIONS.filter(d => plansDbSet.includes(d.value)).map(d => (
        <PlansLayer
          key={d.value}
          map={mapRef.current}
          visible={layers.find(l => l.id === 'plans')?.visible || false}
          filter={plansFilter}
          db={d.value}
          dbColor={d.color}
          onPlanClick={setPlanPopup}
        />
      ))}

      {/* Plans filter panel - draggable */}
      {layers.find(l => l.id === 'plans')?.visible && plansPanelOpen && (
        <PlanFilterPanel
          plansDbSet={plansDbSet}
          setPlansDbSet={setPlansDbSet}
          plansFilter={plansFilter}
          setPlansFilter={setPlansFilter}
          onClose={() => setPlansPanelOpen(false)}
        />
      )}

      {/* Plan detail popup - draggable React panel */}
      {planPopup && (
        <PlanDetailPanel
          data={planPopup}
          onClose={() => setPlanPopup(null)}
        />
      )}

      {/* Parking layers - one per active city */}
      {mapReady && PARKING_CITIES.map(city => {
        const st = parkingCities[city.key] || { active: false, color: city.defaultColor }
        return (
          <ParkingLayer
            key={city.key}
            map={mapRef.current}
            visible={layers.find(l => l.id === 'parking')?.visible && st.active}
            cityKey={city.key}
            color={st.color}
            onBuildingClick={setParkingDetail}
          />
        )
      })}

      {/* Parking building detail panel */}
      {parkingDetail && (
        <ParkingDetailPanel
          data={parkingDetail}
          onClose={() => setParkingDetail(null)}
        />
      )}

      {/* Parking filter panel */}
      {layers.find(l => l.id === 'parking')?.visible && parkingPanelOpen && (
        <ParkingFilterPanel
          cityStates={parkingCities}
          setCityStates={setParkingCities}
          onClose={() => setParkingPanelOpen(false)}
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
