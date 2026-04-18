import { useEffect, useRef, useState } from 'react'

function ParkingDetailPanel({ data, onClose }) {
  const [pos, setPos] = useState(data.pos)
  const dragging = useRef(false)
  const startRef = useRef({})

  const onMouseDown = (e) => {
    if (['BUTTON', 'A', 'SELECT', 'INPUT'].includes(e.target.tagName)) return
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

  const b = data.building

  const Field = ({ label, value }) => value ? (
    <div style={{ marginBottom: 5 }}>
      <span style={{ fontSize: 10, color: '#9ca3af', display: 'block' }}>{label}</span>
      <span style={{ fontSize: 12, color: '#1e3a5f', fontWeight: 500 }}>{value}</span>
    </div>
  ) : null

  return (
    <div
      onMouseDown={onMouseDown}
      style={{
        position: 'absolute', top: pos.top, left: pos.left, zIndex: 1002,
        width: 280, background: 'white', borderRadius: 12,
        boxShadow: '0 8px 32px rgba(0,0,0,0.2)', border: '1px solid #e5e7eb',
        display: 'flex', flexDirection: 'column', direction: 'rtl',
        cursor: 'grab', userSelect: 'none',
      }}
    >
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '8px 12px', borderBottom: '1px solid #e5e7eb',
        background: 'linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%)',
        borderRadius: '12px 12px 0 0',
      }}>
        <span style={{ fontWeight: 700, color: 'white', fontSize: 12 }}>
          {b.city || 'מתקן חניה'}
        </span>
        <button onClick={onClose} style={{
          background: 'rgba(255,255,255,0.2)', border: 'none', color: 'white',
          fontSize: 16, cursor: 'pointer', borderRadius: 4, lineHeight: 1,
          padding: '0 5px', width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>×</button>
      </div>

      {/* Content */}
      <div style={{ padding: '10px 12px' }}>
        {b.address && (
          <div style={{ marginBottom: 8, padding: '6px 8px', background: '#f0f9ff', borderRadius: 6, border: '1px solid #bae6fd' }}>
            <span style={{ fontSize: 11, color: '#0369a1', fontWeight: 600 }}>{b.address}</span>
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 10px' }}>
          <Field label="סוג מתקן" value={b.device_type} />
          <Field label="מספר מקומות" value={b.parking_count} />
          <Field label="גוש" value={b.gush} />
          <Field label="חלקה" value={b.helka} />
          <Field label="תאריך" value={b.date} />
          <Field label="סטטוס" value={b.status} />
        </div>

        {b.description && (
          <div style={{ marginTop: 6, padding: '5px 7px', background: '#fafafa', borderRadius: 5, border: '1px solid #e5e7eb' }}>
            <span style={{ fontSize: 10, color: '#9ca3af', display: 'block', marginBottom: 2 }}>תיאור</span>
            <span style={{ fontSize: 11, color: '#374151' }}>{b.description.substring(0, 200)}</span>
          </div>
        )}

        {b.protocol_file && (
          <div style={{ marginTop: 8 }}>
            <a
              href={`/api/parking-devices/pdf/${encodeURIComponent(b.protocol_file)}`}
              target="_blank" rel="noreferrer"
              style={{ fontSize: 11, color: '#2563eb', textDecoration: 'none', border: '1px solid #bfdbfe', borderRadius: 4, padding: '3px 8px', background: '#eff6ff' }}
            >
              פרוטוקול PDF ↗
            </a>
          </div>
        )}
      </div>
    </div>
  )
}

export default ParkingDetailPanel
