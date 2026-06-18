import React from "react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

interface EquityChartProps {
  data: Array<{ date: string; value: number }>;
}

export const EquityChart: React.FC<EquityChartProps> = ({ data }) => {
  const chartData = data.map((d) => ({
    ...d,
    value: Number(d.value),
  }));

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h3 className="text-lg font-semibold mb-4 text-gray-200">Equity Curve</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="date" stroke="#9CA3AF" />
          <YAxis stroke="#9CA3AF" />
          <Tooltip
            contentStyle={{ backgroundColor: "#1F2937", border: "1px solid #374151" }}
            labelStyle={{ color: "#E5E7EB" }}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#10B981"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6, fill: "#059669" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};