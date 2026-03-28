import { useState, useEffect } from 'react'
import axios from 'axios'

function OurParkingTable() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const resp = await axios.get('/api/parking/ours')
      setData(resp.data)
    } catch {
      // No data yet
    } finally {
      setLoading(false)
    }
  }

  const handleSync = async () => {
    setSyncing(true)
    try {
      await axios.post('/api/parking/sync', null, { timeout: 300000 })
      await fetchData()
    } catch (err) {
      alert('שגיאה בסנכרון: ' + (err.response?.data?.detail || err.message))
    } finally {
      setSyncing(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  return (
    <div className="bg-white rounded-2xl shadow-md border border-sky-100 overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-sky-100">
        <div>
          <h2 className="text-lg font-bold text-blue-900">מתקני חניה - החברה</h2>
          <p className="text-sm text-blue-800/60">מקור: פריוריטי - מכשירים</p>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="px-5 py-2 bg-sky-500 text-white text-base font-medium rounded-lg
                     hover:bg-sky-600 disabled:opacity-50 transition-colors flex items-center gap-2"
        >
          <svg className={`w-5 h-5 ${syncing ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182M2.985 19.644l3.181-3.182" />
          </svg>
          {syncing ? 'מסנכרן...' : 'סנכרון מפריוריטי'}
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-base">
          <thead className="bg-sky-50">
            <tr>
              <th className="px-4 py-3 text-right font-bold text-blue-900">מס' אתר</th>
              <th className="px-4 py-3 text-right font-bold text-blue-900">תיאור אתר</th>
              <th className="px-4 py-3 text-right font-bold text-blue-900">משפחת מוצר</th>
              <th className="px-4 py-3 text-right font-bold text-blue-900">תיאור מוצר</th>
              <th className="px-4 py-3 text-right font-bold text-blue-900">כמות</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="5" className="px-4 py-8 text-center text-blue-800/50">טוען...</td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-4 py-8 text-center text-blue-800/50">
                  אין נתונים. לחץ "סנכרון מפריוריטי" לייבוא ראשוני.
                </td>
              </tr>
            ) : (
              data.map((item, i) => (
                <tr key={item.site_name || i} className="border-t border-sky-50 hover:bg-sky-50/50">
                  <td className="px-4 py-3 text-blue-900 font-mono text-sm">{item.site_code || '-'}</td>
                  <td className="px-4 py-3 text-blue-900">{item.site_name}</td>
                  <td className="px-4 py-3 text-blue-900">{item.family}</td>
                  <td className="px-4 py-3 text-blue-900 text-sm">{item.product}</td>
                  <td className="px-4 py-3 text-blue-900 text-center">{item.count}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {data.length > 0 && (
        <div className="px-6 py-3 border-t border-sky-100 text-sm text-blue-800/50">
          סה"כ {data.length} מתקנים
        </div>
      )}
    </div>
  )
}

export default OurParkingTable
