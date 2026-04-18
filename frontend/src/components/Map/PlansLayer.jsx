import { useEffect, useRef, useCallback, useState } from 'react'
import L from 'leaflet'
import axios from 'axios'

const STYLE_DEFAULT = {
  color: '#7c3aed', weight: 3, fillColor: '#a78bfa', fillOpacity: 0.08,
  opacity: 0.7, dashArray: '8, 6',
}
const STYLE_RELEVANT = {
  color: '#16a34a', weight: 3, fillColor: '#86efac', fillOpacity: 0.12,
  opacity: 0.8, dashArray: '8, 6',
}
const STYLE_NOT_RELEVANT = {
  color: '#9ca3af', weight: 2, fillColor: '#d1d5db', fillOpacity: 0.05,
  opacity: 0.4, dashArray: '4, 8',
}
const STYLE_HIGH_PRIORITY = {
  color: '#dc2626', weight: 4, fillColor: '#fca5a5', fillOpacity: 0.15,
  opacity: 0.9, dashArray: '10, 4',
}
const STYLE_HOVER = {
  weight: 5, fillOpacity: 0.2, opacity: 1,
}

const MIN_ZOOM = 11

function getStyleForPlan(plan) {
  if (plan.review === 'not_relevant') return STYLE_NOT_RELEVANT
  if (plan.priority === 'high') return STYLE_HIGH_PRIORITY
  if (plan.review === 'relevant') return STYLE_RELEVANT
  return STYLE_DEFAULT
}

