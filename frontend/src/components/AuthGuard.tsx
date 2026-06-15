import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'

export default function AuthGuard({ children }: { children: ReactNode }) {
  const token = localStorage.getItem('apex_access_token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return children
}
