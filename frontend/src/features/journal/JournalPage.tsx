import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { BookOpen } from 'lucide-react'
import { journalApi } from '../../services/journalApi'
import type { JournalFilters } from '../../types/api'
import { JournalFilters as JournalFilterPanel } from './JournalFilters'
import { JournalForm } from './JournalForm'
import { JournalList } from './JournalList'
import { JournalStats } from './JournalStats'

const initialFilters: JournalFilters = {
  page: 1,
  size: 20,
  sort_by: 'created_at',
  sort_order: 'desc'
}

export function JournalPage() {
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState<JournalFilters>(initialFilters)
  const [tradeId, setTradeId] = useState('')

  useEffect(() => {
    document.title = 'Trading Journal | APEX'
  }, [])

  const journalsQuery = useQuery({
    queryKey: ['journalList', filters],
    queryFn: () => journalApi.list(filters).then((response) => response.data)
  })

  const analyticsQuery = useQuery({
    queryKey: ['journalAnalytics', filters],
    queryFn: () => journalApi.getAnalytics(filters).then((response) => response.data)
  })

  const deleteMutation = useMutation({
    mutationFn: journalApi.remove,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journalList'] })
      queryClient.invalidateQueries({ queryKey: ['journalAnalytics'] })
    }
  })

  async function exportCsv() {
    const response = await journalApi.exportCsv(filters)
    const blob = new Blob([response.data], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `trade-journals-${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <BookOpen className="h-8 w-8 text-cyan-300" />
          <div>
            <h1 className="text-3xl font-bold text-slate-100">Trading Journal</h1>
            <p className="text-sm text-slate-400">Review trades, tag behavior, and track performance patterns.</p>
          </div>
        </div>
        <button className="btn" type="button" onClick={exportCsv}>Export CSV</button>
      </div>

      <JournalFilterPanel filters={filters} onChange={setFilters} onSearch={(search) => setFilters({ ...filters, search, page: 1 })} />
      <JournalStats analytics={analyticsQuery.data} />

      <div className="grid gap-6 lg:grid-cols-[1fr_420px]">
        <div className="space-y-6">
          <JournalList journals={journalsQuery.data?.items} isLoading={journalsQuery.isLoading} onDelete={(journalId) => deleteMutation.mutate(journalId)} />
        </div>
        <JournalForm tradeId={tradeId} onCreated={() => {
          queryClient.invalidateQueries({ queryKey: ['journalList'] })
          queryClient.invalidateQueries({ queryKey: ['journalAnalytics'] })
        }} />
      </div>

      <div className="card flex gap-3">
        <input className="input flex-1" value={tradeId} onChange={(event) => setTradeId(event.target.value)} placeholder="Closed trade ID" />
        <button className="btn" type="button" onClick={() => setTradeId('')}>Clear</button>
      </div>
    </div>
  )
}
