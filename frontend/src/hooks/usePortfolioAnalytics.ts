import { useQuery } from "@tanstack/react-query";
import { usePortfolioAnalyticsStore } from "../store/analyticsStore";
import { portfolioAnalyticsApi } from "../services/portfolio-analytics";
import { useEffect } from "react";
import type { PortfolioAnalyticsRequestSchema } from "../schemas/analytics";

export const usePortfolioAnalytics = (params?: Parameters<typeof portfolioAnalyticsApi.getAnalytics>[0]) => {
  const { fetchAnalytics, metrics, isLoading, error } = usePortfolioAnalyticsStore();

  const query = useQuery({
    queryKey: ["portfolio-analytics", params],
    queryFn: () => portfolioAnalyticsApi.getAnalytics(params),
    staleTime: 5 * 60 * 1000,
  });

  useEffect(() => {
    if (!query.data) {
      fetchAnalytics(params);
    }
  }, [query.data, fetchAnalytics, params]);

  return {
    metrics: query.data || metrics,
    isLoading: query.isLoading || isLoading,
    error: query.error?.message || error,
    refetch: query.refetch,
  };
};