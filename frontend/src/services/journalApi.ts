import { api } from './api'
import type {
  JournalAnalyticsSummary,
  JournalCreatePayload,
  JournalFilters,
  JournalListResponse,
  JournalStatistics,
  JournalTag,
  JournalUpdatePayload,
  TradeJournal,
  TradeScreenshot
} from '../types/api'

const normalizeFilters = (filters?: JournalFilters) => {
  const params: Record<string, string | number | string[] | undefined> = {
    page: filters?.page,
    size: filters?.size,
    sort_by: filters?.sort_by,
    sort_order: filters?.sort_order,
    search: filters?.search,
    date_from: filters?.date_from,
    date_to: filters?.date_to,
    strategy_ids: filters?.strategy_ids,
    outcome: filters?.outcome,
    tags: filters?.tags
  }

  if (filters?.risk_score_range) {
    params.risk_score_range = [String(filters.risk_score_range[0]), String(filters.risk_score_range[1])]
  }

  return params
}

export const journalApi = {
  list: (filters?: JournalFilters) => api.get<JournalListResponse>('/v1/journal/trades', { params: normalizeFilters(filters) }),
  get: (journalId: string) => api.get<TradeJournal>(`/v1/journal/trades/${journalId}`),
  create: (payload: JournalCreatePayload) => api.post<TradeJournal>('/v1/journal/trades', payload),
  update: (journalId: string, payload: JournalUpdatePayload) => api.patch<TradeJournal>(`/v1/journal/trades/${journalId}`, payload),
  remove: (journalId: string) => api.delete(`/v1/journal/trades/${journalId}`),
  addScreenshot: (journalId: string, url: string, caption?: string | null, stage?: string | null) =>
    api.post<TradeScreenshot>(`/v1/journal/trades/${journalId}/screenshots`, undefined, { params: { url, caption, stage } }),
  removeScreenshot: (journalId: string, screenshotId: string) =>
    api.delete(`/v1/journal/trades/${journalId}/screenshots/${screenshotId}`),
  bulkTag: (tradeIds: string[], tagNames: string[]) =>
    api.post('/v1/journal/trades/bulk-tag', undefined, { params: { trade_ids: tradeIds, tag_names: tagNames } }),
  search: (query: string, limit = 20) => api.get<TradeJournal[]>('/v1/journal/trades/search', { params: { q: query, limit } }),
  autocompleteTags: (query = '', limit = 10) =>
    api.get<JournalTag[]>('/v1/journal/trades/tags/autocomplete', { params: { q: query, limit } }),
  getSummaryStats: (filters?: JournalFilters) => api.get<JournalStatistics>('/v1/journal/trades/stats/summary', { params: normalizeFilters(filters) }),
  getStatsByTag: (filters?: JournalFilters) => api.get<Record<string, JournalStatistics>>('/v1/journal/trades/stats/by-tag', { params: normalizeFilters(filters) }),
  getAnalytics: (filters?: JournalFilters) => api.get<JournalAnalyticsSummary>('/v1/journal/trades/analytics/performance-breakdown', { params: normalizeFilters(filters) }),
  exportCsv: (filters?: JournalFilters) => api.get('/v1/journal/trades/export/csv', { params: normalizeFilters(filters), responseType: 'blob' })
}
