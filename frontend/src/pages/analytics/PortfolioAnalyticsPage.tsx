import React, { useEffect } from "react";
import { MetricsGrid } from "../components/analytics/MetricsGrid";
import { EquityChart } from "../components/analytics/EquityChart";
import { usePortfolioAnalytics } from "../../hooks/usePortfolioAnalytics";
import { TrendingUp } from "lucide-react";

export const PortfolioAnalyticsPage: React.FC = () => {
  const { metrics, isLoading, error } = usePortfolioAnalytics();

  useEffect(() => {
    document.title = "Portfolio Analytics | APEX";
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
        <p className="text-red-400">Error loading analytics: {error}</p>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="bg-gray-800 rounded-lg p-8 text-center">
        <p className="text-gray-400">No analytics data available</p>
      </div>
    );
  }

  const equityData = metrics.chart_data?.equity || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <TrendingUp className="h-8 w-8 text-emerald-500" />
        <h1 className="text-3xl font-bold text-gray-100">Portfolio Analytics</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <MetricsGrid metrics={metrics.metrics} />
        </div>
        <div className="space-y-4">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h3 className="text-sm font-medium text-gray-400 mb-2">Total Trades</h3>
            <p className="text-3xl font-bold text-gray-200">{metrics.metrics.total_trades}</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h3 className="text-sm font-medium text-gray-400 mb-2">Winning Trades</h3>
            <p className="text-2xl font-bold text-green-400">{metrics.metrics.winning_trades}</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h3 className="text-sm font-medium text-gray-400 mb-2">Gross Profit</h3>
            <p className="text-2xl font-bold text-green-400">
              ${metrics.metrics.gross_profit?.toFixed(2) ?? "0.00"}
            </p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h3 className="text-sm font-medium text-gray-400 mb-2">Gross Loss</h3>
            <p className="text-2xl font-bold text-red-400">
              ${Math.abs(metrics.metrics.gross_loss ?? 0).toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {equityData.length > 0 && (
        <EquityChart data={equityData as Array<{ date: string; value: number }>} />
      )}

      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <h3 className="text-sm font-medium text-gray-400 mb-2">Period</h3>
        <p className="text-gray-200">
          {metrics.metrics.period_start
            ? new Date(metrics.metrics.period_start).toLocaleDateString()
            : "N/A"}{" "}
          -{" "}
          {metrics.metrics.period_end
            ? new Date(metrics.metrics.period_end).toLocaleDateString()
            : "N/A"}
        </p>
      </div>
    </div>
  );
};