import { useNavigate } from 'react-router-dom'
import MapView from '../components/Map/MapView'

function MapPage() {
  const navigate = useNavigate()

  return (
    <div className="w-full h-full relative">
      <MapView />

      {/* Back to home button */}
      <button
        onClick={() => navigate('/')}
        className="absolute bottom-4 left-4 z-[1000] px-4 py-2 bg-white/90 backdrop-blur-sm rounded-lg shadow-md
                   border border-sky-200 text-sm text-sky-700 hover:bg-sky-50 transition-colors"
      >
        ← דף הבית
      </button>
    </div>
  )
}

export default MapPage
