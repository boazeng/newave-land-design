import { useEffect, useRef, useState } from 'react'

/** Lists the projects and lets each one be shown on the map or hidden. */
function ProjectsPanel({ projects, state, onToggle, onZoom, onClose }) {
  const [pos, setPos] = useState({ top: 80, left: 56 })
  const dragging = useRef(false)
  const startRef = useRef({})

  const onMouseDown = (e) => {
    if (['INPUT', 'BUTTON', 'LABEL'].includes(e.target.tagName)) return
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

  return (
    <div
      onMouseDown={onMouseDown}
      style={{
        position: 'absolute', top: pos.top, left: pos.left, zIndex: 1000,
        width: 260, background: 'rgba(255,255,255,0.97)', backdropFilter: 'blur(4px)',
        borderRadius: 12, boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
        border: '1px solid #bae6fd', cursor: 'grab', userSelect: 'none',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 16px', borderBottom: '1px solid #e0f2fe' }}>
        <h3 style={{ fontSize: 13, fontWeight: 700, color: '#0c4a6e', margin: 0 }}>פרוייקטים</h3>
        <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 18, color: '#7dd3fc', cursor: 'pointer', lineHeight: 1, padding: '0 2px' }}>×</button>
      </div>

      <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 10, direction: 'rtl' }}>
        {projects.length === 0 && (
          <span style={{ fontSize: 12, color: '#7dd3fc' }}>אין פרוייקטים</span>
        )}
        {projects.map((p) => {
          const st = state[p.id] || {}
          const gushCount = p.plan?.gushim?.length || 0
          return (
            <div key={p.id} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
              <input
                type="checkbox"
                checked={!!st.active}
                onChange={() => onToggle(p.id)}
                style={{ width: 15, height: 15, cursor: 'pointer', accentColor: st.color, marginTop: 2 }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 10, height: 10, borderRadius: 2, background: st.color, flexShrink: 0 }} />
                  <span style={{ fontSize: 13, color: '#0c4a6e', fontWeight: 600 }}>{p.name}</span>
                </div>
                <span style={{ fontSize: 11, color: '#7dd3fc', display: 'block' }}>
                  {p.plan_number} · {gushCount ? `${gushCount} גושים` : 'אין גושים'}
                </span>
              </div>
              {st.active && gushCount > 0 && (
                <button
                  onClick={() => onZoom(p.id)}
                  title="מרכוז על הפרוייקט"
                  style={{ background: 'none', border: '1px solid #bae6fd', borderRadius: 6, cursor: 'pointer', fontSize: 11, color: '#0369a1', padding: '2px 6px' }}
                >
                  מרכוז
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ProjectsPanel
