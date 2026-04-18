import { useEffect, useRef, useCallback, useState } from 'react'
import L from 'leaflet'
import axios from 'axios'

const STYLE_NOT_REVIEWED = {
  color: '#9ca3af', weight: 2, fillColor: '#d1d5db', fillOpacity: 0.05,
  opacity: 0.4, dashArray: '4, 8',
}
const STYLE_HIGH_PRIORITY = {
  color: '#dc2626', weight: 4, fillColor: '#fca5a5', fillOpacity: 0.15,
  opacity: 0.9, dashArray: '10, 4',
}
const STYLE_HOVER = { weight: 5, fillOpacity: 0.22, opacity: 1 }

const MIN_ZOOM = 11

function makeStyles(color) {
  return {
    DEFAULT: { color, weight: 3, fillColor: color, fillOpacity: 0.10, opacity: 0.75, dashArray: '8, 6' },
    CONTINUE: { color, weight: 4, fillColor: color, fillOpacity: 0.22, opacity: 1, dashArray: '6, 3' },
  }
}

function getStyleForPlan(plan, styles) {
  if (plan.priority === 'high') return STYLE_HIGH_PRIORITY
  if (plan.continue_handling) return styles.CONTINUE
  if (plan.reviewed) return STYLE_NOT_REVIEWED
  return styles.DEFAULT
}

function PlansLayer({ map, visible, filter, db = 'plans_tanai_saf', dbColor = '#7c3aed', onPlanClick }) {
  const styles = makeStyles(dbColor)
  const layerGroupRef = useRef(null)
  const abortRef = useRef(null)
  const lastBboxRef = useRef(null)
  const statusCacheRef = useRef({})
  const onPlanClickRef = useRef(onPlanClick)
  useEffect(() => { onPlanClickRef.current = onPlanClick }, [onPlanClick])

  const fetchPlans = useCallback(async () => {
    if (!map || !visible) return
    const zoom = map.getZoom()
    if (zoom < MIN_ZOOM) {
      if (layerGroupRef.current) layerGroupRef.current.clearLayers()
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
        params: { bbox, db }, signal: controller.signal,
      })

      if (!layerGroupRef.current) layerGroupRef.current = L.layerGroup().addTo(map)
      layerGroupRef.current.clearLayers()

      if (resp.data.features?.length > 0) {
        const geojsonLayer = L.geoJSON(resp.data, {
          style: (feature) => {
            const plans = feature.properties.plans || []
            // Use the "best" status among all plans on this block
            let bestPlan = plans[0] || {}
            for (const p of plans) {
              if (p.priority === 'high') { bestPlan = p; break }
              if (p.continue_handling) bestPlan = p
            }
            return { ...getStyleForPlan(bestPlan, styles) }
          },
          filter: (feature) => {
            if (!filter || filter === 'all') return true
            const plans = feature.properties.plans || []
            if (filter === 'not_reviewed') return plans.some(p => !p.reviewed)
            if (filter === 'reviewed') return plans.some(p => p.reviewed)
            if (filter === 'continue') return plans.some(p => p.continue_handling)
            if (filter === 'high') return plans.some(p => p.priority === 'high')
            if (filter === 'medium') return plans.some(p => p.priority === 'medium')
            if (filter === 'low') return plans.some(p => p.priority === 'low')
            return true
          },
          onEachFeature: (feature, layer) => {
            const p = feature.properties
            layer.bindTooltip(`גוש ${p.gush_num} (${p.plan_count} תכניות)`, {
              sticky: true, direction: 'top',
            })

            layer.on('mouseover', () => {
              const currentStyle = layer.options
              layer.setStyle({ ...currentStyle, ...STYLE_HOVER })
            })
            layer.on('mouseout', () => {
              const plans = p.plans || []
              let bestPlan = plans[0] || {}
              for (const pl of plans) {
                if (pl.priority === 'high') { bestPlan = pl; break }
                if (pl.continue_handling) bestPlan = pl
              }
              layer.setStyle(getStyleForPlan(bestPlan, styles))
            })

            layer.on('click', (e) => {
              const { clientX, clientY } = e.originalEvent
              const vw = window.innerWidth, vh = window.innerHeight
              const left = clientX + 350 > vw ? clientX - 360 : clientX + 10
              const top = Math.min(clientY - 40, vh - 100)
              onPlanClickRef.current?.({ ...p, pos: { top, left } })
            })
          },
        })
        layerGroupRef.current.addLayer(geojsonLayer)
      }
    } catch (err) {
      if (err.name !== 'CanceledError') console.error('Plans layer error:', err)
    }
  }, [map, visible, filter, db])

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
    if (visible && !layerGroupRef.current) fetchPlans()
  }, [visible, map, fetchPlans])

  // Re-fetch when filter or db changes
  useEffect(() => {
    lastBboxRef.current = null
    if (visible) fetchPlans()
  }, [filter, db])

  useEffect(() => {
    return () => {
      if (layerGroupRef.current && map) map.removeLayer(layerGroupRef.current)
      if (abortRef.current) abortRef.current.abort()
    }
  }, [map])

  return null
}

export default PlansLayer