function PlansLayer({ map, visible, filter, db = 'plans_tanai_saf' }) {
  const layerGroupRef = useRef(null)
  const abortRef = useRef(null)
  const lastBboxRef = useRef(null)
  const statusCacheRef = useRef({})

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
              if (p.review === 'relevant') bestPlan = p
            }
            return { ...getStyleForPlan(bestPlan) }
          },
          filter: (feature) => {
            if (!filter || filter === 'all') return true
            const plans = feature.properties.plans || []
            if (filter === 'not_reviewed') return plans.some(p => p.review === 'not_reviewed')
            if (filter === 'relevant') return plans.some(p => p.review === 'relevant')
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
                if (pl.review === 'relevant') bestPlan = pl
              }
              layer.setStyle(getStyleForPlan(bestPlan))
            })

            layer.on('click', () => {
              const popupContent = buildPopupHTML(p)
              const popup = L.popup({ maxWidth: 450, maxHeight: 500, className: 'plan-popup' })
                .setLatLng(layer.getBounds().getCenter())
                .setContent(popupContent)
                .openOn(map)

              // Attach event handlers after popup opens
              setTimeout(() => attachPopupHandlers(map, p, layer), 100)
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


function buildPopupHTML(props) {
  const plans = props.plans || []
  const planCards = plans.map((plan, i) => {
    const reviewClass = plan.review === 'relevant' ? 'border-green-500 bg-green-50'
      : plan.review === 'not_relevant' ? 'border-gray-300 bg-gray-50'
      : 'border-purple-300 bg-purple-50'
    const priorityBadge = plan.priority === 'high' ? '<span style="background:#dc2626;color:white;padding:1px 6px;border-radius:4px;font-size:11px;">גבוהה</span>'
      : plan.priority === 'medium' ? '<span style="background:#f59e0b;color:white;padding:1px 6px;border-radius:4px;font-size:11px;">בינונית</span>'
      : plan.priority === 'low' ? '<span style="background:#6b7280;color:white;padding:1px 6px;border-radius:4px;font-size:11px;">נמוכה</span>'
      : ''

    return `
      <div style="border:1px solid #e5e7eb;border-radius:8px;padding:10px;margin-bottom:8px;background:white;" data-plan="${plan.plan_number}">
        <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:6px;">
          <strong style="color:#1e3a5f;font-size:13px;">${plan.plan_number}</strong>
          ${priorityBadge}
        </div>
        <div style="font-size:12px;color:#1e40af;font-weight:600;margin-bottom:4px;">${plan.plan_name || ''}</div>

        ${plan.purpose ? `<div style="font-size:11px;margin:4px 0;"><span style="color:#666;">מטרה:</span> ${plan.purpose.substring(0, 150)}</div>` : ''}
        ${plan.explanation ? `<div style="font-size:11px;margin:4px 0;color:#555;">${plan.explanation.substring(0, 120)}...</div>` : ''}
        ${plan.area_dunam ? `<div style="font-size:11px;"><span style="color:#666;">שטח:</span> <strong>${plan.area_dunam.toLocaleString()} דונם</strong></div>` : ''}
        ${plan.housing_units ? `<div style="font-size:11px;"><span style="color:#666;">יח"ד:</span> <strong>${plan.housing_units}</strong></div>` : ''}

        <div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;">
          ${plan.mavat_url ? `<a href="${plan.mavat_url}" target="_blank" style="font-size:11px;color:#2563eb;text-decoration:underline;">MAVAT ↗</a>` : ''}
          <a href="/plans?q=${encodeURIComponent(plan.plan_number)}" target="_blank" style="font-size:11px;color:#7c3aed;text-decoration:underline;">צפה באתר ↗</a>
          ${plan.has_pdf && plan.sharepoint_url ? `<a href="${plan.sharepoint_url}" target="_blank" style="font-size:11px;color:#16a34a;text-decoration:underline;">PDF ↗</a>` : ''}
        </div>

        <div style="display:flex;gap:4px;margin-top:8px;border-top:1px solid #e5e7eb;padding-top:8px;">
          <select class="plan-review-select" data-plan="${plan.plan_number}" style="font-size:11px;padding:2px 4px;border:1px solid #d1d5db;border-radius:4px;flex:1;">
            <option value="not_reviewed" ${plan.review === 'not_reviewed' ? 'selected' : ''}>לא נבדק</option>
            <option value="relevant" ${plan.review === 'relevant' ? 'selected' : ''}>רלוונטי</option>
            <option value="not_relevant" ${plan.review === 'not_relevant' ? 'selected' : ''}>לא רלוונטי</option>
          </select>
          <select class="plan-priority-select" data-plan="${plan.plan_number}" style="font-size:11px;padding:2px 4px;border:1px solid #d1d5db;border-radius:4px;flex:1;">
            <option value="" ${!plan.priority ? 'selected' : ''}>עדיפות</option>
            <option value="high" ${plan.priority === 'high' ? 'selected' : ''}>גבוהה</option>
            <option value="medium" ${plan.priority === 'medium' ? 'selected' : ''}>בינונית</option>
            <option value="low" ${plan.priority === 'low' ? 'selected' : ''}>נמוכה</option>
          </select>
        </div>
      </div>
    `
  }).join('')

  return `
    <div style="direction:rtl;font-family:Arial;min-width:300px;">
      <div style="font-weight:bold;color:#1e40af;margin-bottom:8px;font-size:15px;border-bottom:2px solid #7c3aed;padding-bottom:4px;">
        גוש ${props.gush_num} - ${props.plan_count} תכניות
      </div>
      ${planCards}
    </div>
  `
}

function attachPopupHandlers(map) {
  // Review status change
  document.querySelectorAll('.plan-review-select').forEach(sel => {
    sel.addEventListener('change', async (e) => {
      const planNum = e.target.dataset.plan
      const review = e.target.value
      try {
        await axios.put(`/api/plans/status/${encodeURIComponent(planNum)}`, { review })
        e.target.style.background = review === 'relevant' ? '#dcfce7' : review === 'not_relevant' ? '#f3f4f6' : '#faf5ff'
      } catch (err) {
        console.error('Status update failed:', err)
      }
    })
  })

  // Priority change
  document.querySelectorAll('.plan-priority-select').forEach(sel => {
    sel.addEventListener('change', async (e) => {
      const planNum = e.target.dataset.plan
      const priority = e.target.value || null
      try {
        await axios.put(`/api/plans/status/${encodeURIComponent(planNum)}`, { priority })
        e.target.style.background = priority === 'high' ? '#fee2e2' : priority === 'medium' ? '#fef3c7' : ''
      } catch (err) {
        console.error('Priority update failed:', err)
      }
    })
  })
}

export default PlansLayer
