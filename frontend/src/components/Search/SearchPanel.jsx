import { useState } from 'react'
import axios from 'axios'
import AutocompleteInput from './AutocompleteInput'

function SearchPanel({ onResult, onClose }) {
  const [mode, setMode] = useState('parcel')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Parcel search fields
  const [gushNum, setGushNum] = useState('')
  const [parcelNum, setParcelNum] = useState('')

  // Address search fields
  const [selectedCity, setSelectedCity] = useState(null)
  const [cityText, setCityText] = useState('')
  const [selectedStreet, setSelectedStreet] = useState(null)
  const [streetText, setStreetText] = useState('')
  const [houseNum, setHouseNum] = useState('')

  const handleCitySelect = (item) => {
    setSelectedCity(item)
    setCityText(item.name)
    // Reset street when city changes
    setSelectedStreet(null)
    setStreetText('')
  }

  const handleStreetSelect = (item) => {
    setSelectedStreet(item)
    setStreetText(item.name)
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      let resp
      if (mode === 'parcel') {
        if (!gushNum) { setError('יש להזין מספר גוש'); setLoading(false); return }
        resp = await axios.get('/api/search/parcel', {
          params: { gush: gushNum, parcel: parcelNum || undefined },
        })
      } else {
        if (!selectedCity) { setError('יש לבחור עיר מהרשימה'); setLoading(false); return }
        if (!selectedStreet && !streetText) { setError('יש לבחור רחוב'); setLoading(false); return }
        resp = await axios.get('/api/search/address', {
          params: {
            city: selectedCity.name,
            street: selectedStreet ? selectedStreet.name : streetText,
            house: houseNum || undefined,
          },
        })
      }

      if (resp.data.error) {
        setError(resp.data.error)
      } else if (resp.data.lat && resp.data.lng) {
        onResult(resp.data)
      } else {
        setError('לא נמצאו תוצאות')
      }
    } catch {
      setError('שגיאה בחיפוש')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="absolute top-4 right-4 z-[1000] w-80 bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-sky-200">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-sky-100">
        <h3 className="text-sm font-bold text-sky-900">חיפוש</h3>
        <button onClick={onClose} className="text-sky-300 hover:text-sky-600 text-lg leading-none">
          &times;
        </button>
      </div>

      {/* Mode tabs */}
      <div className="flex border-b border-sky-100">
        <button
          onClick={() => { setMode('parcel'); setError(null) }}
          className={`flex-1 px-4 py-2 text-sm font-medium ${
            mode === 'parcel'
              ? 'text-sky-600 border-b-2 border-sky-500'
              : 'text-sky-400 hover:text-sky-600'
          }`}
        >
          גוש / חלקה
        </button>
        <button
          onClick={() => { setMode('address'); setError(null) }}
          className={`flex-1 px-4 py-2 text-sm font-medium ${
            mode === 'address'
              ? 'text-sky-600 border-b-2 border-sky-500'
              : 'text-sky-400 hover:text-sky-600'
          }`}
        >
          כתובת
        </button>
      </div>

      {/* Search form */}
      <form onSubmit={handleSearch} className="p-4 flex flex-col gap-3">
        {mode === 'parcel' ? (
          <>
            <input
              type="number"
              placeholder="מספר גוש *"
              value={gushNum}
              onChange={e => setGushNum(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <input
              type="number"
              placeholder="מספר חלקה (אופציונלי)"
              value={parcelNum}
              onChange={e => setParcelNum(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </>
        ) : (
          <>
            <AutocompleteInput
              placeholder="עיר *"
              endpoint="/api/autocomplete/cities"
              params={{}}
              value={cityText}
              onChange={(val) => {
                setCityText(val)
                if (selectedCity && val !== selectedCity.name) {
                  setSelectedCity(null)
                  setSelectedStreet(null)
                  setStreetText('')
                }
              }}
              onSelect={handleCitySelect}
            />
            <AutocompleteInput
              placeholder="רחוב *"
              endpoint="/api/autocomplete/streets"
              params={{ city_code: selectedCity?.code || '' }}
              value={streetText}
              onChange={(val) => {
                setStreetText(val)
                if (selectedStreet && val !== selectedStreet.name) {
                  setSelectedStreet(null)
                }
              }}
              onSelect={handleStreetSelect}
              disabled={!selectedCity}
            />
            <input
              type="text"
              placeholder="מספר בית (אופציונלי)"
              value={houseNum}
              onChange={e => setHouseNum(e.target.value)}
              disabled={!selectedCity}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         disabled:bg-gray-100 disabled:text-gray-400"
            />
          </>
        )}

        {error && (
          <p className="text-sm text-red-500">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 bg-sky-500 text-white text-sm font-medium rounded-lg
                     hover:bg-sky-600 disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors"
        >
          {loading ? 'מחפש...' : 'חפש'}
        </button>
      </form>
    </div>
  )
}

export default SearchPanel
