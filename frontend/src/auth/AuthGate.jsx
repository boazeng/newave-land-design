import { useCallback, useEffect, useState } from 'react'
import axios from 'axios'
import LoginPage from './LoginPage'

// Shows the login screen until there is a valid session, then the app.
// Any API call that comes back 401 (expired or revoked session) drops back here.
function AuthGate({ children }) {
  const [user, setUser] = useState(undefined) // undefined = still checking

  useEffect(() => {
    axios.get('/api/auth/me')
      .then(resp => setUser(resp.data))
      .catch(() => setUser(null))

    const id = axios.interceptors.response.use(
      r => r,
      err => {
        const url = err.config?.url || ''
        if (err.response?.status === 401 && !url.startsWith('/api/auth/')) setUser(null)
        return Promise.reject(err)
      },
    )
    return () => axios.interceptors.response.eject(id)
  }, [])

  const logout = useCallback(async () => {
    try { await axios.post('/api/auth/logout') } catch { /* cookie is cleared either way */ }
    window.google?.accounts?.id?.disableAutoSelect()
    setUser(null)
  }, [])

  if (user === undefined) return null
  if (!user) return <LoginPage onLogin={setUser} />

  return (
    <>
      {children}
      <div dir="rtl" className="fixed bottom-3 left-3 z-[2000] flex items-center gap-2 bg-white/90 backdrop-blur
                                rounded-full shadow border border-sky-100 pl-3 pr-1 py-1 text-sm text-blue-900">
        {user.picture
          ? <img src={user.picture} alt="" referrerPolicy="no-referrer" className="w-7 h-7 rounded-full" />
          : <span className="w-7 h-7 rounded-full bg-sky-100 flex items-center justify-center">{user.name[0]}</span>}
        <span className="max-w-[10rem] truncate" title={user.email}>{user.name}</span>
        <button onClick={logout} className="text-blue-700 hover:text-red-600 font-medium">יציאה</button>
      </div>
    </>
  )
}

export default AuthGate
