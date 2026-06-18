import { api } from "./api";
import { PortfolioAnalyticsRequestSchema, PortfolioAnalyticsResponseSchema } from "../schemas/analytics";

export const portfolioAnalyticsApi = {
  getAnalytics: async (params?: {
    portfolio_id?: string;
    date_from?: string;
    date_to?: string;
    risk_free_rate?: number;
  }) => {
    const response = await api.post("/portfolio/analytics", {
      portfolio_id: params?.portfolio_id,
      date_from: params?.date_from,
      date_to: params?.date_to,
      risk_free_rate: params?.risk_free_rate ?? 0,
    });
    return PortfolioAnalyticsResponseSchema.parse(response.data);
  },

  getHistory: async (period_type?: string) => {
    const response = await api.get("/portfolio/analytics/history", {
      params: { period_type },
    });
    return response.data;
  },
};