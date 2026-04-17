import { useEffect, useRef, useCallback } from 'react'
import L from 'leaflet'
import axios from 'axios'

// Dashed outline style for plan blocks - visible but not hiding other data
const PLAN_STYLE = {
  color: '#7c3aed',        // purple
  weight: 3,
  fillColor: '#a78bfa',
  fillOpacity: 0.08,
  opacity: 0.7,
  dashArray: '8, 6',       // dashed line
  dashOffset: '0',
}

const PLAN_HOVER_STYLE = {
  color: '#7c3aed',
  weight: 4,
  fillOpacity: 0.15,
  opacity: 1,
  dashArray: '8, 6',
}

const MIN_ZOOM = 11

function PlansLayer({ map, visible }) {
  const layerGroupRef = useRef(null)
  const abortRef = useRef(null)
  const lastBboxRef = useRef(null)

  const fetchPlans = useCallback(async () => {
    if (!map || !visible) return

    const zoom = map.getZoom()
    if (zoom < MIN_ZOOM) {
      if (layerGroupRef.current) {
        layerGroupRef.current.clearLayers()
      }
      lastBboxRef.current = null
      return
    }

    const bounds = map.getBounds()
    const bbox = `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`

    if (bbox === lastBboxRef.current) return
    lastBboxRef.current = bbox

    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller

    try {
      const resp = await axios.get('/api/plans/geojson', {
        params: { bbox },
        signal: controller.signal,
      })

      if (!layerGroupRef.current) {
        layerGroupRef.current = L.layerGroup().addTo(map)
      }
      layerGroupRef.current.clearLayers()

      if (resp.data.features && resp.data.features.length > 0) {
        const geojsonLayer = L.geoJSON(resp.data, {
          style: () => ({ ...PLAN_STYLE }),
          onEachFeature: (feature, layer) => {
            const p = feature.properties
            const planList = (p.plans || []).map(plan =>
              `<div style="margin-bottom:4px;">
                <strong>${plan.plan_number}</strong> - ${plan.plan_name || ''}
                ${plan.area_dunam ? `<br/><span style="color:#666;">שטח: ${plan.area_dunam} דונם</span>` : ''}
                ${plan.purpose ? `<br/><span style="color:#666;">${plan.purpose.substring(0, 80)}</span>` : ''}
                ${plan.has_pdf ? '<br/><span style="color:green;">📄 PDF זמין</span>' : ''}
              </div>`
            ).join('<hr style="margin:4px 0;border-color:#e5e7eb;"/>')

            const popup = `
              <div style="direction:rtl;font-family:Arial;max-width:350px;max-height:300px;overflow-y:auto;">
                <div style="font-weight:bold;color:#1e40af;margin-bottom:6px;font-size:14px;">
                  גוש ${p.gush_num} - ${p.plan_count} תכניות
                </div>
                ${planList}
              </div>
            `
            layer.bindPopup(popup, { maxWidth: 400 })
            layer.bindTooltip(`גוש ${p.gush_num} (${p.plan_count} תכניות)`, {
              sticky: true,
              direction: 'top',
              className: 'plans-tooltip',
            })

            // Hover effect
            layer.on('mouseover', () => layer.setStyle(PLAN_HOVER_STYLE))
            layer.on('mouseout', () => layer.setStyle(PLAN_STYLE))
          },
        })
        layerGroupRef.current.addLayer(geojsonLayer)
      }
    } catch (err) {
      if (err.name !== 'CanceledError') {
        console.error('Plans layer error:', err)
      }
    }
  }, [map, visible])

  useEffect(() => {
    if (!map || !visible) return
    fetchPlans()
    const handler = () => fetchPlans()
    map.on('moveend', handler)
    return () => map.off('moveend', handler)
  }, [map, visible, fetchPlans])

  useEffect(() => {
    if (!map) return
    if (!visible && layerGroupRef.current) {
      map.removeLayer(layerGroupRef.current)
      layerGroupRef.current = null
      lastBboxRef.current = null
    }
    if (visible && !layerGroupRef.current) {
      fetchPlans()
    }
  }, [visible, map, fetchPlans])

  useEffect(() => {
    return () => {
      if (layerGroupRef.current && map) map.removeLayer(layerGroupRef.current)
      if (abortRef.current) abortRef.current.abort()
    }
  }, [map])

  return null
}

export default PlansLayer
