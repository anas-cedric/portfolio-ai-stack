'use client';

import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface PortfolioDonutChartProps {
  data: Array<{ name: string; value: number; color: string }>;
  // We can enhance this later with more specific types based on actual portfolioData structure
}

const PortfolioDonutChart: React.FC<PortfolioDonutChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return <p>No portfolio data available to display chart.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart> 
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          // label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
          outerRadius={120} // Adjust as needed
          innerRadius={70}  // This makes it a donut chart
          fill="#8884d8"
          dataKey="value"
          nameKey="name"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip />
        {/* <Legend /> */}
        {/* We will build a custom legend as per the design later */}
      </PieChart>
    </ResponsiveContainer>
  );
};

export default PortfolioDonutChart;
