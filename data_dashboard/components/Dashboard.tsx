'use client'

import { useQuery } from '@tanstack/react-query'
import { apiService } from '@/lib/api'
import KPICard from './KPICard'
import RevenueChart from './RevenueChart'
import StreamingChart from './StreamingChart'
import DistributorPieChart from './DistributorPieChart'
import PaymentStatusTable from './PaymentStatusTable'
import { DollarSign, Music, TrendingUp, Users } from 'lucide-react'
import { formatCurrency, formatNumber } from '@/lib/utils'

export default function Dashboard() {
  // Fetch KPI Summary
  const { data: kpiData, isLoading: kpiLoading } = useQuery({
    queryKey: ['kpis-summary'],
    queryFn: apiService.getKPISummary,
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  // Fetch Monthly Revenue
  const { data: monthlyData, isLoading: monthlyLoading } = useQuery({
    queryKey: ['monthly-revenue'],
    queryFn: () => apiService.getMonthlyRevenue(),
  })

  // Fetch Streaming Summary
  const { data: streamingData, isLoading: streamingLoading } = useQuery({
    queryKey: ['streaming-summary'],
    queryFn: apiService.getStreamingSummary,
  })

  // Fetch Revenue by Distributor
  const { data: distributorData, isLoading: distributorLoading } = useQuery({
    queryKey: ['revenue-distributor'],
    queryFn: apiService.getRevenueDistributor,
  })

  const isLoading = kpiLoading || monthlyLoading || streamingLoading || distributorLoading

  if (isLoading) {
    return <LoadingSkeleton />
  }

  const kpis = kpiData?.data || {}
  const streaming = streamingData?.data || {}
  const monthly = monthlyData?.data || []
  const distributor = distributorData?.data || {}

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              BEDROT Data Dashboard
            </h1>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Last updated: {new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <KPICard
            title="Total Revenue"
            value={formatCurrency(kpis.total_revenue || 0)}
            icon={<DollarSign className="h-6 w-6" />}
            trend={12.5}
            description="All-time earnings"
          />
          <KPICard
            title="Total Streams"
            value={formatNumber(kpis.total_streams || 0)}
            icon={<Music className="h-6 w-6" />}
            trend={8.2}
            description="Across all platforms"
          />
          <KPICard
            title="Avg Revenue/Stream"
            value={formatCurrency(kpis.average_revenue_per_stream || 0)}
            icon={<TrendingUp className="h-6 w-6" />}
            trend={-2.1}
            description="Industry average: $0.003"
          />
          <KPICard
            title="Artists"
            value={kpis.artist_count || 0}
            icon={<Users className="h-6 w-6" />}
            description={`Top: ${kpis.top_artist || 'N/A'}`}
          />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Revenue Trend Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              Monthly Revenue Trend
            </h2>
            <RevenueChart data={monthlyData?.data || []} />
          </div>

          {/* Streaming Trend Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              Streaming Performance
            </h2>
            <StreamingChart data={streamingData?.data || {}} />
          </div>
        </div>

        {/* Distributor Breakdown and Payment Status */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Distributor Pie Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              Revenue by Distributor
            </h2>
            <DistributorPieChart data={distributorData?.data || {}} />
          </div>

          {/* Payment Status Table */}
          <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              Payment Status
            </h2>
            <PaymentStatusTable data={monthlyData?.data || []} />
          </div>
        </div>
      </main>
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="h-8 w-64 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mb-2" />
              <div className="h-8 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}