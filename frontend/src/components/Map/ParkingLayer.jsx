import { useEffect, useRef } from 'react'
import L from 'leaflet'

function ParkingLayer({ map, visible, cityKey, color }) {
  const layerRef = useRef(null)

  useEffect(() => {
    if (!map) return

    // Cleanup previous layer
    if (layerRef.current) {
      map.removeLayer(layerRef.current)
      layerRef.current = null
    }

    if (!visible) return

    const group = L.layerGroup()

    fetch(`/api/parking-devices/results?city=${cityKey}`)
      .then(r => r.json())
      .then(buildings => {
        buildings.forEach(b => {
          if (!b.lat || !b.lng) return

          const marker = L.circleMarker([b.lat, b.lng], {
            radius: 7,
            fillColor: color,
            color: '#fff',
            weight: 1.5,
            opacity: 1,
            fillOpacity: 0.85,
          })

          const deviceInfo = b.device_types
            ? (Array.isArray(b.device_types) ? b.device_types.join(', ') : b.device_types)
            : (b.device_type || '')

          const popup = `
            <div style="direction:rtl;font-family:sans-serif;min-width:200px">
              <div style="font-weight:700;font-size:13px;color:#1e3a5f;margin-bottom:4px">${b.address || ''}</div>
              ${b.city ? `<div style="font-size:11px;color:#666;margin-bottom:3px">${b.city}</div>` : ''}
              ${deviceInfo ? `<div style="font-size:11px;margin-bottom:2px"><span style="color:#888">מתקן: </span>${deviceInfo}</div>` : ''}
              ${b.parking_count ? `<div style="font-size:11px;margin-bottom:2px"><span style="color:#888">חניות: </span><strong>${b.parking_count}</strong></div>` : ''}
              ${b.gush ? `<div style="font-size:11px;color:#888">גוש ${b.gush}${b.helka ? ` חלקה ${b.helka}` : ''}</div>` : ''}
              ${b.description ? `<div style="font-size:10px;color:#555;margin-top:4px;border-top:1px solid #eee;padding-top:3px;max-width:220px">${b.description.substring(0, 180)}${b.description.length > 180 ? '...' : ''}</div>` : ''}
            </div>
          `
          marker.bindPopup(popup)
          group.addLayer(marker)
        })
        group.addTo(map)
      })
      .catch(console.error)

    layerRef.current = group

    return () => {
      if (layerRef.current) {
        map.removeLayer(layerRef.current)
        layerRef.current = null
      }
    }
  }, [map, visible, cityKey, color])

  return null
}

export default ParkingLayer
