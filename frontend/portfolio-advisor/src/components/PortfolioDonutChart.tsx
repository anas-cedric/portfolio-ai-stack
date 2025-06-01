'use client';

import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

interface PortfolioDonutChartProps {
  data: Array<{ name: string; value: number; color: string }>;
  showCenterText?: boolean;
  // We can enhance this later with more specific types based on actual portfolioData structure
}

const PortfolioDonutChart: React.FC<PortfolioDonutChartProps> = ({ data, showCenterText = true }) => {
  if (!data || data.length === 0) {
    return <p>No portfolio data available to display chart.</p>;
  }

  // Find ETF percentage for center display
  const etfData = data.find(d => d.name === 'ETF');
  const etfPercentage = etfData ? etfData.value : 0;

  const customTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-black/80 backdrop-blur-sm border border-white/20 rounded-lg p-3 shadow-lg">
          <p className="font-semibold text-white">{data.name}</p>
          <p className="text-white/80 font-medium">{data.value.toFixed(1)}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="relative w-full h-full">
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
            stroke="none"
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
      {/* Center text */}
      {showCenterText && (
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <div className="text-5xl font-bold text-white">{etfPercentage.toFixed(1)}%</div>
          <div className="text-sm text-white/60 mt-1">ETF</div>
        </div>
      )}
    </div>
  );
};

export default PortfolioDonutChart;
