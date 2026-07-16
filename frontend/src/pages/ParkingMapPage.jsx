import { useState, useEffect, useRef, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import L from 'leaflet'
import * as XLSX from 'xlsx'
import QRCode from 'qrcode'
import 'leaflet/dist/leaflet.css'

const ISRAEL_CENTER = [31.95, 34.85]
const DEFAULT_ZOOM = 11

// Plain teardrop pin (un-routed buildings)
function pinIcon(color = '#0ea5e9') {
  return L.divIcon({
    html: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="28" viewBox="0 0 22 30">
      <path d="M11 0C5.477 0 1 4.477 1 10c0 7.5 10 20 10 20S21 17.5 21 10C21 4.477 16.523 0 11 0z"
            fill="${color}" stroke="white" stroke-width="1.5"/>
      <circle cx="11" cy="10" r="4" fill="white" opacity="0.9"/>
    </svg>`,
    className: '', iconSize: [20, 28], iconAnchor: [10, 28],
  })
}

// Numbered circle marker for an ordered route stop
function numberIcon(n, color = '#1e3a8a') {
  const size = n >= 100 ? 30 : 26
  return L.divIcon({
    html: `<div style="background:${color};color:#fff;width:${size}px;height:${size}px;border-radius:50%;
      display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;
      border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4)">${n}</div>`,
    className: '', iconSize: [size, size], iconAnchor: [size / 2, size / 2],
  })
}

function startIcon() {
  return L.divIcon({
    html: `<div style="background:#16a34a;color:#fff;width:30px;height:30px;border-radius:50%;
      display:flex;align-items:center;justify-content:center;font-size:14px;
      border:3px solid #fff;box-shadow:0 1px 5px rgba(0,0,0,.5)">★</div>`,
    className: '', iconSize: [30, 30], iconAnchor: [15, 15],
  })
}

const extractYear = (date) => {
  if (!date || !date.includes('/')) return ''
  const parts = date.split('/')
  return parts.length >= 3 ? parts[2] : ''
}

// Squared planar distance (good enough for ordering within a city)
function dist2(a, b) {
  const latRad = (a.lat * Math.PI) / 180
  const dx = (b.lng - a.lng) * Math.cos(latRad)
  const dy = b.lat - a.lat
  return dx * dx + dy * dy
}

// Google Maps consumer links allow ~10 stops; split long routes into segments
// that overlap by one stop so the courier walks a continuous path.
const MAX_STOPS_PER_LINK = 10

function chunkRoute(stops, maxPer = MAX_STOPS_PER_LINK) {
  if (stops.length <= maxPer) return [{ stops, from: 0, to: stops.length - 1 }]
  const chunks = []
  let i = 0
  while (i < stops.length) {
    const end = Math.min(i + maxPer, stops.length)
    chunks.push({ stops: stops.slice(i, end), from: i, to: end - 1 })
    if (end === stops.length) break
    i = end - 1 // overlap by one stop for continuity
  }
  return chunks
}

function googleMapsUrl(stops) {
  const pts = stops.map(s => `${s.lat},${s.lng}`)
  const origin = pts[0]
  const destination = pts[pts.length - 1]
  const waypoints = pts.slice(1, -1).join('|')
  let url = `https://www.google.com/maps/dir/?api=1&travelmode=walking&origin=${origin}&destination=${destination}`
  if (waypoints) url += `&waypoints=${encodeURIComponent(waypoints)}`
  return url
}

// Greedy nearest-neighbour ordering from a start point
function nearestNeighbourRoute(points, start) {
  const remaining = points.slice()
  const route = []
  let current = start
  while (remaining.length) {
    let bestIdx = 0
    let bestD = Infinity
    for (let i = 0; i < remaining.length; i++) {
      const d = dist2(current, remaining[i])
      if (d < bestD) { bestD = d; bestIdx = i }
    }
    const next = remaining.splice(bestIdx, 1)[0]
    route.push(next)
    current = next
  }
  return route
}

