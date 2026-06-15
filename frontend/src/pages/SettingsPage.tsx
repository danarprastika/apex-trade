import { SectionTitle } from '../components/common'
import { useNotifications, useRiskProfile } from '../hooks/useApexQueries'

export default function SettingsPage() {
  const riskProfile = useRiskProfile()
  const notifications = useNotifications()

  return (
    <div className="space-y-6">
      <SectionTitle title="Settings" subtitle="Profile, security, Telegram, exchange accounts, and preferences." />
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card space-y-4">
          <SectionTitle title="Risk Profile" />
          <p className="text-sm text-slate-400">Max risk per trade: {riskProfile.data?.max_risk_per_trade ?? 'Loading'}</p>
          <p className="text-sm text-slate-400">Max daily loss: {riskProfile.data?.max_daily_loss ?? 'Loading'}</p>
          <p className="text-sm text-slate-400">Max open positions: {riskProfile.data?.max_open_positions ?? 'Loading'}</p>
        </div>
        <div className="card space-y-4">
          <SectionTitle title="Notifications" />
          <p className="text-sm text-slate-400">{notifications.data?.length ?? 0} messages loaded</p>
        </div>
        <div className="card space-y-4">
          <SectionTitle title="Telegram" />
          <input className="input" placeholder="Telegram chat ID" />
          <button className="btn">Link Telegram</button>
        </div>
        <div className="card space-y-4">
          <SectionTitle title="Exchange Accounts" />
          <input className="input" placeholder="API key encrypted storage" />
          <button className="btn">Add Exchange</button>
        </div>
      </div>
    </div>
  )
}
