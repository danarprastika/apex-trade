import { z } from "zod";

export const PortfolioAnalyticsRequestSchema = z.object({
  portfolio_id: z.string().uuid().optional(),
  date_from: z.string().date().optional(),
  date_to: z.string().date().optional(),
  risk_free_rate: z.number().default(0),
});

export const PerformanceMetricsSchema = z.object({
  total_return: z.number().nullable().optional(),
  sharpe_ratio: z.number().nullable().optional(),
  sortino_ratio: z.number().nullable().optional(),
  calmar_ratio: z.number().nullable().optional(),
  profit_factor: z.number().nullable().optional(),
  win_rate: z.number().nullable().optional(),
  expectancy: z.number().nullable().optional(),
  max_drawdown: z.number().nullable().optional(),
  risk_adjusted_return: z.number().nullable().optional(),
  period_start: z.string().datetime().nullable().optional(),
  period_end: z.string().datetime().nullable().optional(),
  total_trades: z.number().int().default(0),
  winning_trades: z.number().int().default(0),
  losing_trades: z.number().int().default(0),
  gross_profit: z.number().nullable().optional(),
  gross_loss: z.number().nullable().optional(),
});

export const PortfolioAnalyticsResponseSchema = z.object({
  portfolio: z.object({
    id: z.string(),
    user_id: z.string(),
    portfolio_name: z.string(),
    currency: z.string(),
    total_value: z.number(),
    cash_balance: z.number(),
    risk_score: z.number(),
    created_at: z.string(),
    updated_at: z.string(),
  }).nullable().optional(),
  metrics: PerformanceMetricsSchema,
  chart_data: z.record(z.array(z.record(z.union([z.number(), z.string()])))),
});