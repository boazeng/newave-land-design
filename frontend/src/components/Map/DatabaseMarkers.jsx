import { useEffect, useRef } from 'react'
import L from 'leaflet'
import axios from 'axios'

const ENDPOINTS = {
  parking: '/api/parking/ours',
  chargers: '/api/chargers/sites',
}

// Create colored SVG marker icon - larger sizes
function createMarkerIcon(markerStyle) {
  const color = markerStyle.color
  const type = markerStyle.id

  if (type === 'car-green') {
    const carSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40">
      <circle cx="20" cy="20" r="19" fill="white" stroke="${color}" stroke-width="2"/>
      <g transform="translate(8,10) scale(0.055)">
        <path fill="${color}" d="M435.6 73.7c-7.2-18.4-24.8-30.7-44.4-30.7H176.8c-19.6 0-37.2 12.3-44.4 30.7L88 199.3C56.5 215.4 36 248.4 36 285.3v98.7c0 17.7 14.3 32 32 32h16c17.7 0 32-14.3 32-32v-32h336v32c0 17.7 14.3 32 32 32h16c17.7 0 32-14.3 32-32v-98.7c0-36.9-20.5-69.9-52-86L435.6 73.7zM152 311.3c-17.7 0-32-14.3-32-32s14.3-32 32-32s32 14.3 32 32S169.7 311.3 152 311.3zm264 0c-17.7 0-32-14.3-32-32s14.3-32 32-32s32 14.3 32 32S433.7 311.3 416 311.3zM155.2 171.3l27.2-68c2.4-6.1 8.3-10.3 14.8-10.3h173.6c6.5 0 12.4 4.2 14.8 10.3l27.2 68H155.2z"/>
      </g>
    </svg>`
    return L.divIcon({
      className: '',
      html: `<div style="filter:drop-shadow(0 2px 4px rgba(0,0,0,0.3))">${carSvg}</div>`,
      iconSize: [40, 40],
      iconAnchor: [20, 20],
      popupAnchor: [0, -22],
    })
  }

  if (type.startsWith('circle')) {
    return L.divIcon({
      className: '',
      html: `<div style="width:22px;height:22px;border-radius:50%;background:${color};border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.4)"></div>`,
      iconSize: [22, 22],
      iconAnchor: [11, 11],
      popupAnchor: [0, -14],
    })
  }

  if (type === 'star') {
    return L.divIcon({
      className: '',
      html: `<div style="font-size:32px;filter:drop-shadow(0 2px 3px rgba(0,0,0,0.3))">⭐</div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
      popupAnchor: [0, -18],
    })
  }

  if (type === 'square') {
    return L.divIcon({
      className: '',
      html: `<div style="width:20px;height:20px;background:${color};border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.4);border-radius:3px"></div>`,
      iconSize: [20, 20],
      iconAnchor: [10, 10],
      popupAnchor: [0, -12],
    })
  }

  // Default: pin marker - larger
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 36" width="36" height="54">
    <path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 24 12 24s12-15 12-24C24 5.4 18.6 0 12 0z" fill="${color}" stroke="white" stroke-width="1.5"/>
    <circle cx="12" cy="12" r="5" fill="white"/>
  </svg>`

  return L.divIcon({
    className: '',
    html: `<div style="filter:drop-shadow(0 3px 4px rgba(0,0,0,0.35))">${svg}</div>`,
    iconSize: [36, 54],
    iconAnchor: [18, 54],
    popupAnchor: [0, -54],
  })
}

function DatabaseMarkers({ map, dbId, markerStyle }) {
  const layerGroupRef = useRef(null)

  useEffect(() => {
    if (!map || !markerStyle) return

    const fetchAndDisplay = async () => {
      const endpoint = ENDPOINTS[dbId]
      if (!endpoint) return

      try {
        const resp = await axios.get(endpoint)
        const data = resp.data

        // Remove previous markers
        if (layerGroupRef.current) {
          map.removeLayer(layerGroupRef.current)
        }

        const group = L.layerGroup()
        const icon = createMarkerIcon(markerStyle)

        for (const item of data) {
          if (!item.lat || !item.lng) continue

          const popup = `
            <div dir="rtl" style="min-width:200px">
              <b>${item.site_name || item.address || ''}</b><br/>
              ${item.site_code ? `<span>אתר: ${item.site_code}</span><br/>` : ''}
              ${item.family ? `<span>סוג: ${item.family}</span><br/>` : ''}
              ${item.count ? `<span>כמות: ${item.count}</span>` : ''}
            </div>
          `

          L.marker([item.lat, item.lng], { icon })
            .bindPopup(popup)
            .addTo(group)
        }

        group.addTo(map)
        layerGroupRef.current = group

      } catch (err) {
        console.error(`Failed to load ${dbId} markers:`, err)
      }
    }

    fetchAndDisplay()

    return () => {
      if (layerGroupRef.current) {
        map.removeLayer(layerGroupRef.current)
        layerGroupRef.current = null
      }
    }
  }, [map, dbId, markerStyle])

  return null
}

export default DatabaseMarkers
