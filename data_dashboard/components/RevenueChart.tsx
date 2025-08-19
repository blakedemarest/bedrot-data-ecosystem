'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { formatCurrency } from '@/lib/utils'

interface RevenueChartProps {
  data: any[]
}

export default function RevenueChart({ data }: RevenueChartProps) {
  // Transform data for chart
  const chartData = data.slice(-12).map(item => ({
    month: item.month,
    actual: item.actual_revenue,
    expected: item.expected_revenue,
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
        <XAxis 
          dataKey="month" 
          className="text-xs"
          tick={{ fill: '#9CA3AF' }}
        />
        <YAxis 
          className="text-xs"
          tick={{ fill: '#9CA3AF' }}
          tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`}
        />
        <Tooltip 
          formatter={(value: number) => formatCurrency(value)}
          contentStyle={{
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            border: 'none',
            borderRadius: '8px',
            color: '#F3F4F6'
          }}
        />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="actual" 
          stroke="#10B981" 
          strokeWidth={2}
          dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6 }}
          name="Actual Revenue"
        />
        <Line 
          type="monotone" 
          dataKey="expected" 
          stroke="#6366F1" 
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={{ fill: '#6366F1', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6 }}
          name="Expected Revenue"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}