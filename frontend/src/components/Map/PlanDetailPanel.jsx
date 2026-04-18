import { useEffect, useRef, useState } from 'react'
import axios from 'axios'

const PRIORITY_BADGE = {
  high: { bg: '#dc2626', label: 'גבוהה' },
  medium: { bg: '#f59e0b', label: 'בינונית' },
  low: { bg: '#6b7280', label: 'נמוכה' },
}

function PlanCard({ plan }) {
  const [st, setSt] = useState({
    reviewed: plan.reviewed || false,
    continue_handling: plan.continue_handling || false,
    check_stage: plan.check_stage || '',
    priority: plan.priority || '',
  })

  const update = async (field, val) => {
    setSt(prev => ({ ...prev, [field]: val }))
    try {
      await axios.put(`/api/plans/status/${encodeURIComponent(plan.plan_number)}`, { [field]: val })
    } catch (e) { console.error(e) }
  }

  const badge = PRIORITY_BADGE[st.priority]

  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 10, marginBottom: 8, background: '#fafafa' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
        <strong style={{ color: '#1e3a5f', fontSize: 13 }}>{plan.plan_number}</strong>
        {badge && (
          <span style={{ background: badge.bg, color: 'white', padding: '1px 7px', borderRadius: 4, fontSize: 11 }}>
            {badge.label}
          </span>
        )}
      </div>
      {plan.plan_name && <div style={{ fontSize: 12, color: '#1e40af', fontWeight: 600, marginBottom: 4 }}>{plan.plan_name}</div>}
      {plan.authority && <div style={{ fontSize: 11, color: '#555', marginBottom: 2 }}><span style={{ color: '#888' }}>רשות: </span>{plan.authority}</div>}
      {plan.purpose && <div style={{ fontSize: 11, color: '#444', marginBottom: 2 }}><span style={{ color: '#888' }}>מטרה: </span>{plan.purpose.substring(0, 150)}</div>}
      {plan.area_dunam && <div style={{ fontSize: 11 }}><span style={{ color: '#888' }}>שטח: </span><strong>{plan.area_dunam.toLocaleString()} דונם</strong></div>}
      {plan.housing_units && <div style={{ fontSize: 11 }}><span style={{ color: '#888' }}>יח"ד: </span><strong>{plan.housing_units}</strong></div>}

      <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
        {plan.mavat_url && <a href={plan.mavat_url} target="_blank" rel="noreferrer" style={{ fontSize: 11, color: '#2563eb' }}>MAVAT ↗</a>}
        <a href={`/plans?q=${encodeURIComponent(plan.plan_number)}`} target="_blank" rel="noreferrer" style={{ fontSize: 11, color: '#7c3aed' }}>פרטים ↗</a>
        {plan.has_pdf && plan.sharepoint_url && <a href={plan.sharepoint_url} target="_blank" rel="noreferrer" style={{ fontSize: 11, color: '#16a34a' }}>PDF ↗</a>}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginTop: 8, paddingTop: 8, borderTop: '1px solid #e5e7eb' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, cursor: 'pointer' }}>
          <input type="checkbox" checked={st.reviewed} onChange={e => update('reviewed', e.target.checked)} style={{ cursor: 'pointer' }} />
          נבדק
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, cursor: 'pointer' }}>
          <input type="checkbox" checked={st.continue_handling} onChange={e => update('continue_handling', e.target.checked)} style={{ cursor: 'pointer' }} />
          המשך טיפול
        </label>
        <select value={st.check_stage} onChange={e => update('check_stage', e.target.value || null)}
          style={{ fontSize: 11, padding: '2px 4px', border: '1px solid #d1d5db', borderRadius: 4 }}>
          <option value="">שלב בדיקה</option>
          <option value="בדיקה תכנונית">בדיקה תכנונית</option>
          <option value="איתור בעלים">איתור בעלים</option>
        </select>
        <select value={st.priority} onChange={e => update('priority', e.target.value || null)}
          style={{ fontSize: 11, padding: '2px 4px', border: '1px solid #d1d5db', borderRadius: 4, background: st.priority === 'high' ? '#fee2e2' : st.priority === 'medium' ? '#fef3c7' : '' }}>
          <option value="">עדיפות</option>
          <option value="high">גבוהה</option>
          <option value="medium">בינונית</option>
          <option value="low">נמוכה</option>
        </select>
      </div>
    </div>
  )
}

function PlanDetailPanel({ data, onClose }) {
  const [pos, setPos] = useState(data.pos)
  const dragging = useRef(false)
  const startRef = useRef({})

  const onMouseDown = (e) => {
    if (['SELECT', 'OPTION', 'INPUT', 'LABEL', 'A'].includes(e.target.tagName)) return
    dragging.current = true
    startRef.current = { mx: e.clientX, my: e.clientY, top: pos.top, left: pos.left }
    e.preventDefault()
  }

  useEffect(() => {
    const onMove = (e) => {
      if (!dragging.current) return
      setPos({
        top: startRef.current.top + (e.clientY - startRef.current.my),
        left: startRef.current.left + (e.clientX - startRef.current.mx),
      })
    }
    const onUp = () => { dragging.current = false }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp) }
  }, [])

  const plans = data.plans || []

  return (
    <div
      onMouseDown={onMouseDown}
      style={{
        position: 'absolute', top: pos.top, left: pos.left, zIndex: 1001,
        width: 340, maxHeight: '70vh', background: 'white', borderRadius: 12,
        boxShadow: '0 8px 32px rgba(0,0,0,0.2)', border: '1px solid #e5e7eb',
        display: 'flex', flexDirection: 'column', direction: 'rtl',
        cursor: 'grab', userSelect: 'none',
      }}
    >
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '10px 14px', borderBottom: '1px solid #e5e7eb', background: '#f8fafc', borderRadius: '12px 12px 0 0',
      }}>
        <span style={{ fontWeight: 700, color: '#1e3a5f', fontSize: 13 }}>
          גוש {data.gush_num} — {data.plan_count} תוכניות
        </span>
        <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 20, color: '#9ca3af', cursor: 'pointer', lineHeight: 1, padding: '0 2px' }}>×</button>
      </div>
      <div style={{ overflowY: 'auto', padding: '10px 12px', flex: 1 }}>
        {plans.map(plan => <PlanCard key={plan.plan_number} plan={plan} />)}
      </div>
    </div>
  )
}

export default PlanDetailPanel
