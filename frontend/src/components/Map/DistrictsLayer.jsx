import { useEffect, useRef } from 'react'
import L from 'leaflet'
import axios from 'axios'

// Colors for each district
const DISTRICT_COLORS = {
  'מחוז צפון': '#16a34a',
  'מחוז חיפה': '#2563eb',
  'מחוז מרכז': '#9333ea',
  'מחוז תל אביב': '#dc2626',
  'מחוז ירושלים': '#d97706',
  'מחוז הדרום': '#0891b2',
}

function DistrictsLayer({ map, visible }) {
  const layerRef = useRef(null)

  useEffect(() => {
    if (!map) return

    if (visible && !layerRef.current) {
      axios.get('/api/committees/districts-geojson').then(resp => {
        const layer = L.geoJSON(resp.data, {
          style: (feature) => {
            const name = feature.properties.name_he || ''
            const color = DISTRICT_COLORS[name] || '#6b7280'
            return {
              color: color,
              weight: 2.5,
              fillColor: color,
              fillOpacity: 0.12,
              opacity: 0.8,
            }
          },
          onEachFeature: (feature, layer) => {
            const name = feature.properties.name_he || ''
            layer.bindTooltip(name, {
              permanent: true,
              direction: 'center',
              className: 'district-label',
            })
          },
        })
        layer.addTo(map)
        layerRef.current = layer
      })
    }

    if (!visible && layerRef.current) {
      map.removeLayer(layerRef.current)
      layerRef.current = null
    }
  }, [map, visible])

  useEffect(() => {
    return () => {
      if (layerRef.current && map) {
        map.removeLayer(layerRef.current)
      }
    }
  }, [map])

  return null
}

export default DistrictsLayer
