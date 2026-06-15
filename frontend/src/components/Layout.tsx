import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { Activity, Bot, Briefcase, LayoutDashboard, LineChart, Newspaper, ShieldCheck, Settings, Users } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

const menu = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/market', label: 'Market', icon: Activity },
  { to: '/trading', label: 'Trading', icon: LineChart },
  { to: '/portfolio', label: 'Portfolio', labelOnly: true },
  { to: '/news', label: 'News', icon: Newspaper },
  { to: '/admin', label: 'Admin', icon: Users }
]

export default function Layout() {
  const navigate = useNavigate()
  const { isAuthenticated, username, role, logout } = useAuthStore()

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-3 text-xl font-black tracking-tight text-cyan-300">
            <ShieldCheck className="h-8 w-8" />
            APEX
          </Link>
          <div className="flex items-center gap-4">
            <span className="rounded-full border border-slate-700 px-3 py-1 text-sm text-slate-300">
              {username} · {role}
            </span>
            {isAuthenticated ? (
              <button className="btn" onClick={() => { logout(); navigate('/login') }}>
                Logout
              </button>
            ) : (
              <Link className="btn" to="/login">Login</Link>
            )}
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl grid-cols-[220px_1fr] gap-6 px-6 py-6">
        <aside className="card h-fit">
          <nav className="flex flex-col gap-2">
            {menu.map((item) => {
              const Icon = item.icon ?? Briefcase
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition ${
                      isActive ? 'bg-cyan-500 text-slate-950' : 'text-slate-300 hover:bg-slate-900'
                    }`
                  }
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </NavLink>
              )
            })}
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition ${
                  isActive ? 'bg-cyan-500 text-slate-950' : 'text-slate-300 hover:bg-slate-900'
                }`
              }
            >
              <Settings className="h-4 w-4" />
              Settings
            </NavLink>
          </nav>
        </aside>
        <main>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
