import { useState, useEffect } from 'react'
import axios from 'axios'

const EMPTY_FORM = { competitor_name: '', device_type: '', customer: '', address: '', city: '', notes: '' }

function CompetitorParkingTable() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)

  const fetchData = async () => {
    setLoading(true)
    try {
      const resp = await axios.get('/api/parking/competitors')
      setData(resp.data)
    } catch {
      // No data yet
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await axios.post('/api/parking/competitors', form)
      setForm(EMPTY_FORM)
      setShowForm(false)
      await fetchData()
    } catch (err) {
      alert('שגיאה בשמירה')
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('למחוק רשומה זו?')) return
    try {
      await axios.delete(`/api/parking/competitors/${id}`)
      await fetchData()
    } catch {
      alert('שגיאה במחיקה')
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
          <h2 className="text-lg font-bold text-blue-900">מתקני מתחרים</h2>
          <p className="text-sm text-blue-800/60">הזנה ידנית</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-5 py-2 bg-sky-500 text-white text-base font-medium rounded-lg
                     hover:bg-sky-600 transition-colors flex items-center gap-2"
        >
          {showForm ? 'ביטול' : '+ הוסף מתקן'}
        </button>
      </div>

      {/* Add form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="px-6 py-4 border-b border-sky-100 bg-sky-50/50">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
            <input
              placeholder="שם מתחרה *"
              value={form.competitor_name}
              onChange={e => setForm({ ...form, competitor_name: e.target.value })}
              required
              className="px-3 py-2 border border-sky-200 rounded-lg text-base text-blue-900
                         focus:outline-none focus:ring-2 focus:ring-sky-400"
            />
            <input
              placeholder="סוג מתקן *"
              value={form.device_type}
              onChange={e => setForm({ ...form, device_type: e.target.value })}
              required
              className="px-3 py-2 border border-sky-200 rounded-lg text-base text-blue-900
                         focus:outline-none focus:ring-2 focus:ring-sky-400"
            />
            <input
              placeholder="לקוח"
              value={form.customer}
              onChange={e => setForm({ ...form, customer: e.target.value })}
              className="px-3 py-2 border border-sky-200 rounded-lg text-base text-blue-900
                         focus:outline-none focus:ring-2 focus:ring-sky-400"
            />
            <input
              placeholder="כתובת *"
              value={form.address}
              onChange={e => setForm({ ...form, address: e.target.value })}
              required
              className="px-3 py-2 border border-sky-200 rounded-lg text-base text-blue-900
                         focus:outline-none focus:ring-2 focus:ring-sky-400"
            />
            <input
              placeholder="עיר *"
              value={form.city}
              onChange={e => setForm({ ...form, city: e.target.value })}
              required
              className="px-3 py-2 border border-sky-200 rounded-lg text-base text-blue-900
                         focus:outline-none focus:ring-2 focus:ring-sky-400"
            />
            <input
              placeholder="הערות"
              value={form.notes}
              onChange={e => setForm({ ...form, notes: e.target.value })}
              className="px-3 py-2 border border-sky-200 rounded-lg text-base text-blue-900
                         focus:outline-none focus:ring-2 focus:ring-sky-400"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-2 bg-blue-900 text-white text-base font-medium rounded-lg
                       hover:bg-blue-800 transition-colors"
          >
            שמור
          </button>
        </form>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-base">
          <thead className="bg-sky-50">
            <tr>
              <th className="px-4 py-3 text-right font-bold text-blue-900">מתחרה</th>
              <th className="px-4 py-3 text-right font-bold text-blue-900">סוג מתקן</th>
              <th className="px-4 py-3 text-right font-bold text-blue-900">לקוח</th>
              <th className="px-4 py-3 text-right font-bold text-blue-900">כתובת</th>
              <th className="px-4 py-3 text-right font-bold text-blue-900">עיר</th>
              <th className="px-4 py-3 text-right font-bold text-blue-900">הערות</th>
              <th className="px-4 py-3 w-16"></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="7" className="px-4 py-8 text-center text-blue-800/50">טוען...</td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan="7" className="px-4 py-8 text-center text-blue-800/50">
                  אין נתונים. לחץ "+ הוסף מתקן" להזנת מתקן מתחרה.
                </td>
              </tr>
            ) : (
              data.map((item, i) => (
                <tr key={item.id || i} className="border-t border-sky-50 hover:bg-sky-50/50">
                  <td className="px-4 py-3 text-blue-900">{item.competitor_name}</td>
                  <td className="px-4 py-3 text-blue-900">{item.device_type}</td>
                  <td className="px-4 py-3 text-blue-900">{item.customer}</td>
                  <td className="px-4 py-3 text-blue-900">{item.address}</td>
                  <td className="px-4 py-3 text-blue-900">{item.city}</td>
                  <td className="px-4 py-3 text-blue-800/60">{item.notes}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleDelete(item.id)}
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

      {data.length > 0 && (
        <div className="px-6 py-3 border-t border-sky-100 text-sm text-blue-800/50">
          סה"כ {data.length} מתקנים
        </div>
      )}
    </div>
  )
}

export default CompetitorParkingTable
