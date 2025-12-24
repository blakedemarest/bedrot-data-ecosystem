/**
 * API Service for BEDROT Data Dashboard
 * Provides typed functions for all backend API endpoints
 */

const API_BASE = '/api'

interface APIResponse<T> {
  success: boolean
  data: T
  metadata?: {
    sources?: string[]
    last_updated?: string
    limitations?: string[]
    refresh_interval_seconds?: number
  }
}

interface KPISummary {
  total_revenue: number
  total_streams: number
  average_revenue_per_stream: number
  artist_count: number
  top_artist: string
}

interface MonthlyRevenue {
  month: string
  expected_revenue: number
  actual_revenue: number
  variance: number
  payment_status: 'paid' | 'pending' | 'unknown'
  expected_payment_date: string | null
}

interface StreamingSummary {
  total_streams: number
  by_distributor: {
    distrokid: number
    toolost: number
  }
  by_platform: {
    spotify: number
    apple: number
    other: number
  }
}

interface DailyStreaming {
  date: string
  spotify: number
  apple: number
  total: number
}

interface DistributorRevenue {
  distrokid: number
  toolost: number
  total: number
  percentages: {
    distrokid: number
    toolost: number
  }
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<APIResponse<T>> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

export const apiService = {
  // KPI Endpoints
  async getKPISummary(): Promise<APIResponse<KPISummary>> {
    return fetchAPI<KPISummary>('/kpis/summary')
  },

  async getKPIRealtime(): Promise<APIResponse<any>> {
    return fetchAPI('/kpis/realtime')
  },

  async getKPIGoals(): Promise<APIResponse<any>> {
    return fetchAPI('/kpis/goals')
  },

  async getKPIAlerts(): Promise<APIResponse<any>> {
    return fetchAPI('/kpis/alerts')
  },

  // Revenue Endpoints
  async getMonthlyRevenue(months?: number): Promise<APIResponse<MonthlyRevenue[]>> {
    const params = months ? `?months=${months}` : ''
    return fetchAPI<MonthlyRevenue[]>(`/revenue/monthly${params}`)
  },

  async getRevenuePlatform(): Promise<APIResponse<any>> {
    return fetchAPI('/revenue/platform')
  },

  async getRevenueArtist(): Promise<APIResponse<any>> {
    return fetchAPI('/revenue/artist')
  },

  async getRevenueDistributor(): Promise<APIResponse<DistributorRevenue>> {
    return fetchAPI<DistributorRevenue>('/revenue/distributor')
  },

  async getRevenueDelays(): Promise<APIResponse<any>> {
    return fetchAPI('/revenue/delays')
  },

  async getRPSRates(): Promise<APIResponse<any>> {
    return fetchAPI('/revenue/rps-rates')
  },

  // Streaming Endpoints
  async getStreamingSummary(): Promise<APIResponse<StreamingSummary>> {
    return fetchAPI<StreamingSummary>('/streaming/summary')
  },

  async getDailyStreaming(days?: number): Promise<APIResponse<DailyStreaming[]>> {
    const params = days ? `?days=${days}` : ''
    return fetchAPI<DailyStreaming[]>(`/streaming/daily${params}`)
  },

  async getStreamingGrowth(period?: string): Promise<APIResponse<any>> {
    const params = period ? `?period=${period}` : ''
    return fetchAPI(`/streaming/growth${params}`)
  },

  async getSpotifyAudience(): Promise<APIResponse<any>> {
    return fetchAPI('/streaming/spotify-audience')
  },

  // Data Access Endpoints
  async getDataFiles(): Promise<APIResponse<any>> {
    return fetchAPI('/data/files')
  },

  async getDataFile(filename: string, page?: number, pageSize?: number): Promise<APIResponse<any>> {
    const params = new URLSearchParams()
    if (page) params.append('page', String(page))
    if (pageSize) params.append('page_size', String(pageSize))
    const queryString = params.toString() ? `?${params.toString()}` : ''
    return fetchAPI(`/data/file/${encodeURIComponent(filename)}${queryString}`)
  },

  async getDataMetadata(filename: string): Promise<APIResponse<any>> {
    return fetchAPI(`/data/metadata/${encodeURIComponent(filename)}`)
  },

  async getDataSchema(): Promise<APIResponse<any>> {
    return fetchAPI('/data/schema')
  },

  async reloadCache(): Promise<APIResponse<{ message: string }>> {
    return fetchAPI('/data/reload-cache', { method: 'POST' })
  },
}

export type {
  APIResponse,
  KPISummary,
  MonthlyRevenue,
  StreamingSummary,
  DailyStreaming,
  DistributorRevenue
}
