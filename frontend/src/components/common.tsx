export function MetricCard({ label, value, tone = 'cyan' }: { label: string; value: string; tone?: string }) {
  const toneClass = tone === 'green' ? 'text-emerald-300' : tone === 'red' ? 'text-rose-300' : 'text-cyan-300'
  return (
    <div className="card">
      <p className="text-sm text-slate-400">{label}</p>
      <p className={`mt-2 text-3xl font-black ${toneClass}`}>{value}</p>
    </div>
  )
}

export function SectionTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-4">
      <h2 className="text-xl font-bold">{title}</h2>
      {subtitle && <p className="text-sm text-slate-400">{subtitle}</p>}
    </div>
  )
}
