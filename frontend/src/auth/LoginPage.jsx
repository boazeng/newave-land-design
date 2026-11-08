import { useEffect, useRef, useState } from 'react'
import axios from 'axios'

const GSI_SRC = 'https://accounts.google.com/gsi/client'

function loadGsi() {
  if (window.google?.accounts?.id) return Promise.resolve()
  return new Promise((resolve, reject) => {
    let s = document.querySelector(`script[src="${GSI_SRC}"]`)
    if (!s) {
      s = document.createElement('script')
      s.src = GSI_SRC
      s.async = true
      document.head.appendChild(s)
    }
    s.addEventListener('load', () => resolve())
    s.addEventListener('error', () => reject(new Error('gsi')))
  })
}

function LoginPage({ onLogin }) {
  const buttonRef = useRef(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function handleCredential({ credential }) {
      setBusy(true)
      setError('')
      try {
        const resp = await axios.post('/api/auth/google', { credential })
        onLogin(resp.data)
      } catch (e) {
        setError(e.response?.data?.detail || 'ההתחברות נכשלה, נסו שוב')
      } finally {
        setBusy(false)
      }
    }

    async function init() {
      try {
        const [{ data }] = await Promise.all([axios.get('/api/auth/config'), loadGsi()])
        if (cancelled) return
        if (!data.google_client_id) {
          setError('ההתחברות עם גוגל לא הוגדרה בשרת')
          return
        }
        window.google.accounts.id.initialize({
          client_id: data.google_client_id,
          callback: handleCredential,
        })
        window.google.accounts.id.renderButton(buttonRef.current, {
          theme: 'outline',
          size: 'large',
          text: 'signin_with',
          locale: 'he',
          width: 280,
        })
      } catch {
        if (!cancelled) setError('לא ניתן לטעון את ההתחברות עם גוגל')
      }
    }

    init()
    return () => { cancelled = true }
  }, [onLogin])

  return (
    <div dir="rtl" className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-blue-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-md border border-sky-100 p-10 w-full max-w-sm flex flex-col items-center gap-6 text-center">
        <div>
          <h1 className="text-2xl font-bold text-blue-900">Newave Land Design</h1>
          <p className="text-base text-blue-800 mt-2">כניסה למערכת</p>
        </div>
        <div ref={buttonRef} className={busy ? 'opacity-50 pointer-events-none' : ''} />
        {busy && <p className="text-sm text-blue-700">מתחבר…</p>}
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>
    </div>
  )
}

export default LoginPage
