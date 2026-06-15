import { create } from 'zustand'

type AuthState = {
  isAuthenticated: boolean
  username: string
  role: string
  login: (username: string, role: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: Boolean(localStorage.getItem('apex_access_token')),
  username: localStorage.getItem('apex_username') ?? 'Guest',
  role: localStorage.getItem('apex_role') ?? 'VIEWER',
  login: (username, role) => {
    localStorage.setItem('apex_username', username)
    localStorage.setItem('apex_role', role)
    set({ isAuthenticated: true, username, role })
  },
  logout: () => {
    localStorage.removeItem('apex_access_token')
    localStorage.removeItem('apex_refresh_token')
    localStorage.removeItem('apex_username')
    localStorage.removeItem('apex_role')
    set({ isAuthenticated: false, username: 'Guest', role: 'VIEWER' })
  }
}))