function ParkingMapPage() {
  const navigate = useNavigate()
  const mapRef = useRef(null)
  const mapContainerRef = useRef(null)
  const markerLayerRef = useRef(null)
  const routeLayerRef = useRef(null)
  const startMarkerRef = useRef(null)

  const [cities, setCities] = useState([])
  const [selectedCity, setSelectedCity] = useState('')
  const [buildings, setBuildings] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [yearFrom, setYearFrom] = useState('')
  const [yearTo, setYearTo] = useState('')
  const [search, setSearch] = useState('')

  const [route, setRoute] = useState(null)        // ordered array of buildings
  const [startPoint, setStartPoint] = useState(null)
  const [settingStart, setSettingStart] = useState(false)
  const [editorOpen, setEditorOpen] = useState(false)
  const [gmapsSegments, setGmapsSegments] = useState([]) // [{label, url, dataUrl, from, to}]

  const cityName = cities.find(c => c.key === selectedCity)?.name || ''

  // --- init map once ---
  useEffect(() => {
    if (mapRef.current || !mapContainerRef.current) return
    const map = L.map(mapContainerRef.current, {
      center: ISRAEL_CENTER, zoom: DEFAULT_ZOOM, zoomControl: true,
    })
    L.tileLayer('https://tile.openstreetmap.de/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors', maxZoom: 19,
    }).addTo(map)
    markerLayerRef.current = L.layerGroup().addTo(map)
    routeLayerRef.current = L.layerGroup().addTo(map)
    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, [])

  // --- map click sets the start point when in "set start" mode ---
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const handler = (e) => {
      if (!settingStart) return
      setStartPoint({ lat: e.latlng.lat, lng: e.latlng.lng })
      setSettingStart(false)
    }
    map.on('click', handler)
    return () => map.off('click', handler)
  }, [settingStart])

  // --- load cities ---
  useEffect(() => {
    axios.get('/api/parking-devices/cities').then(r => setCities(r.data)).catch(() => {})
  }, [])

  // --- load buildings + stats on city change ---
  useEffect(() => {
    if (!selectedCity) { setBuildings([]); setStats(null); return }
    setLoading(true); setRoute(null); setStartPoint(null)
    const params = { city: selectedCity }
    Promise.all([
      axios.get('/api/parking-devices/results', { params }),
      axios.get('/api/parking-devices/stats', { params }),
    ]).then(([res, st]) => { setBuildings(res.data); setStats(st.data) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [selectedCity])

  const years = stats ? Object.keys(stats.by_year).sort() : []

  // --- filtered buildings that have coordinates (de-duplicated by address) ---
  const filtered = useMemo(() => {
    const seen = new Set()
    return buildings.filter(b => {
      if (!b.lat || !b.lng) return false
      const yr = extractYear(b.dates || b.date)
      if (yearFrom && yr && yr < yearFrom) return false
      if (yearTo && yr && yr > yearTo) return false
      if (search) {
        const text = `${b.address || ''} ${b.gush || ''} ${b.helka || ''} ${b.description || ''}`.toLowerCase()
        if (!text.includes(search.toLowerCase())) return false
      }
      const key = (b.address || '').trim()
      if (key && seen.has(key)) return false
      if (key) seen.add(key)
      return true
    })
  }, [buildings, yearFrom, yearTo, search])

  const noCoords = useMemo(
    () => buildings.filter(b => !b.lat || !b.lng), [buildings]
  )
  const noCoordsCount = noCoords.length

  // Save an edited address: re-geocode on the server and update local state.
  const saveBuilding = async (b, newAddress) => {
    const resp = await axios.post('/api/parking-devices/update', {
      city_key: selectedCity,
      file: b._file,
      row: b._row,
      address: newAddress,
    })
    const u = resp.data.building
    setBuildings(prev => prev.map(x =>
      (x._file === b._file && x._row === b._row)
        ? { ...x, address: u.address, lat: u.lat, lng: u.lng }
        : x
    ))
    return resp.data.geocoded
  }

  // --- draw markers / route on the map ---
  useEffect(() => {
    const map = mapRef.current
    const layer = markerLayerRef.current
    const routeLayer = routeLayerRef.current
    if (!map || !layer || !routeLayer) return
    layer.clearLayers()
    routeLayer.clearLayers()

    const list = route || filtered
    list.forEach((b, i) => {
      const icon = route ? numberIcon(i + 1) : pinIcon()
      const m = L.marker([b.lat, b.lng], { icon })
      m.bindPopup(
        `<div style="direction:rtl;text-align:right;min-width:160px">
          ${route ? `<b>עצירה ${i + 1}</b><br/>` : ''}
          <b>${b.address || 'ללא כתובת'}</b><br/>
          ${b.gush ? `גוש ${b.gush} חלקה ${b.helka || ''}<br/>` : ''}
          ${b.device_types || b.device_type || ''} ${b.parking_count ? `· ${b.parking_count} חניות` : ''}
        </div>`
      )
      layer.addLayer(m)
    })

    if (route && route.length) {
      const pts = [...(startPoint ? [startPoint] : []), ...route].map(b => [b.lat, b.lng])
      routeLayer.addLayer(L.polyline(pts, { color: '#1e3a8a', weight: 3, opacity: 0.7, dashArray: '6 6' }))
    }
    if (startPoint) startMarkerRef.current = L.marker([startPoint.lat, startPoint.lng], { icon: startIcon() }).addTo(routeLayer)

    // fit bounds to what's shown
    if (list.length) {
      const b = L.latLngBounds(list.map(x => [x.lat, x.lng]))
      if (startPoint) b.extend([startPoint.lat, startPoint.lng])
      map.fitBounds(b.pad(0.15))
    }
  }, [filtered, route, startPoint])

  // Build Google-Maps navigation segments (+ QR codes) for the courier
  useEffect(() => {
    if (!route || !route.length) { setGmapsSegments([]); return }
    const allStops = startPoint
      ? [{ lat: startPoint.lat, lng: startPoint.lng }, ...route]
      : route
    const chunks = chunkRoute(allStops)
    let cancelled = false
    Promise.all(chunks.map(async (c, i) => {
      const url = googleMapsUrl(c.stops)
      const dataUrl = await QRCode.toDataURL(url, { margin: 1, width: 220 })
      // stop numbers shown to the user (1-based, ignoring the synthetic start point)
      const offset = startPoint ? 0 : 1
      const fromStop = Math.max(1, c.from + offset)
      const toStop = c.to + offset
      const label = chunks.length === 1 ? 'כל המסלול' : `מקטע ${i + 1} · עצירות ${fromStop}–${toStop}`
      return { label, url, dataUrl, from: fromStop, to: toStop }
    })).then(segs => { if (!cancelled) setGmapsSegments(segs) })
    return () => { cancelled = true }
  }, [route, startPoint])

  const handlePlanRoute = () => {
    if (!filtered.length) return
    const start = startPoint || filtered.reduce((a, b) => (b.lng < a.lng ? b : a), filtered[0]) // west-most default
    setStartPoint(start)
    setRoute(nearestNeighbourRoute(filtered, start))
  }

  const handleClearRoute = () => { setRoute(null) }

  const handleExportExcel = () => {
    const list = route || filtered
    const rows = list.map((b, i) => ({
      'סידורי': i + 1,
      'כתובת': b.address || '',
      'גוש': b.gush || '',
      'חלקה': b.helka || '',
    }))
    const ws = XLSX.utils.json_to_sheet(rows)
    ws['!cols'] = [{ wch: 7 }, { wch: 38 }, { wch: 10 }, { wch: 10 }]
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'מסלול')
    XLSX.writeFile(wb, `מסלול_מתקני_חניה_${cityName || 'עיר'}.xlsx`)
  }

  const handlePrint = () => window.print()

  const list = route || filtered

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-blue-50 flex flex-col">
      {/* print-only styles */}
      <style>{`
        #print-area { display: none; }
        @media print {
          body * { visibility: hidden; }
          #print-area, #print-area * { visibility: visible; }
          #print-area { display: block; position: absolute; inset: 0; width: 100%; padding: 24px; }
          @page { margin: 12mm; }
        }
      `}</style>

      <header className="bg-blue-900 shadow-lg print:hidden">
        <div className="max-w-full mx-auto px-6 py-4 flex items-center gap-4">
          <button onClick={() => navigate('/')} className="text-base text-blue-200 hover:text-white font-medium">
            &larr; דף הבית
          </button>
          <div className="border-r border-blue-700 h-6" />
          <div>
            <h1 className="text-2xl font-bold text-white">מפה מתקני חניה לפי עיר</h1>
            <p className="text-sm text-blue-200">בחירת עיר, סינון לפי שנים, ותכנון מסלול חלוקת פליירים</p>
          </div>
        </div>
      </header>

      {/* Toolbar */}
      <div className="bg-white border-b border-sky-100 px-6 py-3 flex flex-wrap items-center gap-3 print:hidden">
        <select
          value={selectedCity}
          onChange={e => setSelectedCity(e.target.value)}
          className="px-3 py-2 border border-sky-200 rounded-lg text-base bg-white font-medium text-blue-900 focus:outline-none focus:ring-2 focus:ring-sky-400"
        >
          <option value="">בחר עיר…</option>
          {cities.map(c => <option key={c.key} value={c.key}>{c.name} ({c.count})</option>)}
        </select>

        <select value={yearFrom} onChange={e => setYearFrom(e.target.value)}
          className="px-3 py-2 border border-sky-200 rounded-lg text-base bg-white focus:outline-none focus:ring-2 focus:ring-sky-400">
          <option value="">משנה</option>
          {years.map(y => <option key={y} value={y}>{y}</option>)}
        </select>
        <select value={yearTo} onChange={e => setYearTo(e.target.value)}
          className="px-3 py-2 border border-sky-200 rounded-lg text-base bg-white focus:outline-none focus:ring-2 focus:ring-sky-400">
          <option value="">עד שנה</option>
          {years.map(y => <option key={y} value={y}>{y}</option>)}
        </select>

        <input type="text" placeholder="חיפוש כתובת/גוש…" value={search} onChange={e => setSearch(e.target.value)}
          className="px-3 py-2 border border-sky-200 rounded-lg text-base text-blue-900 focus:outline-none focus:ring-2 focus:ring-sky-400 min-w-48" />

        <div className="flex-1" />

        <span className="text-sm text-blue-800/70 font-medium">{filtered.length} בניינים על המפה</span>
        {noCoordsCount > 0 && (
          <button onClick={() => setEditorOpen(true)}
            className="px-3 py-2 rounded-lg text-sm font-medium bg-amber-50 text-amber-700 border border-amber-300 hover:bg-amber-100">
            ✏ ערוך {noCoordsCount} ללא מיקום
          </button>
        )}

        <button onClick={() => setSettingStart(s => !s)} disabled={!filtered.length}
          className={`px-3 py-2 rounded-lg text-sm font-medium border transition disabled:opacity-40
            ${settingStart ? 'bg-green-600 text-white border-green-600' : 'bg-white text-green-700 border-green-300 hover:bg-green-50'}`}>
          {settingStart ? 'לחץ על המפה לקביעת התחלה…' : '★ נקודת התחלה'}
        </button>
        <button onClick={handlePlanRoute} disabled={!filtered.length}
          className="px-4 py-2 rounded-lg text-sm font-bold bg-blue-900 text-white hover:bg-blue-800 disabled:opacity-40">
          תכנן מסלול
        </button>
        {route && (
          <button onClick={handleClearRoute}
            className="px-3 py-2 rounded-lg text-sm font-medium bg-white text-blue-800 border border-sky-200 hover:bg-sky-50">
            נקה מסלול
          </button>
        )}
        <button onClick={handleExportExcel} disabled={!list.length}
          className="px-3 py-2 rounded-lg text-sm font-medium bg-white text-green-700 border border-green-300 hover:bg-green-50 disabled:opacity-40">
          ⬇ אקסל
        </button>
        <button onClick={handlePrint} disabled={!list.length}
          className="px-3 py-2 rounded-lg text-sm font-medium bg-white text-blue-800 border border-sky-200 hover:bg-sky-50 disabled:opacity-40">
          🖨 הדפס תוכנית
        </button>
      </div>

      {/* Map + side list */}
      <div className="flex-1 flex min-h-0 print:hidden">
        <div ref={mapContainerRef} className="flex-1 min-h-[400px]" style={{ height: 'calc(100vh - 140px)' }} />

        {route && (
          <aside className="w-80 bg-white border-r border-sky-100 overflow-y-auto" style={{ height: 'calc(100vh - 140px)' }}>
            <div className="px-4 py-3 border-b border-sky-100 sticky top-0 bg-white z-10">
              <div className="font-bold text-blue-900">מסלול — {route.length} עצירות</div>
              <div className="text-xs text-blue-800/60">{cityName}</div>
            </div>

            {/* Google Maps navigation for the courier */}
            {gmapsSegments.length > 0 && (
              <div className="px-4 py-3 border-b border-sky-100 bg-sky-50/40">
                <div className="text-sm font-bold text-blue-900 mb-2">📍 ניווט בגוגל מפות</div>
                <div className="space-y-1.5">
                  {gmapsSegments.map((s, i) => (
                    <a key={i} href={s.url} target="_blank" rel="noopener noreferrer"
                      className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-white border border-sky-200 hover:bg-sky-50 text-sm text-blue-900">
                      <span>{s.label}</span>
                      <span className="text-sky-600">פתח ›</span>
                    </a>
                  ))}
                </div>
                {gmapsSegments.length > 1 && (
                  <p className="text-xs text-blue-800/50 mt-2">המסלול חולק למקטעים (מגבלת גוגל ~10 עצירות לקישור). קודי QR לסריקה זמינים בהדפסה.</p>
                )}
              </div>
            )}

            <ol className="divide-y divide-sky-50">
              {route.map((b, i) => (
                <li key={i} className="px-4 py-2 flex gap-3 items-start hover:bg-sky-50/50">
                  <span className="shrink-0 w-6 h-6 rounded-full bg-blue-900 text-white text-xs font-bold flex items-center justify-center">{i + 1}</span>
                  <div className="text-sm">
                    <div className="text-blue-900 font-medium">{b.address || 'ללא כתובת'}</div>
                    <div className="text-xs text-blue-800/60">{b.gush ? `גוש ${b.gush} חלקה ${b.helka || ''}` : ''}</div>
                  </div>
                </li>
              ))}
            </ol>
          </aside>
        )}
      </div>

      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/40 print:hidden">
          <div className="px-4 py-2 bg-blue-900 text-white rounded-lg">טוען…</div>
        </div>
      )}

      {/* Printable plan */}
      <div id="print-area" dir="rtl">
        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>
          מסלול חלוקת פליירים — מתקני חניה
        </h1>
        <div style={{ fontSize: 14, marginBottom: 2 }}>עיר: {cityName || '—'}</div>
        <div style={{ fontSize: 13, color: '#444', marginBottom: 2 }}>
          {(yearFrom || yearTo) ? `שנים: ${yearFrom || '…'}–${yearTo || '…'}` : 'כל השנים'} · סה״כ {list.length} עצירות
        </div>
        <div style={{ fontSize: 12, color: '#777', marginBottom: 12 }}>הופק בתאריך {new Date().toLocaleDateString('he-IL')}</div>

        {gmapsSegments.length > 0 && (
          <div style={{ marginBottom: 16, padding: 12, border: '1px solid #cbd5e1', borderRadius: 8 }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>📍 ניווט בגוגל מפות — סרוק עם הטלפון</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
              {gmapsSegments.map((s, i) => (
                <div key={i} style={{ textAlign: 'center', width: 130 }}>
                  <img src={s.dataUrl} alt={s.label} style={{ width: 120, height: 120 }} />
                  <div style={{ fontSize: 11, marginTop: 2 }}>{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: '#f0f6ff' }}>
              <th style={{ border: '1px solid #cbd5e1', padding: '6px 8px', textAlign: 'right', width: 50 }}>#</th>
              <th style={{ border: '1px solid #cbd5e1', padding: '6px 8px', textAlign: 'right' }}>כתובת</th>
              <th style={{ border: '1px solid #cbd5e1', padding: '6px 8px', textAlign: 'right', width: 120 }}>גוש / חלקה</th>
              <th style={{ border: '1px solid #cbd5e1', padding: '6px 8px', textAlign: 'center', width: 50 }}>✓</th>
            </tr>
          </thead>
          <tbody>
            {list.map((b, i) => (
              <tr key={i}>
                <td style={{ border: '1px solid #cbd5e1', padding: '6px 8px', fontWeight: 700 }}>{i + 1}</td>
                <td style={{ border: '1px solid #cbd5e1', padding: '6px 8px' }}>{b.address || '—'}</td>
                <td style={{ border: '1px solid #cbd5e1', padding: '6px 8px' }}>{b.gush ? `${b.gush} / ${b.helka || ''}` : '—'}</td>
                <td style={{ border: '1px solid #cbd5e1', padding: '6px 8px' }}></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editorOpen && (
        <NoLocationEditor
          list={noCoords}
          cityName={cityName}
          onSave={saveBuilding}
          onClose={() => setEditorOpen(false)}
        />
      )}
    </div>
  )
}

// --- Editor for buildings missing coordinates ---
function NoLocationEditor({ list, cityName, onSave, onClose }) {
  const keyOf = (b) => `${b._file}#${b._row}`
  const [drafts, setDrafts] = useState({})
  const [status, setStatus] = useState({}) // key -> 'saving' | 'fail' | 'error'

  const handleSave = async (b) => {
    const k = keyOf(b)
    const addr = (drafts[k] ?? b.address ?? '').trim()
    if (!addr) return
    setStatus(s => ({ ...s, [k]: 'saving' }))
    try {
      const geocoded = await onSave(b, addr)
      // on success the row drops out of `list`; if not geocoded, flag it
      setStatus(s => ({ ...s, [k]: geocoded ? undefined : 'fail' }))
    } catch {
      setStatus(s => ({ ...s, [k]: 'error' }))
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-[1000] print:hidden" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col" dir="rtl" onClick={e => e.stopPropagation()}>
        <div className="px-6 py-4 border-b border-sky-100 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-blue-900">בניינים ללא מיקום — {cityName}</h2>
            <p className="text-sm text-blue-800/60">תקן את הכתובת ולחץ "מצא מיקום". בהצלחה הבניין יופיע על המפה.</p>
          </div>
          <button onClick={onClose} className="text-blue-800/50 hover:text-blue-900 text-2xl leading-none">&times;</button>
        </div>

        <div className="overflow-y-auto p-4">
          {list.length === 0 ? (
            <div className="text-center text-green-700 py-10 font-medium">🎉 כל הבניינים ממוקמים על המפה!</div>
          ) : (
            <ul className="space-y-2">
              {list.map((b) => {
                const k = keyOf(b)
                const st = status[k]
                return (
                  <li key={k} className="flex items-center gap-2 bg-sky-50/50 rounded-lg p-2">
                    <div className="text-xs text-blue-800/50 w-24 shrink-0">
                      {b.gush ? `גוש ${b.gush}` : '—'}<br />{b.helka ? `חלקה ${b.helka}` : ''}
                    </div>
                    <input
                      type="text"
                      defaultValue={b.address || ''}
                      onChange={e => setDrafts(d => ({ ...d, [k]: e.target.value }))}
                      className="flex-1 px-3 py-2 border border-sky-200 rounded-lg text-sm text-blue-900 focus:outline-none focus:ring-2 focus:ring-sky-400"
                    />
                    {st === 'fail' && <span className="text-xs text-red-600 shrink-0">לא נמצא</span>}
                    {st === 'error' && <span className="text-xs text-red-600 shrink-0">שגיאה</span>}
                    <button
                      onClick={() => handleSave(b)}
                      disabled={st === 'saving'}
                      className="px-3 py-2 rounded-lg text-sm font-medium bg-blue-900 text-white hover:bg-blue-800 disabled:opacity-50 shrink-0"
                    >
                      {st === 'saving' ? '...' : 'מצא מיקום'}
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </div>

        <div className="px-6 py-3 border-t border-sky-100 text-sm text-blue-800/60">
          נותרו {list.length} בניינים ללא מיקום
        </div>
      </div>
    </div>
  )
}

export default ParkingMapPage
