'use client'

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { formatNumber } from '@/lib/utils'

interface StreamingChartProps {
  data: any
}

export default function StreamingChart({ data }: StreamingChartProps) {
  // Mock daily data for visualization
  const dailyData = generateDailyData()

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={dailyData}>
        <defs>
          <linearGradient id="colorSpotify" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#1DB954" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#1DB954" stopOpacity={0.1}/>
          </linearGradient>
          <linearGradient id="colorApple" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#FC3C44" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#FC3C44" stopOpacity={0.1}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
        <XAxis 
          dataKey="day" 
          className="text-xs"
          tick={{ fill: '#9CA3AF' }}
        />
        <YAxis 
          className="text-xs"
          tick={{ fill: '#9CA3AF' }}
          tickFormatter={formatNumber}
        />
        <Tooltip 
          formatter={(value: number) => formatNumber(value)}
          contentStyle={{
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            border: 'none',
            borderRadius: '8px',
            color: '#F3F4F6'
          }}
        />
        <Area 
          type="monotone" 
          dataKey="spotify" 
          stroke="#1DB954" 
          fillOpacity={1} 
          fill="url(#colorSpotify)"
          strokeWidth={2}
          name="Spotify"
        />
        <Area 
          type="monotone" 
          dataKey="apple" 
          stroke="#FC3C44" 
          fillOpacity={1} 
          fill="url(#colorApple)"
          strokeWidth={2}
          name="Apple Music"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

function generateDailyData() {
  const days = []
  const today = new Date()
  
  for (let i = 29; i >= 0; i--) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)
    
    days.push({
      day: date.getDate(),
      spotify: Math.floor(Math.random() * 2000) + 1500,
      apple: Math.floor(Math.random() * 200) + 50,
    })
  }
  
  return days
}