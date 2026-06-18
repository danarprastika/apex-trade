import type { TradeJournal } from '../../types/api'

type JournalListProps = {
  journals?: TradeJournal[]
  isLoading?: boolean
  onDelete: (journalId: string) => void
}

export function JournalList({ journals, isLoading, onDelete }: JournalListProps) {
  if (isLoading) {
    return <div className="card text-slate-400">Loading journal entries...</div>
  }

  if (!journals?.length) {
    return <div className="card text-slate-400">No journal entries found. Create one after a closed trade.</div>
  }

  return (
    <div className="card overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-800 text-slate-400">
          <tr>
            <th className="p-3">Trade</th>
            <th className="p-3">Strategy</th>
            <th className="p-3">Outcome</th>
            <th className="p-3">Risk</th>
            <th className="p-3">Tags</th>
            <th className="p-3">Created</th>
            <th className="p-3">Actions</th>
          </tr>
        </thead>
        <tbody>
          {journals.map((journal) => (
            <tr key={journal.id} className="border-b border-slate-800/70 last:border-0">
              <td className="p-3 text-cyan-200">{journal.trade_id}</td>
              <td className="p-3">{journal.strategy_name}</td>
              <td className="p-3">{journal.outcome}</td>
              <td className="p-3">{journal.risk_score ?? 'N/A'}</td>
              <td className="p-3">{journal.tags.map((tag) => tag.name).join(', ') || 'None'}</td>
              <td className="p-3 text-slate-400">{new Date(journal.created_at).toLocaleString()}</td>
              <td className="p-3">
                <button className="text-sm text-red-300 hover:text-red-200" type="button" onClick={() => onDelete(journal.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
