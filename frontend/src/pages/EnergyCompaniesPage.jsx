import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

function EnergyCompaniesPage() {
  const navigate = useNavigate()
  const [companies, setCompanies] = useState([])
  const [loading, setLoading] = useState(false)
  const [searching, setSearching] = useState(false)
  const [searchQuery, setSearchQuery] = useState('חברות טעינת רכבים חשמליים בניין מגורים ישראל')
  const [lastSearch, setLastSearch] = useState(null)

  const fetchCompanies = async () => {
    setLoading(true)
    try {
      const resp = await axios.get('/api/energy-companies')
      setCompanies(resp.data)
    } catch {}
    setLoading(false)
  }

  const handleSearch = async () => {
    setSearching(true)
    try {
      const resp = await axios.post('/api/energy-companies/search', {
        query: searchQuery,
      }, { timeout: 120000 })
      setLastSearch(resp.data)
      await fetchCompanies()
    } catch (err) {
      alert('שגיאה בחיפוש: ' + (err.response?.data?.detail || err.message))
    }
    setSearching(false)
  }

  const handleDelete = async (id) => {
    if (!confirm('למחוק חברה זו?')) return
    try {
      await axios.delete(`/api/energy-companies/${id}`)
      await fetchCompanies()
    } catch {}
  }

  useEffect(() => {
    fetchCompanies()
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-blue-50">
      {/* Header */}
      <header className="bg-blue-900 shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-6 flex items-center gap-4">
          <button
            onClick={() => navigate('/databases')}
            className="text-base text-blue-200 hover:text-white font-medium"
          >
            &larr; בסיסי נתונים
          </button>
          <div className="border-r border-blue-700 h-6" />
          <div>
            <h1 className="text-2xl font-bold text-white">חברות אנרגיה וטעינה</h1>
            <p className="text-base text-blue-200">חברות טעינת רכבים חשמליים וניהול אנרגיה</p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Search section */}
        <div className="bg-white rounded-2xl shadow-md border border-sky-100 p-6 mb-6">
          <h2 className="text-lg font-bold text-blue-900 mb-3">חיפוש חברות</h2>
          <div className="flex gap-3">
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="הזן מילות חיפוש..."
              className="flex-1 px-4 py-2 border border-sky-200 rounded-lg text-base text-blue-900
                         focus:outline-none focus:ring-2 focus:ring-sky-400"
            />
            <button
              onClick={handleSearch}
              disabled={searching}
              className="px-6 py-2 bg-sky-500 text-white text-base font-medium rounded-lg
                         hover:bg-sky-600 disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              {searching ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  מחפש...
                </>
              ) : 'חפש באינטרנט'}
            </button>
          </div>
          {lastSearch && (
            <p className="mt-3 text-sm text-blue-800/60">
              נמצאו {lastSearch.found} חברות חדשות מתוך {lastSearch.results} תוצאות
            </p>
          )}
        </div>

        {/* Companies table */}
        <div className="bg-white rounded-2xl shadow-md border border-sky-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-sky-100 flex items-center justify-between">
            <h2 className="text-lg font-bold text-blue-900">
              רשימת חברות ({companies.length})
            </h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-base">
              <thead className="bg-sky-50">
                <tr>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">שם החברה</th>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">אתר</th>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">תחום פעילות</th>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">תיאור</th>
                  <th className="px-4 py-3 text-right font-bold text-blue-900">מקור</th>
                  <th className="px-4 py-3 w-16"></th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="6" className="px-4 py-8 text-center text-blue-800/50">טוען...</td>
                  </tr>
                ) : companies.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-4 py-8 text-center text-blue-800/50">
                      אין חברות. לחץ "חפש באינטרנט" למציאת חברות.
                    </td>
                  </tr>
                ) : (
                  companies.map((c) => (
                    <tr key={c.id} className="border-t border-sky-50 hover:bg-sky-50/50">
                      <td className="px-4 py-3 text-blue-900 font-medium">{c.name}</td>
                      <td className="px-4 py-3">
                        {c.website ? (
                          <a
                            href={c.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sky-600 hover:text-sky-800 underline text-sm"
                          >
                            {c.website.replace(/^https?:\/\/(www\.)?/, '').split('/')[0]}
                          </a>
                        ) : '-'}
                      </td>
                      <td className="px-4 py-3">
                        {c.category && (
                          <span className="px-2 py-1 bg-sky-50 rounded-md text-sm text-sky-700">
                            {c.category}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-blue-800 text-sm max-w-md">{c.description || '-'}</td>
                      <td className="px-4 py-3 text-blue-800/40 text-sm">{c.source || '-'}</td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => handleDelete(c.id)}
                          className="text-red-400 hover:text-red-600 text-sm"
                        >
                          מחק
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  )
}

export default EnergyCompaniesPage
