import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import type { UserRole } from '../../types/api'

export default function RoleGuard({
  children,
  allowedRoles,
}: {
  children: ReactNode
  allowedRoles: UserRole[]
}) {
  const role = localStorage.getItem('apex_role') as UserRole | null
  if (!role || !allowedRoles.includes(role)) {
    return <Navigate to="/" replace />
  }
  return children
}