import { create } from "zustand";
import { portfolioAnalyticsApi } from "../services/portfolio-analytics";
import { PortfolioAnalyticsResponseSchema } from "../schemas/analytics";

interface PortfolioAnalyticsState {
  metrics: PortfolioAnalyticsResponseSchema | null;
  isLoading: boolean;
  error: string | null;
  fetchAnalytics: (params?: Parameters<typeof portfolioAnalyticsApi.getAnalytics>[0]) => Promise<void>;
}

export const usePortfolioAnalyticsStore = create<PortfolioAnalyticsState>((set) => ({
  metrics: null,
  isLoading: false,
  error: null,
  fetchAnalytics: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const data = await portfolioAnalyticsApi.getAnalytics(params);
      set({ metrics: data, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Failed to fetch analytics",
        isLoading: false,
      });
    }
  },
}));