import { useEffect, useRef } from 'react'
import L from 'leaflet'
import axios from 'axios'

const STYLE = (color) => ({
  color, weight: 3, fillColor: color, fillOpacity: 0.18, opacity: 0.9,
})
const STYLE_HOVER = { weight: 5, fillOpacity: 0.32, opacity: 1 }

/**
 * Draws one project's gushim on the map.
 *
 * Unlike PlansLayer this fetches once and is not bbox/zoom gated - a project is
 * a handful of blocks, and the point is to find it, so it must be visible at
 * any zoom.
 */
function ProjectsLayer({ map, visible, projectId, color = '#dc2626', onFeatureClick, onLoaded }) {
  const layerRef = useRef(null)
  const dataRef = useRef(null)
  const onFeatureClickRef = useRef(onFeatureClick)
  const onLoadedRef = useRef(onLoaded)
  useEffect(() => { onFeatureClickRef.current = onFeatureClick }, [onFeatureClick])
  useEffect(() => { onLoadedRef.current = onLoaded }, [onLoaded])

  useEffect(() => {
    if (!map) return

    const clear = () => {
      if (layerRef.current) {
        map.removeLayer(layerRef.current)
        layerRef.current = null
      }
    }

    if (!visible) {
      clear()
      return
    }

    let cancelled = false

    const draw = (geojson) => {
      if (cancelled || !geojson) return
      const mine = {
        ...geojson,
        features: geojson.features.filter(f => f.properties.project_id === projectId),
      }
      if (!mine.features.length) return

      clear()
      const layer = L.geoJSON(mine, {
        style: () => STYLE(color),
        onEachFeature: (feature, lyr) => {
          const p = feature.properties
          const helkot = [
            p.helkot_full && `בשלמותן: ${p.helkot_full}`,
            p.helkot_partial && `בחלקן: ${p.helkot_partial}`,
          ].filter(Boolean).join('<br>')
          lyr.bindTooltip(
            `<b>גוש ${p.gush_num}</b><br>${p.project_name}${helkot ? '<br>' + helkot : ''}`,
            { sticky: true, direction: 'top' },
          )
          lyr.on('mouseover', () => lyr.setStyle({ ...STYLE(color), ...STYLE_HOVER }))
          lyr.on('mouseout', () => lyr.setStyle(STYLE(color)))
          lyr.on('click', (e) => {
            const { clientX, clientY } = e.originalEvent
            const left = clientX + 350 > window.innerWidth ? clientX - 360 : clientX + 10
            const top = Math.min(clientY - 40, window.innerHeight - 100)
            onFeatureClickRef.current?.({ ...p, pos: { top, left } })
          })
        },
      })
      layer.addTo(map)
      layerRef.current = layer
      onLoadedRef.current?.(projectId, layer.getBounds())
    }

    if (dataRef.current) {
      draw(dataRef.current)
    } else {
      axios.get('/api/projects/geojson')
        .then(r => { dataRef.current = r.data; draw(r.data) })
        .catch(err => console.error('Projects layer error:', err))
    }

    return () => { cancelled = true }
  }, [map, visible, projectId, color])

  useEffect(() => () => {
    if (layerRef.current && map) map.removeLayer(layerRef.current)
  }, [map])

  return null
}

export default ProjectsLayer
