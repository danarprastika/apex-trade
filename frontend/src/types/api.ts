export type UserRole = 'VIEWER' | 'TRADER' | 'ADMIN' | 'SUPER_ADMIN'

export type User = {
  id: string
  username: string
  email: string
  role: UserRole
  status: string
  created_at: string
  updated_at: string
}

export type TokenResponse = {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}

export type HealthResponse = {
  status: 'healthy' | 'degraded'
  service: 'backend'
  database: 'ok' | 'error' | 'not_checked'
  redis: 'ok' | 'error' | 'not_checked'
}

export type Asset = {
  id: string
  symbol: string
  name: string | null
  asset_type: string
  status: string
  created_at: string
  updated_at: string
}

export type MarketPair = {
  id: string
  exchange_id: string
  base_asset_id: string
  quote_asset_id: string
  symbol: string
  status: string
  created_at: string
  updated_at: string
}

export type Candle = {
  id: number
  market_pair_id: string
  timeframe: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  open_time: string
  close_time: string
}

export type Strategy = {
  id: string
  name: string
  code: string
  version: string
  description: string | null
  strategy_type: string
  status: string
  created_at: string
  updated_at: string
}

export type Signal = {
  id: string
  strategy_id: string
  market_pair_id: string
  signal_type: 'BUY' | 'SELL' | 'HOLD' | string
  confidence: number
  entry_price: number
  stop_loss: number | null
  take_profit: number | null
  reason: string
  signal_time: string
  status: string
  created_at: string
  updated_at: string
}

export type Order = {
  id: string
  exchange_account_id: string
  signal_id: string | null
  exchange_order_id: string | null
  order_type: string
  side: string
  quantity: number
  price: number | null
  filled_quantity: number
  status: string
  created_at: string
  updated_at: string
}

export type Position = {
  id: string
  exchange_account_id: string
  market_pair_id: string
  strategy_id: string
  entry_order_id: string | null
  entry_price: number
  quantity: number
  current_price: number
  unrealized_pnl: number
  status: string
  opened_at: string
  closed_at: string | null
  created_at: string
  updated_at: string
}

export type Trade = {
  id: string
  position_id: string
  strategy_id: string
  entry_price: number
  exit_price: number
  quantity: number
  gross_profit: number
  net_profit: number
  profit_percentage: number
  duration_minutes: number
  opened_at: string
  closed_at: string
  created_at: string
  updated_at: string
}

export type Portfolio = {
  id: string
  user_id: string
  portfolio_name: string
  currency: string
  total_value: number
  cash_balance: number
  risk_score: number
  created_at: string
  updated_at: string
}

export type PaperOrder = {
  order: Order
  position: Position | null
  trade: Trade | null
  risk_allowed: boolean
  risk_reason: string
  message: string
}

export type PortfolioSnapshot = {
  id: number
  portfolio_id: string
  total_value: number
  cash_balance: number
  open_positions: number
  daily_pnl: number
  total_pnl: number
  captured_at: string
}

export type RiskProfile = {
  id: string
  user_id: string
  max_risk_per_trade: number
  max_daily_loss: number
  max_drawdown: number
  max_open_positions: number
  created_at: string
  updated_at: string
}

export type RiskDecision = {
  allowed: boolean
  reason: string
  risk_score: number
  position_size: number | null
}

export type RiskEvent = {
  id: string
  user_id: string
  event_type: string
  severity: string
  description: string
  created_at: string
  updated_at: string
}

export type Notification = {
  id: string
  user_id: string
  notification_type: string
  title: string
  message: string
  status: string
  sent_at: string | null
  created_at: string
  updated_at: string
}

export type AuditLog = {
  id: number
  user_id: string | null
  entity_type: string
  entity_id: string
  action: string
  old_value: Record<string, unknown> | null
  new_value: Record<string, unknown> | null
  ip_address: string | null
  created_at: string
}
