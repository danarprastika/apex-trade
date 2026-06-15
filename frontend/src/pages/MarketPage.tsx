import { Activity, TrendingUp, Waves } from 'lucide-react'
import { SectionTitle } from '../components/common'
import { useAssets, useMarketPairs } from '../hooks/useApexQueries'

export default function MarketPage() {
  const assets = useAssets()
  const pairs = useMarketPairs()

  return (
    <div className="space-y-6">
      <SectionTitle title="Market Intelligence" subtitle="Multi-asset market monitoring and scanner foundation." />
      <div className="grid gap-4 md:grid-cols-3">
        <div className="card"><Activity className="mb-3 h-8 w-8 text-cyan-300" /><p className="font-bold">Assets</p><p className="text-sm text-slate-400">{assets.data?.length ?? 0} tracked</p></div>
        <div className="card"><Waves className="mb-3 h-8 w-8 text-emerald-300" /><p className="font-bold">Pairs</p><p className="text-sm text-slate-400">{pairs.data?.length ?? 0} active</p></div>
        <div className="card"><TrendingUp className="mb-3 h-8 w-8 text-amber-300" /><p className="font-bold">Liquidity</p><p className="text-sm text-slate-400">Spread and depth</p></div>
      </div>
      <div className="card overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-800 text-slate-400">
            <tr><th className="p-3">Asset</th><th className="p-3">Type</th><th className="p-3">Status</th><th className="p-3">Updated</th></tr>
          </thead>
          <tbody>
            {assets.data?.map((asset) => (
              <tr key={asset.id} className="border-b border-slate-800/70 last:border-0">
                <td className="p-3 font-bold">{asset.symbol}</td>
                <td className="p-3">{asset.asset_type}</td>
                <td className="p-3 text-emerald-300">{asset.status}</td>
                <td className="p-3 text-slate-400">{new Date(asset.updated_at).toLocaleString()}</td>
              </tr>
            )) ?? <tr><td colSpan={4} className="p-3 text-slate-400">No assets loaded yet</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
