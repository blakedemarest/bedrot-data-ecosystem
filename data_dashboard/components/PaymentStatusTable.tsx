'use client'

import { formatCurrency, formatDate, cn } from '@/lib/utils'
import { CheckCircle, Clock, AlertCircle } from 'lucide-react'

interface PaymentStatusTableProps {
  data: any[]
}

export default function PaymentStatusTable({ data }: PaymentStatusTableProps) {
  // Get last 6 months of data
  const recentData = data.slice(-6).reverse()

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'paid':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusBadge = (status: string) => {
    const baseClasses = 'px-2 py-1 text-xs font-medium rounded-full'
    switch (status) {
      case 'paid':
        return cn(baseClasses, 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400')
      case 'pending':
        return cn(baseClasses, 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400')
      default:
        return cn(baseClasses, 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400')
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead>
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Month
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Expected
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Actual
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Variance
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Payment Date
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
          {recentData.map((row, index) => {
            const variance = row.variance || 0
            const varianceColor = variance >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
            
            return (
              <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                  {row.month}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                  {formatCurrency(row.expected_revenue || 0)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                  {formatCurrency(row.actual_revenue || 0)}
                </td>
                <td className={cn('px-4 py-3 whitespace-nowrap text-sm font-medium', varianceColor)}>
                  {variance >= 0 ? '+' : ''}{formatCurrency(Math.abs(variance))}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(row.payment_status)}
                    <span className={getStatusBadge(row.payment_status)}>
                      {row.payment_status?.toUpperCase() || 'UNKNOWN'}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {row.expected_payment_date ? formatDate(row.expected_payment_date) : '-'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}