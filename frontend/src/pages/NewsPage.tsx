import { Newspaper } from 'lucide-react'
import { SectionTitle } from '../components/common'

const news = [
  ['Macro', 'Central bank decision supports risk-on sentiment', 'Medium'],
  ['Crypto', 'Institutional BTC demand remains elevated', 'High'],
  ['Equities', 'Tech sector volatility increases after earnings', 'Medium']
]

export default function NewsPage() {
  return (
    <div className="space-y-6">
      <SectionTitle title="News Intelligence" subtitle="News collection, classification, impact scoring, and AI summaries." />
      <div className="card">
        <div className="mb-4 flex items-center gap-3">
          <Newspaper className="h-8 w-8 text-cyan-300" />
          <div>
            <p className="font-bold">Stage 2 Ready</p>
            <p className="text-sm text-slate-400">Foundation prepared for Reuters, Bloomberg, CoinDesk, and CoinTelegraph sources.</p>
          </div>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-800 text-slate-400">
            <tr><th className="p-3">Category</th><th className="p-3">Headline</th><th className="p-3">Impact</th></tr>
          </thead>
          <tbody>
            {news.map(([category, headline, impact]) => (
              <tr key={headline} className="border-b border-slate-800/70 last:border-0">
                <td className="p-3">{category}</td>
                <td className="p-3">{headline}</td>
                <td className="p-3 text-amber-300">{impact}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
