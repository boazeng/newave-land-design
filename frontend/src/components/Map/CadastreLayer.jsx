import { useEffect, useRef, useCallback } from 'react'
import L from 'leaflet'
import axios from 'axios'

const API_BASE = '/api/cadastre'

// Style for blocks (גושים)
const BLOCK_STYLE = {
  color: '#1e40af',
  weight: 2,
  fillColor: '#3b82f6',
  fillOpacity: 0.08,
  opacity: 0.6,
}

// Style for parcels (חלקות)
const PARCEL_STYLE = {
  color: '#dc2626',
  weight: 1,
  fillColor: '#fca5a5',
  fillOpacity: 0.05,
  opacity: 0.5,
}

// Min zoom levels to show layers
const BLOCKS_MIN_ZOOM = 12
const PARCELS_MIN_ZOOM = 15

function CadastreLayer({ map, layerId, visible }) {
  const layerGroupRef = useRef(null)
  const abortRef = useRef(null)
  const lastBboxRef = useRef(null)

  const isBlocks = layerId === 'blocks'
  const minZoom = isBlocks ? BLOCKS_MIN_ZOOM : PARCELS_MIN_ZOOM
  const style = isBlocks ? BLOCK_STYLE : PARCEL_STYLE
  const endpoint = isBlocks ? `${API_BASE}/blocks` : `${API_BASE}/parcels`

  const fetchFeatures = useCallback(async () => {
    if (!map || !visible) return

    const zoom = map.getZoom()
    if (zoom < minZoom) {
      // Clear layer if zoomed out too far
      if (layerGroupRef.current) {
        layerGroupRef.current.clearLayers()
      }
      return
    }

    const bounds = map.getBounds()
    const bbox = `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`

    // Skip if same bbox
    if (bbox === lastBboxRef.current) return
    lastBboxRef.current = bbox

    // Cancel previous request
    if (abortRef.current) {
      abortRef.current.abort()
    }
    const controller = new AbortController()
    abortRef.current = controller

    try {
      const resp = await axios.get(endpoint, {
        params: { bbox },
        signal: controller.signal,
      })

      if (!layerGroupRef.current) {
        layerGroupRef.current = L.layerGroup().addTo(map)
      }

      layerGroupRef.current.clearLayers()

      if (resp.data.features && resp.data.features.length > 0) {
        const geojsonLayer = L.geoJSON(resp.data, {
          style: () => style,
          onEachFeature: (feature, layer) => {
            const p = feature.properties
            const label = isBlocks
              ? `גוש ${p.GUSH_NUM}`
              : `גוש ${p.GUSH_NUM} חלקה ${p.PARCEL}`
            layer.bindTooltip(label, { sticky: true, direction: 'top' })
          },
        })
        layerGroupRef.current.addLayer(geojsonLayer)
      }
    } catch (err) {
      if (err.name !== 'CanceledError') {
        console.error(`Failed to fetch ${layerId}:`, err)
      }
    }
  }, [map, visible, layerId, minZoom, style, endpoint, isBlocks])

  // Fetch on map move/zoom
  useEffect(() => {
    if (!map || !visible) return

    fetchFeatures()

    const handler = () => fetchFeatures()
    map.on('moveend', handler)

    return () => {
      map.off('moveend', handler)
    }
  }, [map, visible, fetchFeatures])

  // Show/hide layer
  useEffect(() => {
    if (!map) return

    if (!visible && layerGroupRef.current) {
      map.removeLayer(layerGroupRef.current)
      layerGroupRef.current = null
      lastBboxRef.current = null
    }

    if (visible && !layerGroupRef.current) {
      fetchFeatures()
    }
  }, [visible, map, fetchFeatures])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (layerGroupRef.current && map) {
        map.removeLayer(layerGroupRef.current)
      }
      if (abortRef.current) {
        abortRef.current.abort()
      }
    }
  }, [map])

  return null
}

export default CadastreLayer
