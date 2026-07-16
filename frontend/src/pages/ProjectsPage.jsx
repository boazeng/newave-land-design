import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const STATUS_COLORS = {
  'פעיל': 'bg-green-100 text-green-800 border-green-200',
  'בהמתנה': 'bg-amber-100 text-amber-800 border-amber-200',
  'הושלם': 'bg-gray-100 text-gray-700 border-gray-200',
}

function ProjectsPage() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    axios.get('/api/projects')
      .then(r => setProjects(r.data || []))
      .catch(() => setError('שגיאה בטעינת הפרוייקטים'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-blue-50 flex flex-col">
      <header className="bg-blue-900 shadow-lg">
        <div className="max-w-5xl mx-auto px-6 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">פרוייקטים</h1>
            <p className="text-base text-blue-200 mt-1">ניהול פעילות שוטפת על תוכניות</p>
          </div>
          <button onClick={() => navigate('/')} className="text-sm text-blue-200 hover:text-white font-medium">&larr; דף הבית</button>
        </div>
      </header>

      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-10">
        {loading && <p className="text-blue-800 text-center">טוען...</p>}
        {error && <p className="text-red-700 text-center">{error}</p>}

        {!loading && !error && projects.length === 0 && (
          <p className="text-blue-800/60 text-center">אין פרוייקטים עדיין</p>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {projects.map(p => (
            <button
              key={p.id}
              onClick={() => navigate(`/projects/${encodeURIComponent(p.id)}`)}
              className="group bg-white rounded-2xl shadow-md border border-sky-100 p-6 text-right
                         hover:shadow-xl hover:border-sky-300 hover:-translate-y-1 transition-all duration-300"
            >
              <div className="flex items-start justify-between gap-3">
                <h2 className="text-lg font-bold text-blue-900 group-hover:text-blue-700">{p.name}</h2>
                <span className={`shrink-0 px-2 py-0.5 rounded border text-xs ${STATUS_COLORS[p.status] || STATUS_COLORS['הושלם']}`}>
                  {p.status}
                </span>
              </div>
              <p className="text-sm text-blue-800/70 mt-1 font-mono">{p.plan_number}</p>
              {p.plan && (
                <p className="text-sm text-blue-800 mt-3 leading-relaxed">{p.plan.status}</p>
              )}
              {p.plan_missing && (
                <p className="text-sm text-red-700 mt-3">התוכנית לא נמצאה במאגר</p>
              )}
              <div className="flex items-center gap-3 mt-4 text-xs text-blue-800/60">
                <span>📄 {p.documents?.length || 0} מסמכים</span>
                {p.plan?.settlements?.length > 0 && <span>· {p.plan.settlements.join(', ')}</span>}
              </div>
            </button>
          ))}
        </div>
      </main>
    </div>
  )
}

export default ProjectsPage
