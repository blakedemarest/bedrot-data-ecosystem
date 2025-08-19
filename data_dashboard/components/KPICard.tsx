'use client'

import { cn, getTrendColor, getTrendIcon } from '@/lib/utils'

interface KPICardProps {
  title: string
  value: string | number
  icon?: React.ReactNode
  trend?: number
  description?: string
  className?: string
}

export default function KPICard({
  title,
  value,
  icon,
  trend,
  description,
  className,
}: KPICardProps) {
  return (
    <div
      className={cn(
        'bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-lg transition-shadow',
        className
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
          {title}
        </h3>
        {icon && (
          <div className="text-gray-400 dark:text-gray-500">{icon}</div>
        )}
      </div>
      
      <div className="flex items-baseline space-x-2">
        <p className="text-2xl font-bold text-gray-900 dark:text-white">
          {value}
        </p>
        {trend !== undefined && (
          <span className={cn('text-sm font-medium', getTrendColor(trend))}>
            {getTrendIcon(trend)} {Math.abs(trend).toFixed(1)}%
          </span>
        )}
      </div>
      
      {description && (
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          {description}
        </p>
      )}
    </div>
  )
}