import { useEffect, useRef, useState } from 'react'

function LayersPanel({ layers, onToggleLayer, onClose }) {
  const [pos, setPos] = useState({ top: 16, right: 16 })
  const dragging = useRef(false)
  const startRef = useRef({})

  const onMouseDown = (e) => {
    if (['INPUT', 'BUTTON', 'LABEL'].includes(e.target.tagName)) return
    dragging.current = true
    startRef.current = { mx: e.clientX, my: e.clientY, top: pos.top, right: pos.right }
    e.preventDefault()
  }

  useEffect(() => {
    const onMove = (e) => {
      if (!dragging.current) return
      setPos({
        top: startRef.current.top + (e.clientY - startRef.current.my),
        right: startRef.current.right - (e.clientX - startRef.current.mx),
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
        position: 'absolute', top: pos.top, right: pos.right, zIndex: 1000,
        width: 288, background: 'rgba(255,255,255,0.97)', backdropFilter: 'blur(4px)',
        borderRadius: 12, boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
        border: '1px solid #bae6fd', cursor: 'grab', userSelect: 'none',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 16px', borderBottom: '1px solid #e0f2fe' }}>
        <h3 style={{ fontSize: 13, fontWeight: 700, color: '#0c4a6e', margin: 0 }}>שכבות</h3>
        <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 18, color: '#7dd3fc', cursor: 'pointer', lineHeight: 1, padding: '0 2px' }}>×</button>
      </div>
      <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 12, direction: 'rtl' }}>
        {layers.map((layer) => (
          <label key={layer.id} style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={layer.visible}
              onChange={() => onToggleLayer(layer.id)}
              style={{ width: 15, height: 15, cursor: 'pointer', accentColor: '#0ea5e9' }}
            />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: 13, color: '#0c4a6e' }}>{layer.name}</span>
              {layer.description && <span style={{ fontSize: 11, color: '#7dd3fc' }}>{layer.description}</span>}
            </div>
          </label>
        ))}
      </div>
    </div>
  )
}

export default LayersPanel
