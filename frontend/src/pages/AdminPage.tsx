import { SectionTitle } from '../components/common'
import { useAdminUsers, useAuditLogs } from '../hooks/useApexQueries'

export default function AdminPage() {
  const users = useAdminUsers()
  const auditLogs = useAuditLogs()

  return (
    <div className="space-y-6">
      <SectionTitle title="Admin Center" subtitle="Users, roles, system settings, audit logs, and feature flags." />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="card"><p className="text-sm text-slate-400">Users</p><p className="mt-2 text-3xl font-black text-cyan-300">{users.data?.length ?? 0}</p></div>
        <div className="card"><p className="text-sm text-slate-400">Audit Logs</p><p className="mt-2 text-3xl font-black text-emerald-300">{auditLogs.data?.length ?? 0}</p></div>
        <div className="card"><p className="text-sm text-slate-400">System Status</p><p className="mt-2 text-3xl font-black text-amber-300">Live</p></div>
      </div>
      <div className="card">
        <SectionTitle title="Audit Preview" />
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-800 text-slate-400">
            <tr><th className="p-3">Entity</th><th className="p-3">Action</th><th className="p-3">User</th><th className="p-3">Created</th></tr>
          </thead>
          <tbody>
            {auditLogs.data?.slice(0, 5).map((log) => (
              <tr key={log.id} className="border-b border-slate-800/70 last:border-0">
                <td className="p-3">{log.entity_type}</td>
                <td className="p-3">{log.action}</td>
                <td className="p-3 text-slate-400">{log.user_id ?? 'system'}</td>
                <td className="p-3 text-slate-400">{new Date(log.created_at).toLocaleString()}</td>
              </tr>
            )) ?? <tr><td colSpan={4} className="p-3 text-slate-400">No audit logs loaded yet</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
