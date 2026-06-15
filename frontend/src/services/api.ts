import axios from 'axios'
import type {
  AuditLog,
  Asset,
  Candle,
  HealthResponse,
  MarketPair,
  Notification,
  Order,
  PaperOrder,
  Portfolio,
  PortfolioSnapshot,
  RiskDecision,
  RiskEvent,
  RiskProfile,
  Signal,
  Strategy,
  TokenResponse,
  User
} from '../types/api'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('apex_access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('apex_access_token')
      localStorage.removeItem('apex_refresh_token')
      localStorage.removeItem('apex_username')
      localStorage.removeItem('apex_role')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login: async (username: string, password: string): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/v1/auth/login', { username, password })
    localStorage.setItem('apex_access_token', response.data.access_token)
    localStorage.setItem('apex_refresh_token', response.data.refresh_token)
    return response.data
  },
  me: async (): Promise<User> => {
    const response = await api.get<User>('/v1/users/me')
    localStorage.setItem('apex_role', response.data.role)
    localStorage.setItem('apex_username', response.data.username)
    return response.data
  }
}

export const healthApi = {
  health: async (): Promise<HealthResponse> => api.get<HealthResponse>('/v1/health').then((response) => response.data),
  metrics: async (): Promise<HealthResponse> => api.get<HealthResponse>('/v1/metrics').then((response) => response.data)
}

export const marketApi = {
  assets: async (): Promise<Asset[]> => api.get<Asset[]>('/v1/market/assets').then((response) => response.data),
  pairs: async (): Promise<MarketPair[]> => api.get<MarketPair[]>('/v1/market/pairs').then((response) => response.data),
  candles: async (marketPairId: string, timeframe = '1h', limit = 100): Promise<Candle[]> =>
    api.get<Candle[]>('/v1/market/candles', { params: { market_pair_id: marketPairId, timeframe, limit } }).then((response) => response.data)
}

export const tradingApi = {
  strategies: async (): Promise<Strategy[]> => api.get<Strategy[]>('/v1/trading/strategies').then((response) => response.data),
  signals: async (): Promise<Signal[]> => api.get<Signal[]>('/v1/trading/signals').then((response) => response.data),
  orders: async (): Promise<Order[]> => api.get<Order[]>('/v1/trading/orders').then((response) => response.data),
  createSignal: async (payload: {
    strategy_id: string
    market_pair_id: string
    signal_type: string
    confidence: number
    entry_price: number
    stop_loss?: number | null
    take_profit?: number | null
    reason: string
  }): Promise<Signal> => api.post<Signal>('/v1/trading/signals', payload).then((response) => response.data),
  createOrder: async (payload: {
    exchange_account_id: string
    signal_id?: string | null
    order_type: string
    side: string
    quantity: number
    price?: number | null
  }): Promise<Order> => api.post<Order>('/v1/trading/orders', payload).then((response) => response.data),
  createPaperOrder: async (payload: {
    market_pair_id: string
    strategy_id: string
    signal_id?: string | null
    side: string
    quantity: number
    price: number
  }): Promise<PaperOrder> => api.post<PaperOrder>('/v1/trading/paper-orders', payload).then((response) => response.data)
}

export const portfolioApi = {
  portfolio: async (): Promise<Portfolio> => api.get<Portfolio>('/v1/portfolio').then((response) => response.data),
  snapshots: async (): Promise<PortfolioSnapshot[]> => api.get<PortfolioSnapshot[]>('/v1/portfolio/snapshots').then((response) => response.data)
}

export const riskApi = {
  profile: async (): Promise<RiskProfile> => api.get<RiskProfile>('/v1/risk/profile').then((response) => response.data),
  events: async (): Promise<RiskEvent[]> => api.get<RiskEvent[]>('/v1/risk/events').then((response) => response.data),
  validate: async (riskScore: number, requestedPositionSize?: number | null): Promise<RiskDecision> =>
    api.post<RiskDecision>('/v1/risk/validate', undefined, { params: { risk_score: riskScore, requested_position_size: requestedPositionSize ?? '' } }).then((response) => response.data)
}

export const notificationApi = {
  notifications: async (): Promise<Notification[]> => api.get<Notification[]>('/v1/notifications').then((response) => response.data)
}

export const adminApi = {
  users: async (): Promise<User[]> => api.get<User[]>('/v1/admin/users').then((response) => response.data),
  audit: async (): Promise<AuditLog[]> => api.get<AuditLog[]>('/v1/admin/audit').then((response) => response.data)
}
