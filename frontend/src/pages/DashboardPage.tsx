import { Activity, Bot, LineChart, ShieldCheck } from 'lucide-react'
import { MetricCard, SectionTitle } from '../components/common'
import { useHealth, useOrders, usePortfolio, useRiskProfile, useSignals } from '../hooks/useApexQueries'

function formatCurrency(value: number, currency = 'USDT') {
  return `${currency} ${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`
}

export default function DashboardPage() {
  const health = useHealth()
  const portfolio = usePortfolio()
  const signals = useSignals()
  const orders = useOrders()
  const riskProfile = useRiskProfile()

  const latestSignal = signals.data?.[0]
  const latestOrder = orders.data?.[0]

  return (
    <div className="space-y-6">
      <SectionTitle title="Command Center" subtitle="Real-time trading, portfolio, risk, and system overview." />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Portfolio Value" value={portfolio.data ? formatCurrency(portfolio.data.total_value, portfolio.data.currency) : 'Loading'} />
        <MetricCard label="Cash Balance" value={portfolio.data ? formatCurrency(portfolio.data.cash_balance, portfolio.data.currency) : 'Loading'} />
        <MetricCard label="Open Orders" value={orders.data ? orders.data.length.toString() : 'Loading'} />
        <MetricCard label="Risk Score" value={riskProfile.data ? `${riskProfile.data.max_risk_per_trade}%` : 'Loading'} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <SectionTitle title="Market Overview" subtitle="Latest market signals and order flow." />
          <div className="space-y-3">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <p className="text-sm text-slate-400">Latest Signal</p>
              <p className="mt-2 text-lg font-bold">{latestSignal ? `${latestSignal.signal_type} ${latestSignal.market_pair_id}` : 'No signals yet'}</p>
              <p className="text-sm text-slate-400">{latestSignal?.reason ?? 'Waiting for market data'}</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <p className="text-sm text-slate-400">Latest Order</p>
              <p className="mt-2 text-lg font-bold">{latestOrder ? `${latestOrder.side} ${latestOrder.quantity}` : 'No orders yet'}</p>
              <p className="text-sm text-slate-400">{latestOrder ? latestOrder.status : 'Waiting for execution'}</p>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center gap-3">
              <ShieldCheck className="h-8 w-8 text-cyan-300" />
              <div>
                <p className="font-bold">Risk Engine</p>
                <p className="text-sm text-slate-400">{riskProfile.data ? 'Profile active' : 'No profile yet'}</p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center gap-3">
              <Activity className="h-8 w-8 text-emerald-300" />
              <div>
                <p className="font-bold">Market Data</p>
                <p className="text-sm text-slate-400">{health.data?.database ?? 'Checking'}</p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center gap-3">
              <Bot className="h-8 w-8 text-violet-300" />
              <div>
                <p className="font-bold">AI Readiness</p>
                <p className="text-sm text-slate-400">Foundation complete</p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center gap-3">
              <LineChart className="h-8 w-8 text-amber-300" />
              <div>
                <p className="font-bold">Strategy Engine</p>
                <p className="text-sm text-slate-400">{signals.data ? `${signals.data.length} signals` : 'Loading'}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
