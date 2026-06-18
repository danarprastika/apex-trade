import type { JournalAnalyticsSummary, JournalStatistics } from '../../types/api'

type JournalStatsProps = {
  analytics?: JournalAnalyticsSummary
  summary?: JournalStatistics
}

function formatPercent(value: number | null | undefined) {
  return value == null ? 'N/A' : `${(value * 100).toFixed(1)}%`
}

function formatNumber(value: number | null | undefined) {
  return value == null ? 'N/A' : value.toFixed(2)
}

export function JournalStats({ analytics, summary }: JournalStatsProps) {
  const overall = analytics?.performance_breakdown.overall ?? summary

  if (!overall) {
    return null
  }

  return (
    <div className="grid gap-4 md:grid-cols-4">
      <div className="card"><p className="text-sm text-slate-400">Total Trades</p><p className="mt-2 text-3xl font-black text-cyan-300">{overall.total_trades}</p></div>
      <div className="card"><p className="text-sm text-slate-400">Win Rate</p><p className="mt-2 text-3xl font-black text-emerald-300">{formatPercent(overall.win_rate)}</p></div>
      <div className="card"><p className="text-sm text-slate-400">Avg P&L</p><p className="mt-2 text-3xl font-black text-cyan-200">{formatNumber(overall.avg_profit)}</p></div>
      <div className="card"><p className="text-sm text-slate-400">Avg Risk</p><p className="mt-2 text-3xl font-black text-amber-300">{formatNumber(overall.avg_risk_score)}</p></div>
      {analytics && (
        <div className="card md:col-span-4">
          <h3 className="mb-3 text-sm font-semibold text-slate-300">Risk buckets</h3>
          <div className="grid gap-3 md:grid-cols-3">
            {Object.entries(analytics.performance_breakdown.by_risk_bucket).map(([bucket, stats]) => (
              <div key={bucket} className="rounded-xl border border-slate-800 p-3">
                <p className="text-sm text-slate-400">{bucket}</p>
                <p className="text-lg font-semibold text-slate-100">{stats.total_trades} trades</p>
                <p className="text-sm text-cyan-300">Win {formatPercent(stats.win_rate)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
