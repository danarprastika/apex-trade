import React from "react";
import { MetricsCard } from "./MetricsCard";
import type { PerformanceMetricsSchema } from "../../schemas/analytics";

interface MetricsGridProps {
  metrics: PerformanceMetricsSchema;
}

export const MetricsGrid: React.FC<MetricsGridProps> = ({ metrics }) => {
  const metricItems = [
    {
      title: "Total Return",
      value: metrics.total_return,
      format: "percent" as const,
      description: "Overall portfolio performance",
    },
    {
      title: "Sharpe Ratio",
      value: metrics.sharpe_ratio,
      format: "ratio" as const,
      description: "Risk-adjusted returns vs volatility",
    },
    {
      title: "Sortino Ratio",
      value: metrics.sortino_ratio,
      format: "ratio" as const,
      description: "Downside risk-adjusted returns",
    },
    {
      title: "Calmar Ratio",
      value: metrics.calmar_ratio,
      format: "ratio" as const,
      description: "Return vs max drawdown",
    },
    {
      title: "Profit Factor",
      value: metrics.profit_factor,
      format: "ratio" as const,
      description: "Gross profit / gross loss",
    },
    {
      title: "Win Rate",
      value: metrics.win_rate !== undefined ? metrics.win_rate : null,
      format: "percent" as const,
      description: "Percentage of winning trades",
    },
    {
      title: "Expectancy",
      value: metrics.expectancy,
      format: "number" as const,
      description: "Expected value per trade",
    },
    {
      title: "Max Drawdown",
      value: metrics.max_drawdown !== undefined && metrics.max_drawdown !== null
        ? -Math.abs(metrics.max_drawdown)
        : null,
      format: "percent" as const,
      description: "Largest peak-to-trough decline",
    },
    {
      title: "Risk-Adjusted Return",
      value: metrics.risk_adjusted_return,
      format: "ratio" as const,
      description: "Return / volatility",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {metricItems.map((item) => (
        <MetricsCard
          key={item.title}
          title={item.title}
          value={item.value}
          format={item.format}
          description={item.description}
        />
      ))}
    </div>
  );
};