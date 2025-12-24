'use client'

import { useQuery } from '@tanstack/react-query'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { formatNumber } from '@/lib/utils'
import { apiService } from '@/lib/api'

interface StreamingChartProps {
  data?: any
}

export default function StreamingChart({ data }: StreamingChartProps) {
  // Fetch daily streaming data from API
  const { data: dailyData, isLoading } = useQuery({
    queryKey: ['streaming-daily'],
    queryFn: () => apiService.getDailyStreaming(30),
    refetchInterval: 60000, // Refetch every minute
  })

  if (isLoading) {
    return (
      <div className="h-[300px] flex items-center justify-center">
        <div className="animate-pulse text-gray-400">Loading streaming data...</div>
      </div>
    )
  }

  // Transform API data for the chart
  const chartData = transformDataForChart(dailyData?.data || [])

  if (chartData.length === 0) {
    return (
      <div className="h-[300px] flex items-center justify-center">
        <div className="text-gray-400">No streaming data available</div>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={chartData}>
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
          formatter={(value: number, name: string) => [formatNumber(value), name]}
          contentStyle={{
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            border: 'none',
            borderRadius: '8px',
            color: '#F3F4F6'
          }}
          labelFormatter={(label) => `Day ${label}`}
        />
        <Legend />
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

function transformDataForChart(apiData: any[]): Array<{ day: number; spotify: number; apple: number }> {
  if (!Array.isArray(apiData) || apiData.length === 0) {
    return []
  }

  return apiData.map((row, index) => {
    // Handle different possible field names from the API
    const spotifyStreams = row.spotify_streams || row.spotify || 0
    const appleStreams = row.apple_streams || row.apple || 0

    // Extract day from date if available, otherwise use index
    let day = index + 1
    if (row.date) {
      const date = new Date(row.date)
      day = date.getDate()
    }

    return {
      day,
      spotify: Number(spotifyStreams) || 0,
      apple: Number(appleStreams) || 0,
    }
  })
}
