import { useNavigate } from 'react-router-dom'

function HomePage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-blue-50 flex flex-col">
      {/* Header */}
      <header className="bg-blue-900 shadow-lg">
        <div className="max-w-5xl mx-auto px-6 py-6">
          <h1 className="text-3xl font-bold text-white">Newave Land Design</h1>
          <p className="text-base text-blue-200 mt-1">מערכת מידע גושים וחלקות - ישראל</p>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 flex items-center justify-center px-6">
        <div className="max-w-5xl w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

          {/* Interactive Map */}
          <button
            onClick={() => navigate('/map')}
            className="group bg-white rounded-2xl shadow-md border border-sky-100 p-10
                       hover:shadow-xl hover:border-sky-300 hover:-translate-y-1
                       transition-all duration-300
                       flex flex-col items-center gap-5 text-center"
          >
            <div className="w-20 h-20 bg-sky-50 rounded-2xl flex items-center justify-center
                            group-hover:bg-sky-100 transition-colors duration-300">
              <svg className="w-10 h-10 text-sky-500 group-hover:text-sky-600 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-blue-900">מפה אינטראקטיבית</h2>
            <p className="text-base text-blue-800 leading-relaxed">
              צפייה בגושים וחלקות על גבי מפה, חיפוש לפי כתובת או גוש/חלקה
            </p>
          </button>

          {/* Databases */}
          <button
            onClick={() => navigate('/databases')}
            className="group bg-white rounded-2xl shadow-md border border-sky-100 p-10
                       hover:shadow-xl hover:border-sky-300 hover:-translate-y-1
                       transition-all duration-300
                       flex flex-col items-center gap-5 text-center"
          >
            <div className="w-20 h-20 bg-sky-50 rounded-2xl flex items-center justify-center
                            group-hover:bg-sky-100 transition-colors duration-300">
              <svg className="w-10 h-10 text-sky-500 group-hover:text-sky-600 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-blue-900">בסיסי נתונים</h2>
            <p className="text-base text-blue-800 leading-relaxed">
              גישה לבסיסי נתונים קיימים - גושים, חלקות, רחובות ועוד
            </p>
          </button>

          {/* Committees */}
          <button
            onClick={() => navigate('/committees')}
            className="group bg-white rounded-2xl shadow-md border border-sky-100 p-10
                       hover:shadow-xl hover:border-sky-300 hover:-translate-y-1
                       transition-all duration-300
                       flex flex-col items-center gap-5 text-center"
          >
            <div className="w-20 h-20 bg-sky-50 rounded-2xl flex items-center justify-center
                            group-hover:bg-sky-100 transition-colors duration-300">
              <svg className="w-10 h-10 text-sky-500 group-hover:text-sky-600 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0012 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-blue-900">ועדות מקומיות ומחוזיות</h2>
            <p className="text-base text-blue-800 leading-relaxed">
              הפקת נתונים מוועדות מקומיות ומוועדות מחוזיות
            </p>
          </button>

          {/* Parking Devices */}
          <button
            onClick={() => navigate('/parking-devices')}
            className="group bg-white rounded-2xl shadow-md border border-sky-100 p-10
                       hover:shadow-xl hover:border-sky-300 hover:-translate-y-1
                       transition-all duration-300
                       flex flex-col items-center gap-5 text-center"
          >
            <div className="w-20 h-20 bg-sky-50 rounded-2xl flex items-center justify-center
                            group-hover:bg-sky-100 transition-colors duration-300">
              <svg className="w-10 h-10 text-sky-500 group-hover:text-sky-600 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 00-3.213-9.193 2.056 2.056 0 00-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 00-10.026 0 1.106 1.106 0 00-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-blue-900">מתקני חניה בבניינים</h2>
            <p className="text-base text-blue-800 leading-relaxed">
              בניינים עם מתקני חניה מכניים - מתוך פרוטוקולי ועדות תכנון
            </p>
          </button>

        </div>
      </main>

      {/* Footer */}
      <footer className="py-4 text-center text-sm text-blue-900/40">
        Newave Land Design &copy; {new Date().getFullYear()}
      </footer>
    </div>
  )
}

export default HomePage
