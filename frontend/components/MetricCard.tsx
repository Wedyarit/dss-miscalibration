"use client"

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'

interface MetricCardProps {
  title: string
  value: string | number
  description?: string
  trend?: 'up' | 'down' | 'neutral'
  variant?: 'default' | 'success' | 'warning' | 'danger'
}

export function MetricCard({ 
  title, 
  value, 
  description, 
  trend = 'neutral',
  variant = 'default' 
}: MetricCardProps) {
  const getVariantStyles = () => {
    switch (variant) {
      case 'success':
        return 'border-green-200 bg-green-50'
      case 'warning':
        return 'border-yellow-200 bg-yellow-50'
      case 'danger':
        return 'border-red-200 bg-red-50'
      default:
        return 'border-border bg-card'
    }
  }

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return '↗️'
      case 'down':
        return '↘️'
      default:
        return ''
    }
  }

  return (
    <Card className={`${getVariantStyles()}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {trend !== 'neutral' && (
          <Badge variant="outline" className="text-xs">
            {getTrendIcon()}
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">
            {description}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
