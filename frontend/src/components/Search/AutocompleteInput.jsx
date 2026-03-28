import { useState, useRef, useEffect } from 'react'
import axios from 'axios'

function AutocompleteInput({ placeholder, endpoint, params, onSelect, value, onChange, disabled }) {
  const [suggestions, setSuggestions] = useState([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [inputValue, setInputValue] = useState(value || '')
  const debounceRef = useRef(null)
  const wrapperRef = useRef(null)

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  // Sync external value
  useEffect(() => {
    setInputValue(value || '')
  }, [value])

  const fetchSuggestions = async (query) => {
    if (!query || query.length < 1) {
      setSuggestions([])
      setShowDropdown(false)
      return
    }

    try {
      const resp = await axios.get(endpoint, {
        params: { ...params, q: query },
      })
      setSuggestions(resp.data)
      setShowDropdown(resp.data.length > 0)
    } catch {
      setSuggestions([])
    }
  }

  const handleChange = (e) => {
    const val = e.target.value
    setInputValue(val)
    if (onChange) onChange(val)

    // Debounce API calls
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => fetchSuggestions(val), 200)
  }

  const handleSelect = (item) => {
    setInputValue(item.name)
    setShowDropdown(false)
    setSuggestions([])
    if (onSelect) onSelect(item)
  }

  return (
    <div ref={wrapperRef} className="relative">
      <input
        type="text"
        placeholder={placeholder}
        value={inputValue}
        onChange={handleChange}
        onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
        disabled={disabled}
        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                   disabled:bg-gray-100 disabled:text-gray-400"
      />

      {showDropdown && (
        <ul className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg
                       max-h-48 overflow-y-auto">
          {suggestions.map((item, i) => (
            <li
              key={item.code || i}
              onClick={() => handleSelect(item)}
              className="px-3 py-2 text-sm text-gray-700 cursor-pointer
                         hover:bg-blue-50 hover:text-blue-700"
            >
              {item.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default AutocompleteInput
