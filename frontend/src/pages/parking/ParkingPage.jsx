import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import OurParkingTable from './OurParkingTable'
import CompetitorParkingTable from './CompetitorParkingTable'

function ParkingPage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('ours')

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-blue-50">
      {/* Header */}
      <header className="bg-blue-900 shadow-lg">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center gap-4">
          <button
            onClick={() => navigate('/databases')}
            className="text-base text-blue-200 hover:text-white font-medium"
          >
            &larr; בסיסי נתונים
          </button>
          <div className="border-r border-blue-700 h-6" />
          <div>
            <h1 className="text-2xl font-bold text-white">מתקני חניה</h1>
            <p className="text-base text-blue-200">ניהול מתקני חניה - החברה ומתחרים</p>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Tabs */}
        <div className="flex gap-1 bg-blue-900/10 rounded-xl p-1 mb-6">
          <button
            onClick={() => setActiveTab('ours')}
            className={`flex-1 py-3 px-6 rounded-lg text-base font-medium transition-all duration-200
                       ${activeTab === 'ours'
                         ? 'bg-white text-blue-900 shadow-md'
                         : 'text-blue-800 hover:bg-white/50'
                       }`}
          >
            מתקני החברה (פריוריטי)
          </button>
          <button
            onClick={() => setActiveTab('competitors')}
            className={`flex-1 py-3 px-6 rounded-lg text-base font-medium transition-all duration-200
                       ${activeTab === 'competitors'
                         ? 'bg-white text-blue-900 shadow-md'
                         : 'text-blue-800 hover:bg-white/50'
                       }`}
          >
            מתקני מתחרים
          </button>
        </div>

        {/* Content */}
        {activeTab === 'ours' ? <OurParkingTable /> : <CompetitorParkingTable />}
      </main>
    </div>
  )
}

export default ParkingPage
