import type { JournalFilters } from '../../types/api'

type JournalFiltersProps = {
  filters: JournalFilters
  onChange: (filters: JournalFilters) => void
  onSearch: (search: string) => void
}

export function JournalFilters({ filters, onChange, onSearch }: JournalFiltersProps) {
  function update(patch: Partial<JournalFilters>) {
    onChange({ ...filters, ...patch })
  }

  return (
    <div className="card space-y-4">
      <div className="grid gap-3 md:grid-cols-4">
        <input className="input" value={filters.search ?? ''} onChange={(event) => onSearch(event.target.value)} placeholder="Search notes" />
        <input className="input" value={filters.date_from ?? ''} onChange={(event) => update({ date_from: event.target.value })} type="date" />
        <input className="input" value={filters.date_to ?? ''} onChange={(event) => update({ date_to: event.target.value })} type="date" />
        <select className="input" value={filters.outcome?.[0] ?? ''} onChange={(event) => update({ outcome: event.target.value ? [event.target.value] : undefined })}>
          <option value="">All outcomes</option>
          <option value="WIN">Win</option>
          <option value="LOSS">Loss</option>
          <option value="BREAK_EVEN">Break even</option>
        </select>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        <input className="input" type="number" min={1} max={10} value={filters.risk_score_range?.[0] ?? ''} onChange={(event) => update({ risk_score_range: [Number(event.target.value || 1), filters.risk_score_range?.[1] ?? 10] })} placeholder="Min risk" />
        <input className="input" type="number" min={1} max={10} value={filters.risk_score_range?.[1] ?? ''} onChange={(event) => update({ risk_score_range: [filters.risk_score_range?.[0] ?? 1, Number(event.target.value || 10)] })} placeholder="Max risk" />
        <input className="input" value={filters.tags?.join(', ') ?? ''} onChange={(event) => update({ tags: event.target.value.split(',').map((tag) => tag.trim()).filter(Boolean) })} placeholder="Tags comma-separated" />
      </div>
      <div className="flex justify-end">
        <button className="btn" type="button" onClick={() => onChange({ page: 1, size: filters.size ?? 20 })}>
          Reset
        </button>
      </div>
    </div>
  )
}
