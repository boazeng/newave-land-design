import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

function DetailPanel({ plan: p, onClose }) {
  const [tab, setTab] = useState('info')

  const tabs = [
    { id: 'info', label: 'פרטים כלליים' },
    { id: 'purpose', label: 'מטרות התכנית', show: p.purpose || p.main_instructions },
    { id: 'explanation', label: 'דברי הסבר', show: p.explanation },
    { id: 'stages', label: 'שלבי טיפול', show: p.processing_stages?.length > 0 },
    { id: 'decisions', label: 'החלטות', show: p.committee_decisions?.length > 0 },
    { id: 'gushim', label: 'גושים וחלקות', show: p.gushim?.length > 0 },
  ].filter(t => t.show !== false)

  return (
    <div className="border-t-2 border-sky-200 bg-sky-50/50 px-6 py-4">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-lg font-bold text-blue-900">{p.plan_number} - {p.plan_name}</h3>
          {p.district && (
            <span className="text-sm text-blue-800/60">
              {p.district} | {p.planning_area || ''} | {p.municipality || ''}
            </span>
          )}
        </div>
        <div className="flex gap-2 items-center">
          {p.mavat_url && (
            <a href={p.mavat_url} target="_blank" rel="noopener noreferrer"
               className="px-3 py-1.5 bg-sky-600 text-white rounded-lg text-xs hover:bg-sky-700">
              MAVAT ↗
            </a>
          )}
          {p.sharepoint_url && (
            <a href={p.sharepoint_url} target="_blank" rel="noopener noreferrer"
               className="px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs hover:bg-green-700">
              PDF ↗
            </a>
          )}
          <button onClick={onClose} className="text-blue-800/40 hover:text-blue-800 text-xl mr-2">✕</button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-blue-900/5 rounded-lg p-0.5 mb-4 overflow-x-auto">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-all
              ${tab === t.id ? 'bg-white text-blue-900 shadow-sm' : 'text-blue-800/60 hover:text-blue-900'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {tab === 'info' && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div><span className="text-blue-800/50">סמכות:</span><span className="mr-2 font-medium">{p.authority}</span></div>
          <div><span className="text-blue-800/50">סטטוס:</span><span className="mr-2 font-medium">{p.status}</span></div>
          <div><span className="text-blue-800/50">שטח:</span><span className="mr-2 font-medium">{p.area_dunam ? `${p.area_dunam.toLocaleString()} דונם` : '-'}</span></div>
          <div><span className="text-blue-800/50">סוג:</span><span className="mr-2 font-medium">{p.plan_type || '-'}</span></div>
          {p.housing_units && <div><span className="text-blue-800/50">יח"ד:</span><span className="mr-2 font-medium">{p.housing_units.toLocaleString()}</span></div>}
          {p.residential_sqm && <div><span className="text-blue-800/50">מגורים:</span><span className="mr-2 font-medium">{p.residential_sqm.toLocaleString()} מ"ר</span></div>}
          {p.commercial_sqm && <div><span className="text-blue-800/50">מסחר:</span><span className="mr-2 font-medium">{p.commercial_sqm.toLocaleString()} מ"ר</span></div>}
          {p.office_sqm && <div><span className="text-blue-800/50">משרדים:</span><span className="mr-2 font-medium">{p.office_sqm.toLocaleString()} מ"ר</span></div>}
          {p.hotel_rooms && <div><span className="text-blue-800/50">חדרי מלון:</span><span className="mr-2 font-medium">{p.hotel_rooms}</span></div>}
          <div><span className="text-blue-800/50">מיקום:</span><span className="mr-2">{p.location}</span></div>
          {p.last_update && <div><span className="text-blue-800/50">עדכון אחרון:</span><span className="mr-2">{p.last_update}</span></div>}
          {p.downloaded_files?.length > 0 && (
            <div className="col-span-full">
              <span className="text-blue-800/50">קבצים שהורדו:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {p.downloaded_files.map((f, j) => (
                  <span key={j} className="px-2 py-0.5 bg-green-100 text-green-800 rounded text-xs">📄 {f}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'purpose' && (
        <div className="text-sm space-y-4">
          {p.purpose && (
            <div>
              <h4 className="font-bold text-blue-900 mb-2">מטרת התכנית</h4>
              <p className="text-blue-800 bg-white rounded-lg p-3 border border-sky-100 whitespace-pre-line">{p.purpose}</p>
            </div>
          )}
          {p.main_instructions && (
            <div>
              <h4 className="font-bold text-blue-900 mb-2">עיקרי הוראותיה</h4>
              <p className="text-blue-800 bg-white rounded-lg p-3 border border-sky-100 whitespace-pre-line">{p.main_instructions}</p>
            </div>
          )}
        </div>
      )}

      {tab === 'explanation' && p.explanation && (
        <div className="text-sm">
          <h4 className="font-bold text-blue-900 mb-2">דברי הסבר</h4>
          <p className="text-blue-800 bg-white rounded-lg p-3 border border-sky-100 whitespace-pre-line leading-relaxed">{p.explanation}</p>
        </div>
      )}

      {tab === 'stages' && p.processing_stages?.length > 0 && (
        <div className="text-sm">
          <h4 className="font-bold text-blue-900 mb-2">שלבי טיפול בתכנית</h4>
          <div className="bg-white rounded-lg border border-sky-100 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-sky-50">
                <tr>
                  <th className="px-4 py-2 text-right font-bold text-blue-900">שלב</th>
                  <th className="px-4 py-2 text-right font-bold text-blue-900">תאריך</th>
                </tr>
              </thead>
              <tbody>
                {p.processing_stages.map((s, j) => (
                  <tr key={j} className="border-t border-sky-50">
                    <td className="px-4 py-2 text-blue-900">{s.status}</td>
                    <td className="px-4 py-2 text-blue-800">{s.date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'decisions' && p.committee_decisions?.length > 0 && (
        <div className="text-sm">
          <h4 className="font-bold text-blue-900 mb-2">החלטות מוסדות תכנון</h4>
          <div className="bg-white rounded-lg border border-sky-100 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-sky-50">
                <tr>
                  <th className="px-4 py-2 text-right font-bold text-blue-900">מספר ישיבה</th>
                  <th className="px-4 py-2 text-right font-bold text-blue-900">מוסד תכנון</th>
                  <th className="px-4 py-2 text-right font-bold text-blue-900">תאריך</th>
                </tr>
              </thead>
              <tbody>
                {p.committee_decisions.map((d, j) => (
                  <tr key={j} className="border-t border-sky-50">
                    <td className="px-4 py-2 text-blue-900 font-mono">{d.session_number}</td>
                    <td className="px-4 py-2 text-blue-800 text-xs">{d.institution}</td>
                    <td className="px-4 py-2 text-blue-800">{d.date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'gushim' && p.gushim?.length > 0 && (
        <div className="text-sm">
          <h4 className="font-bold text-blue-900 mb-2">גושים וחלקות</h4>
          <div className="bg-white rounded-lg border border-sky-100 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-sky-50">
                <tr>
                  <th className="px-4 py-2 text-right font-bold text-blue-900">מספר גוש</th>
                  <th className="px-4 py-2 text-right font-bold text-blue-900">חלקות בשלמותן</th>
                  <th className="px-4 py-2 text-right font-bold text-blue-900">חלקות בחלקן</th>
                </tr>
              </thead>
              <tbody>
                {p.gushim.map((g, j) => (
                  <tr key={j} className="border-t border-sky-50">
                    <td className="px-4 py-2 text-blue-900 font-bold font-mono">{g.gush}</td>
                    <td className="px-4 py-2 text-blue-800">{g.helkot_full || g.helka || '-'}</td>
                    <td className="px-4 py-2 text-blue-800">{g.helkot_partial || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function PlansPage() {
  const navigate = useNavigate()
  const [plans, setPlans] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [authorityFilter, setAuthorityFilter] = useState('')
  const [pdfFilter, setPdfFilter] = useState('')
  const [minArea, setMinArea] = useState('')
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [selectedPlan, setSelectedPlan] = useState(null)
  const limit = 50

  useEffect(() => {
    axios.get('/api/plans/stats').then(r => setStats(r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    const params = { limit, offset }
    if (filter) params.q = filter
    if (authorityFilter) params.authority = authorityFilter
    if (pdfFilter === 'yes') params.has_pdf = true
    if (pdfFilter === 'no') params.has_pdf = false
    if (minArea) params.min_area = parseFloat(minArea)

    axios.get('/api/plans/search', { params })
      .then(r => {
        setPlans(r.data.plans || [])
        setTotal(r.data.total || 0)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [filter, authorityFilter, pdfFilter, minArea, offset])

  const totalPages = Math.ceil(total / limit)
  const currentPage = Math.floor(offset / limit) + 1

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-blue-50">
      {/* Header */}
      <header className="bg-blue-900 shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-6 flex items-center gap-4">
          <button onClick={() => navigate('/')} className="text-base text-blue-200 hover:text-white font-medium">
            &larr; דף הבית
          </button>
          <div className="border-r border-blue-700 h-6" />
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-white">תוכניות תכנון ובנייה</h1>
            <p className="text-base text-blue-200">תוכניות בבדיקת תנאי סף - מעל 10,000 מ"ר</p>
          </div>
          <button
            onClick={() => navigate('/map?layer=plans')}
            className="px-4 py-2 bg-sky-500 hover:bg-sky-400 text-white rounded-lg text-sm font-medium transition-colors"
          >
            🗺️ הצג על המפה
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-xl shadow-sm border border-sky-100 p-4 text-center">
              <div className="text-3xl font-bold text-blue-900">{stats.total_plans}</div>
              <div className="text-sm text-blue-800/60 mt-1">סה"כ תוכניות</div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-sky-100 p-4 text-center">
              <div className="text-3xl font-bold text-green-700">{stats.plans_with_pdf}</div>
              <div className="text-sm text-blue-800/60 mt-1">עם קובץ PDF</div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-sky-100 p-4 text-center">
              <div className="text-3xl font-bold text-purple-700">{stats.plans_with_area}</div>
              <div className="text-sm text-blue-800/60 mt-1">עם נתוני שטח</div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-sky-100 p-4 text-center">
              <div className="text-3xl font-bold text-amber-700">{stats.plans_with_gush}</div>
              <div className="text-sm text-blue-800/60 mt-1">עם גוש/חלקה</div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-4">
          <input
            type="text"
            placeholder="חיפוש לפי שם, מספר או מיקום..."
            value={filter}
            onChange={e => { setFilter(e.target.value); setOffset(0) }}
            className="flex-1 min-w-64 px-4 py-2 border border-sky-200 rounded-lg text-base text-blue-900
                       focus:outline-none focus:ring-2 focus:ring-sky-400"
          />
          <select
            value={authorityFilter}
            onChange={e => { setAuthorityFilter(e.target.value); setOffset(0) }}
            className="px-4 py-2 border border-sky-200 rounded-lg text-base text-blue-900 bg-white
                       focus:outline-none focus:ring-2 focus:ring-sky-400"
          >
            <option value="">כל הסמכויות</option>
            <option value="מקומית">מקומית</option>
            <option value="מחוזית">מחוזית</option>
            <option value="ארצית">ארצית</option>
          </select>
          <select
            value={pdfFilter}
            onChange={e => { setPdfFilter(e.target.value); setOffset(0) }}
            className="px-4 py-2 border border-sky-200 rounded-lg text-base text-blue-900 bg-white
                       focus:outline-none focus:ring-2 focus:ring-sky-400"
          >
            <option value="">כל התוכניות</option>
            <option value="yes">עם PDF</option>
            <option value="no">בלי PDF</option>
          </select>
          <input
            type="number"
            placeholder="שטח מינימלי (דונם)"
            value={minArea}
            onChange={e => { setMinArea(e.target.value); setOffset(0) }}
            className="w-44 px-4 py-2 border border-sky-200 rounded-lg text-base text-blue-900
                       focus:outline-none focus:ring-2 focus:ring-sky-400"
          />
        </div>

        {/* Table */}
        <div className="bg-white rounded-2xl shadow-md border border-sky-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-base">
              <thead className="bg-sky-50">
                <tr>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">מספר תכנית</th>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">שם תכנית</th>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">סמכות</th>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">מיקום</th>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">שטח (דונם)</th>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">יח"ד</th>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">מגורים (מ"ר)</th>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">מסחר (מ"ר)</th>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">גושים</th>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">מסמכים</th>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">קישורים</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={11} className="px-4 py-12 text-center text-blue-800/50">
                      <svg className="animate-spin h-6 w-6 mx-auto mb-2 text-sky-500" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      טוען תוכניות...
                    </td>
                  </tr>
                ) : plans.length === 0 ? (
                  <tr>
                    <td colSpan={11} className="px-4 py-12 text-center text-blue-800/50">לא נמצאו תוכניות</td>
                  </tr>
                ) : (
                  plans.map((p, i) => (
                    <React.Fragment key={i}>
                    <tr
                      className={`border-t border-sky-50 hover:bg-sky-50/50 cursor-pointer transition-colors
                        ${selectedPlan?.plan_number === p.plan_number ? 'bg-sky-100' : ''}`}
                      onClick={() => setSelectedPlan(selectedPlan?.plan_number === p.plan_number ? null : p)}
                    >
                      <td className="px-4 py-3 text-blue-900 font-mono text-sm font-medium whitespace-nowrap">
                        {p.plan_number}
                      </td>
                      <td className="px-4 py-3 text-blue-900 max-w-xs">
                        <div className="truncate">{p.plan_name}</div>
                        {p.purpose && (
                          <div className="text-xs text-blue-800/50 truncate mt-0.5">{p.purpose}</div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-md text-xs font-medium
                          ${p.authority === 'מחוזית' ? 'bg-purple-50 text-purple-700' :
                            p.authority === 'ארצית' ? 'bg-red-50 text-red-700' :
                            'bg-sky-50 text-sky-700'}`}>
                          {p.authority}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-blue-800 text-sm max-w-xs">
                        <div className="truncate">{p.location}</div>
                      </td>
                      <td className="px-4 py-3 text-blue-900 text-sm text-center">
                        {p.area_dunam ? (
                          <span className="font-medium">{p.area_dunam.toLocaleString()}</span>
                        ) : (
                          <span className="text-blue-800/20">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-blue-900 text-sm text-center">
                        {p.housing_units ? (
                          <span className="font-medium">{p.housing_units.toLocaleString()}</span>
                        ) : (
                          <span className="text-blue-800/20">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-blue-900 text-sm text-center">
                        {p.residential_sqm ? (
                          <span className="font-medium">{p.residential_sqm.toLocaleString()}</span>
                        ) : (
                          <span className="text-blue-800/20">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-blue-900 text-sm text-center">
                        {p.commercial_sqm ? (
                          <span className="font-medium">{p.commercial_sqm.toLocaleString()}</span>
                        ) : (
                          <span className="text-blue-800/20">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {p.gushim && p.gushim.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {p.gushim.slice(0, 3).map((g, j) => (
                              <span key={j} className="px-1.5 py-0.5 bg-amber-50 text-amber-800 rounded text-xs">
                                {g.gush}{g.helka ? `/${g.helka}` : ''}
                              </span>
                            ))}
                            {p.gushim.length > 3 && (
                              <span className="text-xs text-blue-800/40">+{p.gushim.length - 3}</span>
                            )}
                          </div>
                        ) : (
                          <span className="text-blue-800/20">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex items-center gap-1 justify-center">
                          {p.has_horaot_pdf && (
                            <span className="px-1.5 py-0.5 bg-green-50 text-green-700 rounded text-xs" title="הוראות">📄</span>
                          )}
                          {p.has_tashrit_pdf && (
                            <span className="px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded text-xs" title="תשריט">🗺️</span>
                          )}
                          {!p.has_horaot_pdf && !p.has_tashrit_pdf && (
                            <span className="text-blue-800/20 text-xs">אין</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          {p.mavat_url && (
                            <a href={p.mavat_url} target="_blank" rel="noopener noreferrer"
                               onClick={e => e.stopPropagation()}
                               className="text-sky-600 hover:text-sky-800 text-xs underline">
                              MAVAT
                            </a>
                          )}
                          {p.sharepoint_url && (
                            <a href={p.sharepoint_url} target="_blank" rel="noopener noreferrer"
                               onClick={e => e.stopPropagation()}
                               className="text-green-600 hover:text-green-800 text-xs underline">
                              PDF
                            </a>
                          )}
                        </div>
                      </td>
                    </tr>
                    {selectedPlan?.plan_number === p.plan_number && (
                      <tr>
                        <td colSpan={11} className="p-0">
                          <DetailPanel plan={selectedPlan} onClose={() => setSelectedPlan(null)} />
                        </td>
                      </tr>
                    )}
                    </React.Fragment>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-6 py-3 border-t border-sky-100 flex items-center justify-between">
            <span className="text-sm text-blue-800/50">
              מציג {offset + 1}-{Math.min(offset + limit, total)} מתוך {total} תוכניות
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setOffset(Math.max(0, offset - limit))}
                disabled={offset === 0}
                className="px-3 py-1 rounded-lg text-sm border border-sky-200 text-blue-900
                           hover:bg-sky-50 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                ← הקודם
              </button>
              <span className="px-3 py-1 text-sm text-blue-800/60">
                עמוד {currentPage} מתוך {totalPages}
              </span>
              <button
                onClick={() => setOffset(offset + limit)}
                disabled={offset + limit >= total}
                className="px-3 py-1 rounded-lg text-sm border border-sky-200 text-blue-900
                           hover:bg-sky-50 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                הבא →
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default PlansPage
