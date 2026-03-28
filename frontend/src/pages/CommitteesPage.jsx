import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

function CommitteesPage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('local')
  const [localData, setLocalData] = useState([])
  const [districtData, setDistrictData] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [scraperCommittees, setScraperCommittees] = useState([])
  const [runningTasks, setRunningTasks] = useState({}) // { committeeName: { taskId, status, result } }
  const [yearsSelection, setYearsSelection] = useState({}) // { committeeName: number }
  const pollTimers = useRef({})

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [local, district, scrapers] = await Promise.all([
          axios.get('/api/committees/local'),
          axios.get('/api/committees/district'),
          axios.get('/api/committees/scrapers'),
        ])
        setLocalData(local.data)
        setDistrictData(district.data)
        setScraperCommittees(scrapers.data)
      } catch {}
      setLoading(false)
    }
    fetchData()
    return () => {
      Object.values(pollTimers.current).forEach(clearInterval)
    }
  }, [])

  const hasScraper = (name) => scraperCommittees.includes(name)

  const getYears = (name) => yearsSelection[name] || 5

  const setYears = (name, val) => {
    setYearsSelection(prev => ({ ...prev, [name]: val }))
  }

  const startScrape = async (committeeName) => {
    const years = getYears(committeeName)
    setRunningTasks(prev => ({
      ...prev,
      [committeeName]: { status: 'starting', result: null }
    }))

    try {
      const resp = await axios.post('/api/committees/scrape', {
        committee_name: committeeName,
        years_back: years,
      })
      const taskId = resp.data.task_id

      setRunningTasks(prev => ({
        ...prev,
        [committeeName]: { taskId, status: 'running', result: null }
      }))

      // Poll for status
      const timer = setInterval(async () => {
        try {
          const statusResp = await axios.get(`/api/committees/scrape/${taskId}`)
          const task = statusResp.data

          if (task.status === 'completed' || task.status === 'error') {
            clearInterval(timer)
            delete pollTimers.current[committeeName]
            setRunningTasks(prev => ({
              ...prev,
              [committeeName]: {
                taskId,
                status: task.status,
                result: task.result,
              }
            }))
          }
        } catch {
          clearInterval(timer)
          delete pollTimers.current[committeeName]
        }
      }, 3000)

      pollTimers.current[committeeName] = timer

    } catch (err) {
      const msg = err.response?.data?.detail || 'שגיאה בהפעלת הסקריפט'
      setRunningTasks(prev => ({
        ...prev,
        [committeeName]: { status: 'error', result: { error: msg } }
      }))
    }
  }

  const data = activeTab === 'local' ? localData : districtData
  const filtered = filter
    ? data.filter(c => c.name.includes(filter) || c.district.includes(filter) || (c.settlements || '').includes(filter))
    : data

  const renderScrapeCell = (c) => {
    if (!hasScraper(c.name)) {
      return <span className="text-blue-800/20 text-sm">-</span>
    }

    const task = runningTasks[c.name]
    const years = getYears(c.name)
    const isRunning = task?.status === 'running' || task?.status === 'starting'

    return (
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-2">
          <select
            value={years}
            onChange={e => setYears(c.name, parseInt(e.target.value))}
            disabled={isRunning}
            className="px-2 py-1 border border-sky-200 rounded text-sm bg-white
                       focus:outline-none focus:ring-1 focus:ring-sky-400 disabled:opacity-50"
          >
            {[1, 2, 3, 5, 7, 10].map(y => (
              <option key={y} value={y}>{y} שנים</option>
            ))}
          </select>
          <button
            onClick={() => startScrape(c.name)}
            disabled={isRunning}
            className={`px-3 py-1 rounded text-sm font-medium transition-all whitespace-nowrap
              ${isRunning
                ? 'bg-amber-100 text-amber-700 cursor-wait'
                : 'bg-green-600 text-white hover:bg-green-700 shadow-sm'
              }`}
          >
            {isRunning ? (
              <span className="flex items-center gap-1">
                <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                מוריד...
              </span>
            ) : 'הורד פרוטוקולים'}
          </button>
        </div>

        {/* Result display */}
        {task?.status === 'completed' && task.result && (
          <div className="text-xs text-green-700 bg-green-50 rounded px-2 py-1">
            {task.result.total_documents != null
              ? `${task.result.total_documents} מסמכים הורדו`
              : task.result.message || 'הושלם בהצלחה'
            }
          </div>
        )}
        {task?.status === 'error' && task.result && (
          <div className="text-xs text-red-600 bg-red-50 rounded px-2 py-1">
            {task.result.error || 'שגיאה'}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-blue-50">
      {/* Header */}
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
            <h1 className="text-2xl font-bold text-white">ועדות תכנון ובנייה</h1>
            <p className="text-base text-blue-200">ועדות מקומיות ומחוזיות - מנהל התכנון</p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Tabs */}
        <div className="flex gap-1 bg-blue-900/10 rounded-xl p-1 mb-6">
          <button
            onClick={() => { setActiveTab('local'); setFilter('') }}
            className={`flex-1 py-3 px-6 rounded-lg text-base font-medium transition-all duration-200
                       ${activeTab === 'local'
                         ? 'bg-white text-blue-900 shadow-md'
                         : 'text-blue-800 hover:bg-white/50'
                       }`}
          >
            ועדות מקומיות ({localData.length})
          </button>
          <button
            onClick={() => { setActiveTab('district'); setFilter('') }}
            className={`flex-1 py-3 px-6 rounded-lg text-base font-medium transition-all duration-200
                       ${activeTab === 'district'
                         ? 'bg-white text-blue-900 shadow-md'
                         : 'text-blue-800 hover:bg-white/50'
                       }`}
          >
            ועדות מחוזיות ({districtData.length})
          </button>
        </div>

        {/* Filter */}
        <div className="mb-4">
          <input
            type="text"
            placeholder="סנן לפי שם או מחוז..."
            value={filter}
            onChange={e => setFilter(e.target.value)}
            className="w-full md:w-80 px-4 py-2 border border-sky-200 rounded-lg text-base text-blue-900
                       focus:outline-none focus:ring-2 focus:ring-sky-400"
          />
        </div>

        {/* Table */}
        <div className="bg-white rounded-2xl shadow-md border border-sky-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-base">
              <thead className="bg-sky-50">
                <tr>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">שם הוועדה</th>
                  {activeTab === 'local' && <th className="px-4 py-3 text-right font-bold text-blue-900">מחוז</th>}
                  {activeTab === 'local' && <th className="px-4 py-3 text-right font-bold text-blue-900">סוג</th>}
                  {activeTab === 'local' && <th className="px-4 py-3 text-right font-bold text-blue-900">יישובים</th>}
                  {activeTab === 'local' && <th className="px-4 py-3 text-right font-bold text-blue-900">פרוטוקולים</th>}
                  {activeTab === 'local' && <th className="px-4 py-3 text-right font-bold text-blue-900">סנכרון אחרון</th>}
                  {activeTab === 'local' && <th className="px-4 py-3 text-right font-bold text-blue-900">הורדת היסטוריה</th>}
                  {activeTab === 'district' && <th className="px-4 py-3 text-right font-bold text-blue-900">תיאור</th>}
                  <th className="px-4 py-3 text-right font-bold text-blue-900">קישורים</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={activeTab === 'local' ? 8 : 3} className="px-4 py-8 text-center text-blue-800/50">טוען...</td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={activeTab === 'local' ? 8 : 3} className="px-4 py-8 text-center text-blue-800/50">לא נמצאו תוצאות</td>
                  </tr>
                ) : (
                  filtered.map((c, i) => (
                    <tr key={i} className="border-t border-sky-50 hover:bg-sky-50/50">
                      <td className="px-4 py-3 text-blue-900 font-medium">{c.name}</td>
                      {activeTab === 'local' && (
                        <td className="px-4 py-3 text-blue-900">
                          <span className="px-2 py-1 bg-sky-50 rounded-md text-sm">{c.district}</span>
                        </td>
                      )}
                      {activeTab === 'local' && (
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded-md text-sm font-medium
                            ${c.type === 'מרחבית' ? 'bg-amber-50 text-amber-700' : 'bg-sky-50 text-sky-700'}`}>
                            {c.type}
                          </span>
                        </td>
                      )}
                      {activeTab === 'local' && (
                        <td className="px-4 py-3 text-blue-800 text-sm max-w-md">{c.settlements || '-'}</td>
                      )}
                      {activeTab === 'local' && (
                        <td className="px-4 py-3">
                          {c.protocols_from ? (
                            <div className="text-sm">
                              <span className="text-green-700 font-medium">{c.protocol_count} מסמכים</span>
                              <br />
                              <span className="text-blue-800/50">{c.protocols_from} - {c.protocols_to}</span>
                            </div>
                          ) : (
                            <span className="text-blue-800/30 text-sm">-</span>
                          )}
                        </td>
                      )}
                      {activeTab === 'local' && (
                        <td className="px-4 py-3">
                          {c.last_sync ? (
                            <span className="text-sm text-blue-800/60">{c.last_sync}</span>
                          ) : (
                            <span className="text-blue-800/30 text-sm">-</span>
                          )}
                        </td>
                      )}
                      {activeTab === 'local' && (
                        <td className="px-4 py-3">
                          {renderScrapeCell(c)}
                        </td>
                      )}
                      {activeTab === 'district' && (
                        <td className="px-4 py-3 text-blue-800 text-sm max-w-lg">{c.description}</td>
                      )}
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-2">
                          {c.url && (
                            <a href={c.url} target="_blank" rel="noopener noreferrer"
                               className="text-sky-600 hover:text-sky-800 underline text-sm">
                              דף הוועדה
                            </a>
                          )}
                          {c.planning_bureau && (
                            <a href={c.planning_bureau} target="_blank" rel="noopener noreferrer"
                               className="text-sky-600 hover:text-sky-800 underline text-sm">
                              לשכת תכנון
                            </a>
                          )}
                          {c.master_plans && (
                            <a href={c.master_plans} target="_blank" rel="noopener noreferrer"
                               className="text-sky-600 hover:text-sky-800 underline text-sm">
                              תכניות מתאר
                            </a>
                          )}
                          {c.contact && (
                            <a href={c.contact} target="_blank" rel="noopener noreferrer"
                               className="text-sky-600 hover:text-sky-800 underline text-sm">
                              יצירת קשר
                            </a>
                          )}
                          {!c.url && !c.planning_bureau && !c.master_plans && !c.contact && (
                            <span className="text-blue-800/30 text-sm">-</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="px-6 py-3 border-t border-sky-100 text-sm text-blue-800/50">
            מציג {filtered.length} מתוך {data.length} ועדות
          </div>
        </div>
      </main>
    </div>
  )
}

export default CommitteesPage
