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
    <div className="border-t-2 border-sky-200 bg-sky-50/50 px-4 py-3">
      <div className="flex items-start justify-between mb-2">
        <div>
          <h3 className="text-sm font-bold text-blue-900">{p.plan_number} - {p.plan_name}</h3>
          {p.district && <span className="text-xs text-blue-800/60">{p.district} | {p.planning_area || ''} | {p.municipality || ''}</span>}
        </div>
        <div className="flex gap-1.5 items-center">
          {p.mavat_url && <a href={p.mavat_url} target="_blank" rel="noopener noreferrer" className="px-2 py-1 bg-sky-600 text-white rounded text-[10px] hover:bg-sky-700">MAVAT ↗</a>}
          {p.sharepoint_url && <a href={p.sharepoint_url} target="_blank" rel="noopener noreferrer" className="px-2 py-1 bg-green-600 text-white rounded text-[10px] hover:bg-green-700">PDF ↗</a>}
          <button onClick={onClose} className="text-blue-800/40 hover:text-blue-800 text-lg mr-1">✕</button>
        </div>
      </div>
      <div className="flex gap-0.5 bg-blue-900/5 rounded p-0.5 mb-3 overflow-x-auto">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-2.5 py-1 rounded text-[11px] font-medium whitespace-nowrap transition-all
              ${tab === t.id ? 'bg-white text-blue-900 shadow-sm' : 'text-blue-800/60 hover:text-blue-900'}`}>
            {t.label}
          </button>
        ))}
      </div>
      {tab === 'info' && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
          <div><span className="text-blue-800/50">סמכות:</span> <span className="font-medium">{p.authority}</span></div>
          <div><span className="text-blue-800/50">סטטוס:</span> <span className="font-medium">{p.status}</span></div>
          <div><span className="text-blue-800/50">שטח:</span> <span className="font-medium">{p.area_dunam ? `${p.area_dunam.toLocaleString()} דונם` : '-'}</span></div>
          <div><span className="text-blue-800/50">סוג:</span> <span className="font-medium">{p.plan_type || '-'}</span></div>
          {p.housing_units && <div><span className="text-blue-800/50">יח"ד:</span> <span className="font-medium">{p.housing_units.toLocaleString()}</span></div>}
          {p.residential_sqm && <div><span className="text-blue-800/50">מגורים:</span> <span className="font-medium">{p.residential_sqm.toLocaleString()} מ"ר</span></div>}
          {p.commercial_sqm && <div><span className="text-blue-800/50">מסחר:</span> <span className="font-medium">{p.commercial_sqm.toLocaleString()} מ"ר</span></div>}
          {p.office_sqm && <div><span className="text-blue-800/50">משרדים:</span> <span className="font-medium">{p.office_sqm.toLocaleString()} מ"ר</span></div>}
          {p.hotel_rooms && <div><span className="text-blue-800/50">חדרי מלון:</span> <span className="font-medium">{p.hotel_rooms}</span></div>}
          <div><span className="text-blue-800/50">מיקום:</span> <span>{p.location}</span></div>
          {p.last_update && <div><span className="text-blue-800/50">עדכון:</span> <span>{p.last_update}</span></div>}
          {p.downloaded_files?.length > 0 && (
            <div className="col-span-full"><span className="text-blue-800/50">קבצים:</span>
              <div className="flex flex-wrap gap-1 mt-0.5">{p.downloaded_files.map((f, j) => <span key={j} className="px-1.5 py-0.5 bg-green-100 text-green-800 rounded text-[10px]">📄 {f}</span>)}</div>
            </div>
          )}
        </div>
      )}
      {tab === 'purpose' && (
        <div className="text-xs space-y-3">
          {p.purpose && <div><h4 className="font-bold text-blue-900 mb-1">מטרת התכנית</h4><p className="text-blue-800 bg-white rounded p-2 border border-sky-100 whitespace-pre-line">{p.purpose}</p></div>}
          {p.main_instructions && <div><h4 className="font-bold text-blue-900 mb-1">עיקרי הוראותיה</h4><p className="text-blue-800 bg-white rounded p-2 border border-sky-100 whitespace-pre-line">{p.main_instructions}</p></div>}
        </div>
      )}
      {tab === 'explanation' && p.explanation && (
        <div className="text-xs"><h4 className="font-bold text-blue-900 mb-1">דברי הסבר</h4><p className="text-blue-800 bg-white rounded p-2 border border-sky-100 whitespace-pre-line leading-relaxed">{p.explanation}</p></div>
      )}
      {tab === 'stages' && p.processing_stages?.length > 0 && (
        <div className="text-xs"><h4 className="font-bold text-blue-900 mb-1">שלבי טיפול</h4>
          <table className="w-full bg-white rounded border border-sky-100"><thead className="bg-sky-50"><tr><th className="px-2 py-1 text-right text-blue-900">שלב</th><th className="px-2 py-1 text-right text-blue-900">תאריך</th></tr></thead>
            <tbody>{p.processing_stages.map((s, j) => <tr key={j} className="border-t border-sky-50"><td className="px-2 py-1">{s.status}</td><td className="px-2 py-1">{s.date}</td></tr>)}</tbody></table>
        </div>
      )}
      {tab === 'decisions' && p.committee_decisions?.length > 0 && (
        <div className="text-xs"><h4 className="font-bold text-blue-900 mb-1">החלטות מוסדות תכנון</h4>
          <table className="w-full bg-white rounded border border-sky-100"><thead className="bg-sky-50"><tr><th className="px-2 py-1 text-right text-blue-900">ישיבה</th><th className="px-2 py-1 text-right text-blue-900">מוסד</th><th className="px-2 py-1 text-right text-blue-900">תאריך</th></tr></thead>
            <tbody>{p.committee_decisions.map((d, j) => <tr key={j} className="border-t border-sky-50"><td className="px-2 py-1 font-mono">{d.session_number}</td><td className="px-2 py-1 text-[10px]">{d.institution}</td><td className="px-2 py-1">{d.date}</td></tr>)}</tbody></table>
        </div>
      )}
      {tab === 'gushim' && p.gushim?.length > 0 && (
        <div className="text-xs"><h4 className="font-bold text-blue-900 mb-1">גושים וחלקות</h4>
          <table className="w-full bg-white rounded border border-sky-100"><thead className="bg-sky-50"><tr><th className="px-2 py-1 text-right text-blue-900">גוש</th><th className="px-2 py-1 text-right text-blue-900">חלקות מלאות</th><th className="px-2 py-1 text-right text-blue-900">חלקות חלקיות</th></tr></thead>
            <tbody>{p.gushim.map((g, j) => <tr key={j} className="border-t border-sky-50"><td className="px-2 py-1 font-bold font-mono">{g.gush}</td><td className="px-2 py-1">{g.helkot_full || g.helka || '-'}</td><td className="px-2 py-1">{g.helkot_partial || '-'}</td></tr>)}</tbody></table>
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
  const [databases, setDatabases] = useState([])
  const [activeDb, setActiveDb] = useState('plans_tanai_saf')
  const [filter, setFilter] = useState('')
  const [authorityFilter, setAuthorityFilter] = useState('')
  const [pdfFilter, setPdfFilter] = useState('')
  const [minArea, setMinArea] = useState('')
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [reviewFilter, setReviewFilter] = useState('')
  const [statuses, setStatuses] = useState({})
  const limit = 50

  useEffect(() => {
    axios.get('/api/plans/databases').then(r => setDatabases(r.data || [])).catch(() => {})
    axios.get('/api/plans/statuses').then(r => setStatuses(r.data || {})).catch(() => {})
  }, [])

  useEffect(() => {
    axios.get('/api/plans/stats', { params: { db: activeDb } }).then(r => setStats(r.data)).catch(() => {})
    setOffset(0)
  }, [activeDb])

  useEffect(() => {
    setLoading(true)
    const params = { limit, offset, db: activeDb }
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
  }, [filter, authorityFilter, pdfFilter, minArea, offset, activeDb])

  // Client-side filter by review status (separate from API fetch)
  const filteredPlans = reviewFilter ? plans.filter(p => {
    const st = statuses[p.plan_number] || {}
    if (reviewFilter === 'reviewed') return st.reviewed
    if (reviewFilter === 'not_reviewed') return !st.reviewed
    if (reviewFilter === 'continue') return st.continue_handling
    if (reviewFilter === 'high') return st.priority === 'high'
    if (reviewFilter === 'medium') return st.priority === 'medium'
    if (reviewFilter === 'low') return st.priority === 'low'
    return true
  }) : plans
  const displayTotal = reviewFilter ? filteredPlans.length : total

  const updateStatus = async (planNum, field, value) => {
    const body = {}
    body[field] = value
    try {
      await axios.put(`/api/plans/status/${encodeURIComponent(planNum)}`, body)
      setStatuses(prev => ({
        ...prev,
        [planNum]: { ...prev[planNum], [field]: value }
      }))
    } catch {}
  }

  const getStatus = (planNum) => statuses[planNum] || {}

  const totalPages = Math.ceil(displayTotal / limit)
  const currentPage = Math.floor(offset / limit) + 1

  // Compact cell classes
  const th = "px-2 py-1.5 text-right text-[11px] font-bold text-blue-900 whitespace-nowrap"
  const td = "px-2 py-1.5 text-[11px] text-blue-900"

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-blue-50">
      <header className="bg-blue-900 shadow-lg">
        <div className="max-w-[1600px] mx-auto px-4 py-4 flex items-center gap-3">
          <button onClick={() => navigate('/')} className="text-sm text-blue-200 hover:text-white font-medium">&larr; דף הבית</button>
          <div className="border-r border-blue-700 h-5" />
          <div className="flex-1">
            <h1 className="text-xl font-bold text-white">תוכניות תכנון ובנייה</h1>
            <p className="text-sm text-blue-200">תוכניות מעל 10,000 מ"ר</p>
          </div>
          <button onClick={() => navigate('/map?layer=plans')} className="px-3 py-1.5 bg-sky-500 hover:bg-sky-400 text-white rounded text-xs font-medium">🗺️ מפה</button>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-4 py-4">
        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-4 gap-2 mb-3">
            {[
              { v: stats.total_plans, l: 'סה"כ', c: 'text-blue-900' },
              { v: stats.plans_with_pdf, l: 'עם PDF', c: 'text-green-700' },
              { v: stats.plans_with_area, l: 'עם שטח', c: 'text-purple-700' },
              { v: stats.plans_with_gush, l: 'עם גוש', c: 'text-amber-700' },
            ].map((s, i) => (
              <div key={i} className="bg-white rounded-lg shadow-sm border border-sky-100 p-2 text-center">
                <div className={`text-2xl font-bold ${s.c}`}>{s.v}</div>
                <div className="text-[10px] text-blue-800/60">{s.l}</div>
              </div>
            ))}
          </div>
        )}

        {/* DB selector */}
        {databases.length > 1 && (
          <div className="flex gap-0.5 bg-blue-900/10 rounded-lg p-0.5 mb-3">
            {databases.map(db => (
              <button key={db.name} onClick={() => setActiveDb(db.name)}
                className={`flex-1 py-1.5 px-2 rounded text-xs font-medium transition-all
                  ${activeDb === db.name ? 'bg-white text-blue-900 shadow-sm' : 'text-blue-800 hover:bg-white/50'}`}>
                {db.title.replace('כל התוכניות, סטטוס: ', '').replace(', שטח מעל 10,000 מ"ר', '')}
                <span className="mr-1 text-[10px] opacity-60">({db.total_plans})</span>
              </button>
            ))}
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-wrap gap-2 mb-3">
          <input type="text" placeholder="חיפוש..." value={filter}
            onChange={e => { setFilter(e.target.value); setOffset(0) }}
            className="flex-1 min-w-48 px-3 py-1.5 border border-sky-200 rounded text-sm focus:outline-none focus:ring-1 focus:ring-sky-400" />
          {[
            { v: authorityFilter, set: setAuthorityFilter, opts: [['', 'סמכות'], ['מקומית', 'מקומית'], ['מחוזית', 'מחוזית'], ['ארצית', 'ארצית']] },
            { v: pdfFilter, set: setPdfFilter, opts: [['', 'PDF'], ['yes', 'עם PDF'], ['no', 'בלי PDF']] },
            { v: reviewFilter, set: setReviewFilter, opts: [['', 'סיווג'], ['not_reviewed', 'לא נבדק'], ['reviewed', 'נבדק'], ['continue', 'המשך טיפול'], ['high', 'עדיפות גבוהה'], ['medium', 'עדיפות בינונית'], ['low', 'עדיפות נמוכה']] },
          ].map((f, i) => (
            <select key={i} value={f.v} onChange={e => { f.set(e.target.value); setOffset(0) }}
              className="px-2 py-1.5 border border-sky-200 rounded text-sm bg-white focus:outline-none focus:ring-1 focus:ring-sky-400">
              {f.opts.map(([val, label]) => <option key={val} value={val}>{label}</option>)}
            </select>
          ))}
          <input type="number" placeholder="שטח מינ' (דונם)" value={minArea}
            onChange={e => { setMinArea(e.target.value); setOffset(0) }}
            className="w-32 px-2 py-1.5 border border-sky-200 rounded text-sm focus:outline-none focus:ring-1 focus:ring-sky-400" />
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl shadow-md border border-sky-100 overflow-hidden">
          <div className="overflow-x-auto max-h-[calc(100vh-280px)]">
            <table className="w-full border-collapse">
              <thead className="bg-sky-50 sticky top-0 z-10 shadow-sm">
                <tr>
                  {/* Classification columns FIRST (right side in RTL) */}
                  <th className={th}>נבדק</th>
                  <th className={th}>המשך טיפול</th>
                  <th className={th}>שלב בדיקה</th>
                  <th className={th}>עדיפות</th>
                  {/* Data columns */}
                  <th className={th}>מספר תכנית</th>
                  <th className={th}>שם תכנית</th>
                  <th className={th}>סמכות</th>
                  <th className={th}>מיקום</th>
                  <th className={th}>שטח (דונם)</th>
                  <th className={th}>יח"ד</th>
                  <th className={th}>מגורים (מ"ר)</th>
                  <th className={th}>מסחר (מ"ר)</th>
                  <th className={th}>גושים</th>
                  <th className={th}>פעילות</th>
                  <th className={th}>PDF</th>
                  <th className={th}>קישור</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={16} className="px-4 py-8 text-center text-blue-800/50 text-sm">
                    <svg className="animate-spin h-5 w-5 mx-auto mb-1 text-sky-500" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                    טוען...
                  </td></tr>
                ) : filteredPlans.length === 0 ? (
                  <tr><td colSpan={16} className="px-4 py-8 text-center text-blue-800/50 text-sm">לא נמצאו תוכניות</td></tr>
                ) : (
                  filteredPlans.map((p, i) => {
                    const st = getStatus(p.plan_number)
                    const rowBg = selectedPlan?.plan_number === p.plan_number ? 'bg-sky-100'
                      : st.continue_handling ? 'bg-green-50/40'
                      : st.priority === 'high' ? 'bg-red-50/30'
                      : st.reviewed && !st.continue_handling ? 'bg-gray-50/40' : ''

                    return (
                    <React.Fragment key={i}>
                    <tr className={`border-b border-gray-200 hover:bg-sky-50/50 cursor-pointer transition-colors ${rowBg}`}
                        onClick={() => setSelectedPlan(selectedPlan?.plan_number === p.plan_number ? null : p)}>

                      {/* נבדק - checkbox */}
                      <td className={`${td} text-center`} onClick={e => e.stopPropagation()}>
                        <input type="checkbox" checked={!!st.reviewed}
                          onChange={e => updateStatus(p.plan_number, 'reviewed', e.target.checked)}
                          className="w-3.5 h-3.5 accent-blue-600 cursor-pointer" />
                      </td>

                      {/* המשך טיפול - checkbox */}
                      <td className={`${td} text-center`} onClick={e => e.stopPropagation()}>
                        <input type="checkbox" checked={!!st.continue_handling}
                          onChange={e => updateStatus(p.plan_number, 'continue_handling', e.target.checked)}
                          className="w-3.5 h-3.5 accent-green-600 cursor-pointer" />
                      </td>

                      {/* שלב בדיקה - droplist */}
                      <td className={td} onClick={e => e.stopPropagation()}>
                        <select value={st.check_stage || ''} onChange={e => updateStatus(p.plan_number, 'check_stage', e.target.value)}
                          className="text-[10px] px-1 py-0.5 rounded border border-gray-200 bg-white w-full min-w-[70px]">
                          <option value="">-</option>
                          <option value="בדיקה תכנונית">בדיקה תכנונית</option>
                          <option value="איתור בעלים">איתור בעלים</option>
                        </select>
                      </td>

                      {/* עדיפות - droplist */}
                      <td className={td} onClick={e => e.stopPropagation()}>
                        <select value={st.priority || ''} onChange={e => updateStatus(p.plan_number, 'priority', e.target.value || null)}
                          className={`text-[10px] px-1 py-0.5 rounded border w-full min-w-[55px]
                            ${st.priority === 'high' ? 'bg-red-100 border-red-300 text-red-800' :
                              st.priority === 'medium' ? 'bg-amber-100 border-amber-300 text-amber-800' :
                              st.priority === 'low' ? 'bg-gray-100 border-gray-300' : 'border-gray-200 bg-white'}`}>
                          <option value="">-</option>
                          <option value="high">גבוהה</option>
                          <option value="medium">בינונית</option>
                          <option value="low">נמוכה</option>
                        </select>
                      </td>

                      {/* מספר תכנית */}
                      <td className={`${td} font-mono font-medium whitespace-nowrap`}>{p.plan_number}</td>

                      {/* שם */}
                      <td className={`${td} max-w-[200px]`}>
                        <div className="truncate">{p.plan_name}</div>
                        {p.purpose && <div className="text-[10px] text-blue-800/40 truncate">{p.purpose}</div>}
                      </td>

                      {/* סמכות */}
                      <td className={td}>
                        <span className={`px-1 py-0.5 rounded text-[10px] font-medium
                          ${p.authority === 'מחוזית' ? 'bg-purple-50 text-purple-700' :
                            p.authority === 'ארצית' ? 'bg-red-50 text-red-700' : 'bg-sky-50 text-sky-700'}`}>
                          {p.authority}
                        </span>
                      </td>

                      {/* מיקום */}
                      <td className={`${td} max-w-[140px]`}><div className="truncate text-blue-800">{p.location}</div></td>

                      {/* שטח */}
                      <td className={`${td} text-center`}>{p.area_dunam ? <span className="font-medium">{p.area_dunam.toLocaleString()}</span> : <span className="text-gray-300">-</span>}</td>

                      {/* יח"ד */}
                      <td className={`${td} text-center`}>{p.housing_units ? <span className="font-medium">{p.housing_units.toLocaleString()}</span> : <span className="text-gray-300">-</span>}</td>

                      {/* מגורים */}
                      <td className={`${td} text-center`}>{p.residential_sqm ? <span className="font-medium">{p.residential_sqm.toLocaleString()}</span> : <span className="text-gray-300">-</span>}</td>

                      {/* מסחר */}
                      <td className={`${td} text-center`}>{p.commercial_sqm ? <span className="font-medium">{p.commercial_sqm.toLocaleString()}</span> : <span className="text-gray-300">-</span>}</td>

                      {/* גושים */}
                      <td className={td}>
                        {p.gushim?.length > 0 ? (
                          <div className="flex flex-wrap gap-0.5">
                            {p.gushim.slice(0, 2).map((g, j) => <span key={j} className="px-1 py-0 bg-amber-50 text-amber-800 rounded text-[10px]">{g.gush}</span>)}
                            {p.gushim.length > 2 && <span className="text-[10px] text-gray-400">+{p.gushim.length - 2}</span>}
                          </div>
                        ) : <span className="text-gray-300">-</span>}
                      </td>

                      {/* פעילות אחרונה */}
                      <td className={`${td} text-center text-[10px] text-blue-800/60 whitespace-nowrap`}>{p.last_activity_date || '-'}</td>

                      {/* PDF */}
                      <td className={`${td} text-center`}>
                        {(p.has_horaot_pdf || p.has_tashrit_pdf) ? <span className="text-green-600 text-[10px]">📄</span> : <span className="text-gray-300 text-[10px]">-</span>}
                      </td>

                      {/* קישור */}
                      <td className={td} onClick={e => e.stopPropagation()}>
                        {p.mavat_url && <a href={p.mavat_url} target="_blank" rel="noopener noreferrer" className="text-sky-600 hover:text-sky-800 text-[10px] underline">MAVAT</a>}
                      </td>
                    </tr>

                    {selectedPlan?.plan_number === p.plan_number && (
                      <tr><td colSpan={16} className="p-0"><DetailPanel plan={selectedPlan} onClose={() => setSelectedPlan(null)} /></td></tr>
                    )}
                    </React.Fragment>
                  )})
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-4 py-2 border-t border-sky-100 flex items-center justify-between text-xs">
            <span className="text-blue-800/50">{offset + 1}-{Math.min(offset + limit, total)} מתוך {displayTotal}</span>
            <div className="flex gap-1.5">
              <button onClick={() => setOffset(Math.max(0, offset - limit))} disabled={offset === 0}
                className="px-2 py-0.5 rounded border border-sky-200 hover:bg-sky-50 disabled:opacity-30">← הקודם</button>
              <span className="px-2 py-0.5 text-blue-800/60">{currentPage}/{totalPages}</span>
              <button onClick={() => setOffset(offset + limit)} disabled={offset + limit >= displayTotal}
                className="px-2 py-0.5 rounded border border-sky-200 hover:bg-sky-50 disabled:opacity-30">הבא →</button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default PlansPage
