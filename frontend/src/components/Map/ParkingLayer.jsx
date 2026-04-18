import { useEffect, useRef } from 'react'
import L from 'leaflet'

function createPinIcon(color) {
  return L.divIcon({
    html: `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="30" viewBox="0 0 22 30">
      <path d="M11 0C5.477 0 1 4.477 1 10c0 7.5 10 20 10 20S21 17.5 21 10C21 4.477 16.523 0 11 0z"
            fill="${color}" stroke="white" stroke-width="1.5"/>
      <circle cx="11" cy="10" r="4" fill="white" opacity="0.9"/>
    </svg>`,
    className: '',
    iconSize: [22, 30],
    iconAnchor: [11, 30],
  })
}

function ParkingLayer({ map, visible, cityKey, color, onBuildingClick }) {
  const layerRef = useRef(null)
  const colorRef = useRef(color)

  useEffect(() => { colorRef.current = color }, [color])

  useEffect(() => {
    if (!map) return
    if (layerRef.current) { map.removeLayer(layerRef.current); layerRef.current = null }
    if (!visible) return

    const group = L.layerGroup()

    fetch(`/api/parking-devices/results?city=${cityKey}`)
      .then(r => r.json())
      .then(buildings => {
        buildings.forEach(b => {
          if (!b.lat || !b.lng) return
          const marker = L.marker([b.lat, b.lng], { icon: createPinIcon(colorRef.current) })
          marker.on('click', (e) => {
            const rect = map.getContainer().getBoundingClientRect()
            const pt = map.latLngToContainerPoint([b.lat, b.lng])
            onBuildingClick?.({
              building: b,
              pos: {
                top: Math.min(pt.y + rect.top + 10, window.innerHeight - 320),
                left: Math.min(pt.x + rect.left + 10, window.innerWidth - 280),
              },
            })
            L.DomEvent.stopPropagation(e)
          })
          group.addLayer(marker)
        })
        group.addTo(map)
        layerRef.current = group
      })
      .catch(console.error)

    return () => {
      if (layerRef.current) { map.removeLayer(layerRef.current); layerRef.current = null }
    }
  }, [map, visible, cityKey])

  // Update icon color without refetching
  useEffect(() => {
    if (!layerRef.current) return
    const icon = createPinIcon(color)
    layerRef.current.eachLayer(m => { if (m.setIcon) m.setIcon(icon) })
  }, [color])

  return null
}

export default ParkingLayer
