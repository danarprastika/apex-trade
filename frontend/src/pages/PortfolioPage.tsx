import { SectionTitle } from '../components/common'
import { usePortfolio, usePortfolioSnapshots } from '../hooks/useApexQueries'

function formatCurrency(value: number, currency = 'USDT') {
  return `${currency} ${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
}

export default function PortfolioPage() {
  const portfolio = usePortfolio()
  const snapshots = usePortfolioSnapshots()

  return (
    <div className="space-y-6">
      <SectionTitle title="Portfolio Center" subtitle="Allocation, exposure, snapshots, and performance analytics." />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <SectionTitle title="Snapshots" />
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 text-slate-400">
              <tr><th className="p-3">Captured</th><th className="p-3">Total Value</th><th className="p-3">Cash</th><th className="p-3">Open Positions</th><th className="p-3">PnL</th></tr>
            </thead>
            <tbody>
              {snapshots.data?.map((snapshot) => (
                <tr key={snapshot.id} className="border-b border-slate-800/70 last:border-0">
                  <td className="p-3">{new Date(snapshot.captured_at).toLocaleString()}</td>
                  <td className="p-3">{formatCurrency(snapshot.total_value, portfolio.data?.currency)}</td>
                  <td className="p-3">{formatCurrency(snapshot.cash_balance, portfolio.data?.currency)}</td>
                  <td className="p-3">{snapshot.open_positions}</td>
                  <td className="p-3 text-emerald-300">{snapshot.daily_pnl}</td>
                </tr>
              )) ?? <tr><td colSpan={5} className="p-3 text-slate-400">No snapshots loaded yet</td></tr>}
            </tbody>
          </table>
        </div>
        <div className="space-y-4">
          <div className="card"><p className="text-sm text-slate-400">Total Value</p><p className="mt-2 text-3xl font-black text-cyan-300">{portfolio.data ? formatCurrency(portfolio.data.total_value, portfolio.data.currency) : 'Loading'}</p></div>
          <div className="card"><p className="text-sm text-slate-400">Cash Balance</p><p className="mt-2 text-3xl font-black text-emerald-300">{portfolio.data ? formatCurrency(portfolio.data.cash_balance, portfolio.data.currency) : 'Loading'}</p></div>
          <div className="card"><p className="text-sm text-slate-400">Risk Score</p><p className="mt-2 text-3xl font-black text-cyan-300">{portfolio.data ? portfolio.data.risk_score : 'Loading'}</p></div>
        </div>
      </div>
    </div>
  )
}
