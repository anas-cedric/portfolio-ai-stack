'use client';

import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

interface PortfolioDonutChartProps {
  data: Array<{ name: string; value: number; color: string }>;
  // We can enhance this later with more specific types based on actual portfolioData structure
}

const PortfolioDonutChart: React.FC<PortfolioDonutChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return <p>No portfolio data available to display chart.</p>;
  }

  const customTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-lg p-3 shadow-lg">
          <p className="font-semibold text-gray-900">{data.name}</p>
          <p className="text-blue-600 font-medium">{data.value.toFixed(1)}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart> 
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          outerRadius={130}
          innerRadius={80}
          fill="#8884d8"
          dataKey="value"
          nameKey="name"
          stroke="rgba(255, 255, 255, 0.2)"
          strokeWidth={2}
        >
          {data.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={entry.color}
              className="hover:opacity-80 transition-opacity duration-200"
            />
          ))}
        </Pie>
        <Tooltip content={customTooltip} />
      </PieChart>
    </ResponsiveContainer>
  );
};

export default PortfolioDonutChart;
