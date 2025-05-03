'use client';

import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface PortfolioPieChartProps {
  allocations: Record<string, number>;
}

// Define a set of colors for the pie slices
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d', '#ffc658', '#a4de6c', '#d0ed57', '#ffc658'];

const PortfolioPieChart: React.FC<PortfolioPieChartProps> = ({ allocations }) => {
  if (!allocations || Object.keys(allocations).length === 0) {
    return <div className="text-center text-gray-500">No allocation data to display.</div>;
  }

  // Transform allocations into the format Recharts expects
  const data = Object.entries(allocations).map(([ticker, percentage]) => ({
    name: ticker,
    value: percentage, // Use the percentage directly as the value
  }));

  return (
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            // label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
            nameKey="name"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PortfolioPieChart;
