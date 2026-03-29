import { useNavigate } from 'react-router-dom'

const DATABASES = [
  {
    id: 'blocks',
    name: 'גושים',
    description: '18,656 גושי רישום בישראל',
    records: '18,656',
    source: 'רשות המקרקעין',
  },
  {
    id: 'parcels',
    name: 'חלקות',
    description: '1,094,533 חלקות רישום בישראל',
    records: '1,094,533',
    source: 'רשות המקרקעין',
  },
  {
    id: 'streets',
    name: 'רחובות',
    description: '63,438 רחובות בכל יישובי ישראל',
    records: '63,438',
    source: 'data.gov.il',
  },
]

const DB_ICONS = {
  blocks: (
    <svg className="w-8 h-8 text-sky-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
    </svg>
  ),
  parcels: (
    <svg className="w-8 h-8 text-sky-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  ),
  streets: (
    <svg className="w-8 h-8 text-sky-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
    </svg>
  ),
}

function DatabasesPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-blue-50">
      {/* Header */}
      <header className="bg-blue-900 shadow-lg">
        <div className="max-w-5xl mx-auto px-6 py-6 flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="text-base text-blue-200 hover:text-white font-medium"
          >
            &larr; דף הבית
          </button>
          <div className="border-r border-blue-700 h-6" />
          <div>
            <h1 className="text-2xl font-bold text-white">בסיסי נתונים</h1>
            <p className="text-base text-blue-200">נתונים מקומיים זמינים במערכת</p>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* Parking - featured card */}
        <button
          onClick={() => navigate('/parking')}
          className="w-full mb-8 group bg-white rounded-2xl shadow-md border border-sky-100 p-8
                     hover:shadow-xl hover:border-sky-300 hover:-translate-y-1
                     transition-all duration-300 text-right"
        >
          <div className="flex items-center gap-5">
            <div className="w-16 h-16 bg-sky-50 rounded-2xl flex items-center justify-center flex-shrink-0
                            group-hover:bg-sky-100 transition-colors duration-300">
              <svg className="w-9 h-9 text-sky-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 00-3.213-9.193 2.056 2.056 0 00-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 00-10.026 0 1.106 1.106 0 00-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" />
              </svg>
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-blue-900">מתקני חניה</h2>
              <p className="text-base text-blue-800 mt-1">
                ניהול מתקני חניה של החברה (מפריוריטי) ומיפוי מתקני מתחרים
              </p>
            </div>
            <svg className="w-6 h-6 text-sky-400 group-hover:text-sky-600 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
          </div>
        </button>

        {/* Chargers card */}
        <button
          onClick={() => navigate('/chargers')}
          className="w-full mb-8 group bg-white rounded-2xl shadow-md border border-sky-100 p-8
                     hover:shadow-xl hover:border-sky-300 hover:-translate-y-1
                     transition-all duration-300 text-right"
        >
          <div className="flex items-center gap-5">
            <div className="w-16 h-16 bg-sky-50 rounded-2xl flex items-center justify-center flex-shrink-0
                            group-hover:bg-sky-100 transition-colors duration-300">
              <svg className="w-9 h-9 text-sky-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
              </svg>
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-blue-900">מטענים</h2>
              <p className="text-base text-blue-800 mt-1">
                ניהול מטעני AC - קיבוץ לפי אתר (מפריוריטי)
              </p>
            </div>
            <svg className="w-6 h-6 text-sky-400 group-hover:text-sky-600 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
          </div>
        </button>

        {/* Energy companies card */}
        <button
          onClick={() => navigate('/energy-companies')}
          className="w-full mb-8 group bg-white rounded-2xl shadow-md border border-sky-100 p-8
                     hover:shadow-xl hover:border-sky-300 hover:-translate-y-1
                     transition-all duration-300 text-right"
        >
          <div className="flex items-center gap-5">
            <div className="w-16 h-16 bg-sky-50 rounded-2xl flex items-center justify-center flex-shrink-0
                            group-hover:bg-sky-100 transition-colors duration-300">
              <svg className="w-9 h-9 text-sky-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
              </svg>
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-blue-900">חברות אנרגיה וטעינה</h2>
              <p className="text-base text-blue-800 mt-1">
                חיפוש ומיפוי חברות טעינת רכבים חשמליים וניהול אנרגיה בבניינים
              </p>
            </div>
            <svg className="w-6 h-6 text-sky-400 group-hover:text-sky-600 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
          </div>
        </button>

        {/* Other databases */}
        <h3 className="text-lg font-bold text-blue-900 mb-4">נתוני מקרקעין</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {DATABASES.map((db) => (
            <div
              key={db.id}
              className="bg-white rounded-2xl shadow-md border border-sky-100 p-6
                         hover:shadow-lg hover:border-sky-200 transition-all duration-200
                         flex flex-col gap-3"
            >
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-sky-50 rounded-xl flex items-center justify-center">
                  {DB_ICONS[db.id]}
                </div>
                <h2 className="text-lg font-bold text-blue-900">{db.name}</h2>
              </div>
              <p className="text-base text-blue-800">{db.description}</p>
              <div className="mt-auto pt-3 border-t border-sky-50 flex justify-between text-sm text-blue-800/50">
                <span>רשומות: {db.records}</span>
                <span>מקור: {db.source}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Sync info */}
        <div className="mt-8 bg-white rounded-2xl shadow-md border border-sky-100 p-6">
          <div className="flex items-center gap-3 mb-2">
            <svg className="w-5 h-5 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182M2.985 19.644l3.181-3.182" />
            </svg>
            <h3 className="text-base font-bold text-blue-900">סנכרון נתונים</h3>
          </div>
          <p className="text-base text-blue-800">
            הנתונים נשמרים מקומית ומתעדכנים מ-data.gov.il.
            סנכרון אחרון: מרץ 2026
          </p>
        </div>
      </main>
    </div>
  )
}

export default DatabasesPage
