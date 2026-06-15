import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'
import { authApi } from '../services/api'
import { useAuthStore } from '../store/authStore'

export default function LoginPage() {
  const navigate = useNavigate()
  const loginStore = useAuthStore()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    try {
      await authApi.login(username, password)
      const user = await authApi.me()
      loginStore.login(user.username, user.role)
      navigate('/')
    } catch {
      setError('Login failed. Check credentials or backend availability.')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <form onSubmit={submit} className="w-full max-w-md space-y-6 card">
        <div className="flex items-center gap-3 text-cyan-300">
          <ShieldCheck className="h-10 w-10" />
          <h1 className="text-3xl font-black">APEX</h1>
        </div>
        <input className="input" value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Username" />
        <input className="input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Password" />
        {error && <p className="rounded-xl border border-rose-500/50 bg-rose-950/40 p-3 text-sm text-rose-200">{error}</p>}
        <button className="btn w-full" type="submit">Login</button>
      </form>
    </div>
  )
}
