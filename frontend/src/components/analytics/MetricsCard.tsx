import React from "react";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import type { PerformanceMetricsSchema } from "../../schemas/analytics";

interface MetricsCardProps {
  title: string;
  value: number | null | undefined;
  format?: "percent" | "number" | "ratio";
  precision?: number;
  description?: string;
}

export const MetricsCard: React.FC<MetricsCardProps> = ({
  title,
  value,
  format = "number",
  precision = 2,
  description,
}) => {
  const displayValue = value !== null && value !== undefined
    ? format === "percent"
      ? `${(value * 100).toFixed(precision)}%`
      : format === "ratio"
        ? value.toFixed(precision)
        : value.toFixed(precision)
    : "N/A";

  const isPositive = value !== null && value !== undefined && value >= 0;
  const isNegative = value !== null && value !== undefined && value < 0;

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className={`text-2xl font-bold mt-1 ${isPositive ? "text-green-400" : isNegative ? "text-red-400" : "text-gray-300"}`}>
            {displayValue}
          </p>
          {description && (
            <p className="text-xs text-gray-500 mt-1">{description}</p>
          )}
        </div>
        {isPositive && value !== null && (
          <ArrowUpRight className="h-5 w-5 text-green-400" />
        )}
        {isNegative && value !== null && (
          <ArrowDownRight className="h-5 w-5 text-red-400" />
        )}
      </div>
    </div>
  );
};