import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

function ParkingDevicesPage() {
  const navigate = useNavigate()
  const [buildings, setBuildings] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [yearFilter, setYearFilter] = useState('')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [resultsResp, statsResp] = await Promise.all([
          axios.get('/api/parking-devices/results'),
          axios.get('/api/parking-devices/stats'),
        ])
        setBuildings(resultsResp.data)
        setStats(statsResp.data)
      } catch (err) {
        console.error(err)
      }
      setLoading(false)
    }
    fetchData()
  }, [])

  const extractYear = (date) => {
    if (!date || !date.includes('/')) return ''
    const parts = date.split('/')
    return parts.length >= 3 ? parts[2] : ''
  }

  const deviceTypes = stats ? Object.keys(stats.by_device_type).sort() : []
  const years = stats ? Object.keys(stats.by_year).sort() : []

  const filtered = buildings.filter(b => {
    const text = `${b.address || ''} ${b.gush || ''} ${b.helka || ''} ${b.description || ''} ${b.device_type || ''}`.toLowerCase()
    if (filter && !text.includes(filter.toLowerCase())) return false
    if (typeFilter && (b.device_type || '') !== typeFilter) return false
    if (yearFilter && extractYear(b.date) !== yearFilter) return false
    return true
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-blue-50">
      <header className="bg-blue-900 shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-6 flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="text-base text-blue-200 hover:text-white font-medium"
          >
            &larr; דף הבית
          </button>
          <div className="border-r border-blue-700 h-6" />
          <div>
            <h1 className="text-2xl font-bold text-white">מתקני חניה בבניינים</h1>
            <p className="text-base text-blue-200">בניינים עם מתקני חניה מכניים - מתוך פרוטוקולי ועדות תכנון</p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-xl shadow-sm border border-sky-100 p-4 text-center">
              <div className="text-3xl font-bold text-blue-900">{stats.total_buildings}</div>
              <div className="text-sm text-blue-800/60">בניינים עם מתקני חניה</div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-sky-100 p-4 text-center">
              <div className="text-3xl font-bold text-green-700">{deviceTypes.length}</div>
              <div className="text-sm text-blue-800/60">סוגי מתקנים</div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-sky-100 p-4 text-center">
              <div className="text-3xl font-bold text-amber-600">{years.length}</div>
              <div className="text-sm text-blue-800/60">שנים</div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-sky-100 p-4 text-center">
              <div className="text-3xl font-bold text-purple-700">
                {buildings.reduce((sum, b) => sum + (parseInt(b.parking_count) || 0), 0)}
              </div>
              <div className="text-sm text-blue-800/60">מקומות חניה במתקנים</div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-4">
          <input
            type="text"
            placeholder="חיפוש לפי כתובת, גוש, תיאור..."
            value={filter}
            onChange={e => setFilter(e.target.value)}
            className="flex-1 min-w-64 px-4 py-2 border border-sky-200 rounded-lg text-base text-blue-900
                       focus:outline-none focus:ring-2 focus:ring-sky-400"
          />
          <select
            value={typeFilter}
            onChange={e => setTypeFilter(e.target.value)}
            className="px-3 py-2 border border-sky-200 rounded-lg text-base bg-white
                       focus:outline-none focus:ring-2 focus:ring-sky-400"
          >
            <option value="">כל סוגי המתקנים</option>
            {deviceTypes.map(dt => (
              <option key={dt} value={dt}>{dt} ({stats.by_device_type[dt]})</option>
            ))}
          </select>
          <select
            value={yearFilter}
            onChange={e => setYearFilter(e.target.value)}
            className="px-3 py-2 border border-sky-200 rounded-lg text-base bg-white
                       focus:outline-none focus:ring-2 focus:ring-sky-400"
          >
            <option value="">כל השנים</option>
            {years.map(y => (
              <option key={y} value={y}>{y} ({stats.by_year[y]})</option>
            ))}
          </select>
        </div>

        {/* Results Table */}
        <div className="bg-white rounded-2xl shadow-md border border-sky-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-sky-50">
                <tr>
                  <th className="px-3 py-3 text-right font-bold text-blue-900">#</th>
                  <th className="px-3 py-3 text-right font-bold text-blue-900">כתובת</th>
                  <th className="px-3 py-3 text-right font-bold text-blue-900">גוש</th>
                  <th className="px-3 py-3 text-right font-bold text-blue-900">חלקה</th>
                  <th className="px-3 py-3 text-right font-bold text-blue-900">סוג מתקן</th>
                  <th className="px-3 py-3 text-right font-bold text-blue-900">חניות</th>
                  <th className="px-3 py-3 text-right font-bold text-blue-900">תאריך</th>
                  <th className="px-3 py-3 text-right font-bold text-blue-900 max-w-md">תיאור</th>
                  <th className="px-3 py-3 text-right font-bold text-blue-900">פרוטוקול</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-blue-800/50">טוען...</td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-blue-800/50">לא נמצאו תוצאות</td>
                  </tr>
                ) : (
                  filtered.map((b, i) => (
                    <tr key={i} className="border-t border-sky-50 hover:bg-sky-50/50">
                      <td className="px-3 py-2 text-blue-800/50">{i + 1}</td>
                      <td className="px-3 py-2 text-blue-900 font-medium">{b.address || '-'}</td>
                      <td className="px-3 py-2 text-blue-900">{b.gush || '-'}</td>
                      <td className="px-3 py-2 text-blue-900">{b.helka || '-'}</td>
                      <td className="px-3 py-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium
                          ${b.device_type?.includes('רובוטי') ? 'bg-purple-50 text-purple-700' :
                            b.device_type?.includes('אוטומטי') ? 'bg-green-50 text-green-700' :
                            b.device_type?.includes('מכפיל') ? 'bg-amber-50 text-amber-700' :
                            'bg-sky-50 text-sky-700'}`}>
                          {b.device_type || '-'}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-blue-900 font-medium">{b.parking_count || '-'}</td>
                      <td className="px-3 py-2 text-blue-800/70 text-xs">{b.date || '-'}</td>
                      <td className="px-3 py-2 text-blue-800 text-xs max-w-md">
                        {b.description ? (
                          <span title={b.description}>{b.description.substring(0, 100)}{b.description.length > 100 ? '...' : ''}</span>
                        ) : '-'}
                      </td>
                      <td className="px-3 py-2">
                        {b.source_file ? (
                          <a
                            href={`/api/parking-devices/pdf/${encodeURIComponent(b.source_file)}${b.page_number ? `#page=${b.page_number}` : ''}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sky-600 hover:text-sky-800 underline text-xs whitespace-nowrap"
                          >
                            {b.page_number ? `עמ' ${b.page_number}` : 'צפה'}
                          </a>
                        ) : '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="px-6 py-3 border-t border-sky-100 text-sm text-blue-800/50">
            מציג {filtered.length} מתוך {buildings.length} בניינים
          </div>
        </div>
      </main>
    </div>
  )
}

export default ParkingDevicesPage
