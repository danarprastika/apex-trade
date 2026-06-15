import { FormEvent, useState } from 'react'
import { SectionTitle } from '../components/common'
import { useOrders, useSignals, useStrategies } from '../hooks/useApexQueries'
import { tradingApi } from '../services/api'

export default function TradingPage() {
  const strategies = useStrategies()
  const signals = useSignals()
  const orders = useOrders()
  const [symbol, setSymbol] = useState('')
  const [quantity, setQuantity] = useState('')
  const [price, setPrice] = useState('')
  const [side, setSide] = useState('BUY')
  const [message, setMessage] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    try {
      const strategyId = strategies.data?.[0]?.id
      if (!strategyId) {
        setMessage('Create a strategy before submitting a paper order.')
        return
      }
      await tradingApi.createPaperOrder({
        strategy_id: strategyId,
        market_pair_id: symbol,
        side,
        quantity: Number(quantity),
        price: Number(price)
      })
      setMessage('Paper order submitted and routed through Risk Engine validation.')
    } catch {
      setMessage('Unable to create signal.')
    }
  }

  return (
    <div className="space-y-6">
      <SectionTitle title="Trading Terminal" subtitle="Signals, orders, positions, and risk-aware execution." />
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <SectionTitle title="Latest Signals" />
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 text-slate-400">
              <tr><th className="p-3">Strategy</th><th className="p-3">Pair</th><th className="p-3">Action</th><th className="p-3">Confidence</th><th className="p-3">Reason</th></tr>
            </thead>
            <tbody>
              {signals.data?.map((signal) => (
                <tr key={signal.id} className="border-b border-slate-800/70 last:border-0">
                  <td className="p-3">{signal.strategy_id}</td>
                  <td className="p-3">{signal.market_pair_id}</td>
                  <td className="p-3 text-cyan-300">{signal.signal_type}</td>
                  <td className="p-3">{signal.confidence}</td>
                  <td className="p-3 text-slate-400">{signal.reason}</td>
                </tr>
              )) ?? <tr><td colSpan={5} className="p-3 text-slate-400">No signals loaded yet</td></tr>}
            </tbody>
          </table>
        </div>
        <div className="card">
          <SectionTitle title="Execution Control" />
          <form onSubmit={submit} className="space-y-4">
            <input className="input" value={symbol} onChange={(event) => setSymbol(event.target.value)} placeholder="Symbol" />
            <input className="input" type="number" value={quantity} onChange={(event) => setQuantity(event.target.value)} placeholder="Quantity" />
            <input className="input" type="number" value={price} onChange={(event) => setPrice(event.target.value)} placeholder="Price" />
            <select className="input" value={side} onChange={(event) => setSide(event.target.value)}>
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>
            <button className="btn w-full" type="submit" disabled={!symbol || !quantity || !price}>Submit Paper Order</button>
            <p className="text-sm text-slate-400">All execution requests are routed through Risk Engine validation.</p>
            {message && <p className="text-sm text-cyan-300">{message}</p>}
          </form>
          <div className="mt-6">
            <SectionTitle title="Recent Orders" />
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-800 text-slate-400">
                <tr><th className="p-3">Side</th><th className="p-3">Quantity</th><th className="p-3">Status</th></tr>
              </thead>
              <tbody>
                {orders.data?.map((order) => (
                  <tr key={order.id} className="border-b border-slate-800/70 last:border-0">
                    <td className="p-3">{order.side}</td>
                    <td className="p-3">{order.quantity}</td>
                    <td className="p-3 text-slate-400">{order.status}</td>
                  </tr>
                )) ?? <tr><td colSpan={3} className="p-3 text-slate-400">No orders loaded yet</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
