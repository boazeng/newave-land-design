import { useEffect, useRef, useState } from 'react'

/** Details for a single gush of a project, shown when its polygon is clicked. */
function ProjectDetailPanel({ data, onClose }) {
  const [pos, setPos] = useState({ top: data.pos?.top ?? 80, left: data.pos?.left ?? 80 })
  const dragging = useRef(false)
  const startRef = useRef({})

  useEffect(() => {
    setPos({ top: data.pos?.top ?? 80, left: data.pos?.left ?? 80 })
  }, [data])

  const onMouseDown = (e) => {
    if (['BUTTON', 'A'].includes(e.target.tagName)) return
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

  const row = (label, value) => value ? (
    <div style={{ display: 'flex', gap: 6, fontSize: 12, alignItems: 'baseline' }}>
      <span style={{ color: '#7dd3fc', flexShrink: 0 }}>{label}:</span>
      <span style={{ color: '#0c4a6e', direction: 'ltr', textAlign: 'right' }}>{value}</span>
    </div>
  ) : null

  return (
    <div
      onMouseDown={onMouseDown}
      style={{
        position: 'fixed', top: pos.top, left: pos.left, zIndex: 1200,
        width: 320, background: 'rgba(255,255,255,0.98)', backdropFilter: 'blur(4px)',
        borderRadius: 12, boxShadow: '0 6px 24px rgba(0,0,0,0.2)',
        border: '1px solid #bae6fd', cursor: 'grab', userSelect: 'none', direction: 'rtl',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderBottom: '1px solid #e0f2fe' }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: '#0c4a6e', margin: 0 }}>גוש {data.gush_num}</h3>
        <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 18, color: '#7dd3fc', cursor: 'pointer', lineHeight: 1, padding: '0 2px' }}>×</button>
      </div>

      <div style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: '#0c4a6e' }}>{data.project_name}</span>
        {row('תוכנית', data.plan_number)}
        {row('סטטוס', data.status)}
        {row('חלקות בשלמותן', data.helkot_full)}
        {row('חלקות בחלקן', data.helkot_partial)}
        <a
          href={`/projects/${encodeURIComponent(data.project_id)}`}
          style={{ marginTop: 6, fontSize: 12, color: '#0369a1', textDecoration: 'underline' }}
        >
          לעמוד הפרוייקט ←
        </a>
      </div>
    </div>
  )
}

export default ProjectDetailPanel
