"use client"

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useTranslation } from '@/lib/useTranslation'

interface ReliabilityChartProps {
  data: Array<{
    bin_low: number
    bin_high: number
    conf_avg: number
    acc_avg: number
    count: number
  }>
  modelVersion?: string
}

export function ReliabilityChart({ data, modelVersion }: ReliabilityChartProps) {
  const { t } = useTranslation()
  const chartData = data.map((bin) => ({
    bin: `${(bin.bin_low * 100).toFixed(0)}-${(bin.bin_high * 100).toFixed(0)}%`,
    confidence: bin.conf_avg,
    accuracy: bin.acc_avg,
    count: bin.count,
    perfect: bin.bin_low + (bin.bin_high - bin.bin_low) / 2, // Perfect calibration line
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('instructor.reliabilityChart.title')}</CardTitle>
        <p className="text-sm text-muted-foreground">
          {t('instructor.reliabilityChart.description')}
        </p>
        {modelVersion && (
          <p className="text-xs text-muted-foreground">
            {t('instructor.reliabilityChart.modelVersion')}: {modelVersion}
          </p>
        )}
      </CardHeader>
      <CardContent>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="bin"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis
                domain={[0, 1]}
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
              />
              <Tooltip
                formatter={(value: number, name: string) => [
                  `${(value * 100).toFixed(1)}%`,
                  name === 'confidence' ? t('instructor.reliabilityChart.confidence') :
                  name === 'accuracy' ? t('instructor.reliabilityChart.accuracy') :
                  name === 'perfect' ? t('instructor.reliabilityChart.perfectCalibration') : name
                ]}
                labelFormatter={(label) => `${t('instructor.reliabilityChart.confidenceRange')}: ${label}`}
              />
              <Bar
                dataKey="confidence"
                fill="#3b82f6"
                name={t('instructor.reliabilityChart.confidence')}
                opacity={0.7}
              />
              <Line
                type="monotone"
                dataKey="accuracy"
                stroke="#ef4444"
                strokeWidth={2}
                name={t('instructor.reliabilityChart.accuracy')}
                dot={{ fill: '#ef4444', strokeWidth: 2, r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="perfect"
                stroke="#10b981"
                strokeWidth={2}
                strokeDasharray="5 5"
                name={t('instructor.reliabilityChart.perfectCalibration')}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 text-xs text-muted-foreground">
          <p>• {t('instructor.reliabilityChart.legendBlue')}</p>
          <p>• {t('instructor.reliabilityChart.legendRed')}</p>
          <p>• {t('instructor.reliabilityChart.legendGreen')}</p>
        </div>
      </CardContent>
    </Card>
  )
}
