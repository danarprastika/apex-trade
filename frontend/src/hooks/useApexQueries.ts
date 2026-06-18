import { useQuery } from '@tanstack/react-query'
import { adminApi, authApi, healthApi, marketApi, notificationApi, portfolioApi, riskApi, tradingApi } from '../services/api'
import { journalApi as journalQueryApi } from '../services/journalApi'

export function useCurrentUser() {
  return useQuery({ queryKey: ['currentUser'], queryFn: authApi.me })
}

export function useHealth() {
  return useQuery({ queryKey: ['health'], queryFn: healthApi.health })
}

export function useAssets() {
  return useQuery({ queryKey: ['assets'], queryFn: marketApi.assets })
}

export function useMarketPairs() {
  return useQuery({ queryKey: ['marketPairs'], queryFn: marketApi.pairs })
}

export function useStrategies() {
  return useQuery({ queryKey: ['strategies'], queryFn: tradingApi.strategies })
}

export function useSignals() {
  return useQuery({ queryKey: ['signals'], queryFn: tradingApi.signals })
}

export function useOrders() {
  return useQuery({ queryKey: ['orders'], queryFn: tradingApi.orders })
}

export function usePortfolio() {
  return useQuery({ queryKey: ['portfolio'], queryFn: portfolioApi.portfolio })
}

export function usePortfolioSnapshots() {
  return useQuery({ queryKey: ['portfolioSnapshots'], queryFn: portfolioApi.snapshots })
}

export function useRiskProfile() {
  return useQuery({ queryKey: ['riskProfile'], queryFn: riskApi.profile })
}

export function useRiskEvents() {
  return useQuery({ queryKey: ['riskEvents'], queryFn: riskApi.events })
}

export function useNotifications() {
  return useQuery({ queryKey: ['notifications'], queryFn: notificationApi.notifications })
}

export function useAuditLogs() {
  return useQuery({ queryKey: ['auditLogs'], queryFn: adminApi.audit })
}

export function useAdminUsers() {
  return useQuery({ queryKey: ['adminUsers'], queryFn: adminApi.users })
}

export function useJournals(filters?: Parameters<typeof journalQueryApi.list>[0]) {
  return useQuery({ queryKey: ['journalList', filters], queryFn: () => journalQueryApi.list(filters).then((response) => response.data) })
}

export function useJournalAnalytics(filters?: Parameters<typeof journalQueryApi.list>[0]) {
  return useQuery({ queryKey: ['journalAnalytics', filters], queryFn: () => journalQueryApi.getAnalytics(filters).then((response) => response.data) })
}

export function useJournalTags(query = '', limit = 10) {
  return useQuery({ queryKey: ['journalTags', query, limit], queryFn: () => journalQueryApi.autocompleteTags(query, limit).then((response) => response.data) })
}
