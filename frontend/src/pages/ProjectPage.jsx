import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import axios from 'axios'

const STATUSES = ['פעיל', 'בהמתנה', 'הושלם']

/** Plan fields worth showing on a project page, in display order. */
const PLAN_FIELDS = [
  ['status', 'סטטוס תוכנית'],
  ['authority', 'סמכות'],
  ['plan_type', 'סוג תוכנית'],
  ['area_dunam', 'שטח (דונם)'],
  ['purpose', 'מטרת התוכנית'],
  ['district', 'מחוז'],
  ['planning_area', 'מרחב תכנון'],
  ['last_update', 'עדכון אחרון'],
]

function ProjectPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    axios.get(`/api/projects/${encodeURIComponent(id)}`)
      .then(r => { setProject(r.data); setNotes(r.data.notes || '') })
      .catch(() => setError('הפרוייקט לא נמצא'))
      .finally(() => setLoading(false))
  }, [id])

  const save = async (updates) => {
    setSaving(true)
    try {
      const r = await axios.put(`/api/projects/${encodeURIComponent(id)}`, updates)
      setProject(r.data)
    } catch {
      setError('שגיאה בשמירה')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center text-blue-800">טוען...</div>
  if (error || !project) return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4">
      <p className="text-red-700">{error || 'הפרוייקט לא נמצא'}</p>
      <button onClick={() => navigate('/projects')} className="text-blue-700 underline">חזרה לפרוייקטים</button>
    </div>
  )

  const plan = project.plan || {}
  const fields = PLAN_FIELDS.filter(([key]) => plan[key] !== null && plan[key] !== undefined && plan[key] !== '')

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-blue-50 flex flex-col">
      <header className="bg-blue-900 shadow-lg">
        <div className="max-w-5xl mx-auto px-6 py-6 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white">{project.name}</h1>
            <p className="text-base text-blue-200 mt-1 font-mono">{project.plan_number}</p>
          </div>
          <button onClick={() => navigate('/projects')} className="text-sm text-blue-200 hover:text-white font-medium shrink-0">&larr; פרוייקטים</button>
        </div>
      </header>

      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-10 space-y-6">

        {/* Status + external links */}
        <section className="bg-white rounded-2xl shadow-md border border-sky-100 p-6">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-sm font-bold text-blue-900">סטטוס פרוייקט:</span>
            {STATUSES.map(s => (
              <button
                key={s}
                onClick={() => save({ status: s })}
                disabled={saving}
                className={`px-3 py-1 rounded-full border text-sm transition-colors disabled:opacity-50 ${
                  project.status === s
                    ? 'bg-blue-900 text-white border-blue-900'
                    : 'bg-white text-blue-800 border-sky-200 hover:border-sky-400'
                }`}
              >
                {s}
              </button>
            ))}
            <div className="flex-1" />
            {plan.mavat_url && (
              <a href={plan.mavat_url} target="_blank" rel="noopener noreferrer"
                 className="px-3 py-1 bg-sky-100 text-sky-800 border border-sky-200 rounded text-sm hover:bg-sky-200 transition-colors">
                מבא"ת ↗
              </a>
            )}
            {plan.sharepoint_url && (
              <a href={plan.sharepoint_url} target="_blank" rel="noopener noreferrer"
                 className="px-3 py-1 bg-green-100 text-green-800 border border-green-200 rounded text-sm hover:bg-green-200 transition-colors">
                תיקיית SharePoint ↗
              </a>
            )}
          </div>
        </section>

        {/* Documents */}
        <section className="bg-white rounded-2xl shadow-md border border-sky-100 p-6">
          <h2 className="text-xl font-bold text-blue-900 mb-4">מסמכי התוכנית</h2>
          {project.documents?.length > 0 ? (
            <ul className="space-y-2">
              {project.documents.map(d => (
                <li key={d.filename}>
                  <a
                    href={d.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 p-3 rounded-xl border border-sky-100
                               hover:bg-sky-50 hover:border-sky-300 transition-colors"
                  >
                    <span className="text-2xl">📄</span>
                    <div className="flex-1 min-w-0">
                      <p dir="ltr" className="text-blue-900 font-medium truncate text-right">{d.filename}</p>
                      <p className="text-xs text-blue-800/60">{d.kind}</p>
                    </div>
                    <span className="text-sky-600 text-sm shrink-0">פתח ↗</span>
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-blue-800/60 text-sm">אין מסמכים שהורדו לתוכנית זו</p>
          )}
        </section>

        {/* Plan details */}
        <section className="bg-white rounded-2xl shadow-md border border-sky-100 p-6">
          <h2 className="text-xl font-bold text-blue-900 mb-4">פרטי התוכנית</h2>
          {fields.length > 0 ? (
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3">
              {fields.map(([key, label]) => (
                <div key={key} className="flex gap-2 text-sm border-b border-sky-50 pb-2">
                  <dt className="text-blue-800/60 shrink-0">{label}:</dt>
                  <dd className="text-blue-900 font-medium">{String(plan[key])}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p className="text-blue-800/60 text-sm">אין פרטים נוספים במאגר</p>
          )}
          {plan.settlements?.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {plan.settlements.map(s => (
                <span key={s} className="px-2 py-0.5 bg-sky-50 text-sky-800 rounded text-xs border border-sky-100">{s}</span>
              ))}
            </div>
          )}
        </section>

        {/* Notes */}
        <section className="bg-white rounded-2xl shadow-md border border-sky-100 p-6">
          <h2 className="text-xl font-bold text-blue-900 mb-4">הערות</h2>
          <textarea
            value={notes}
            onChange={e => setNotes(e.target.value)}
            rows={5}
            placeholder="הערות על הפעילות בפרוייקט..."
            className="w-full p-3 border border-sky-200 rounded-xl text-blue-900 text-sm
                       focus:outline-none focus:border-sky-400 resize-y"
          />
          <button
            onClick={() => save({ notes })}
            disabled={saving || notes === (project.notes || '')}
            className="mt-3 px-5 py-2 bg-blue-900 text-white rounded-lg text-sm font-medium
                       hover:bg-blue-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {saving ? 'שומר...' : 'שמור הערות'}
          </button>
        </section>

      </main>
    </div>
  )
}

export default ProjectPage
