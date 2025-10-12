"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { MetricCard } from '@/components/MetricCard'
import { AnimatedText } from '@/components/AnimatedText'
import { adminApi, analyticsApi } from '@/lib/api'
import { AnalyticsOverview, TrainRequest, TrainResponse } from '@/lib/types'
import { useTranslation } from '@/lib/useTranslation'

export default function AdminDatasetsPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null)
  const [isSeeding, setIsSeeding] = useState(false)
  const [isTraining, setIsTraining] = useState(false)
  const [seedResult, setSeedResult] = useState<any>(null)
  const [trainResult, setTrainResult] = useState<TrainResponse | null>(null)
  const [trainConfig, setTrainConfig] = useState<TrainRequest>({
    confidence_threshold: 0.7,
    calibration: 'platt',
    bins: 10,
    test_size: 0.2
  })
  const { t } = useTranslation()

  useEffect(() => {
    loadOverview()
  }, [])

  const loadOverview = async () => {
    try {
      const data = await analyticsApi.getOverview()
      setOverview(data)
    } catch (error) {
      console.error('Failed to load overview:', error)
    }
  }

  const handleSeedDatabase = async () => {
    try {
      setIsSeeding(true)
      const result = await adminApi.seedDatabase()
      setSeedResult(result)
      await loadOverview() // Refresh data
    } catch (error) {
      console.error('Failed to seed database:', error)
    } finally {
      setIsSeeding(false)
    }
  }

  const handleTrainModel = async () => {
    try {
      setIsTraining(true)
      const result = await adminApi.trainModel(trainConfig)
      setTrainResult(result)
      await loadOverview() // Refresh data
    } catch (error) {
      console.error('Failed to train model:', error)
    } finally {
      setIsTraining(false)
    }
  }

  const handleExportData = async () => {
    try {
      const blob = await analyticsApi.exportInteractions()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'interactions.csv'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to export data:', error)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold">
            {t("adminDatasets.title")}
          </h1>
          <p className="text-muted-foreground">
            {t('adminDatasets.subtitle')}
          </p>
        </div>

        {/* Current Status */}
        {overview && (
          <Card>
            <CardHeader>
              <CardTitle>
                {t("adminDatasets.currentStatus")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <MetricCard
                  title={t('adminDatasets.labels.totalInteractions')}
                  value={overview.total_interactions}
                  description={t('adminDatasets.labels.allInteractions')}
                />
                <MetricCard
                  title={t('adminDatasets.labels.withConfidence')}
                  value={overview.interactions_with_confidence}
                  description={t('adminDatasets.labels.confidenceInteractions')}
                />
                <MetricCard
                  title={t('adminDatasets.labels.modelVersion')}
                  value={overview.model_version || 'None'}
                  description={t('adminDatasets.labels.latestModel')}
                />
                <MetricCard
                  title={t('adminDatasets.labels.confidentErrorRate')}
                  value={`${(overview.confident_error_rate * 100).toFixed(1)}%`}
                  description={t('adminDatasets.labels.errorRate')}
                  variant={overview.confident_error_rate < 0.2 ? 'success' : overview.confident_error_rate > 0.4 ? 'danger' : 'warning'}
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Database Seeding */}
        <Card>
          <CardHeader>
            <CardTitle>
              {t("adminDatasets.seedDatabase")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {t('adminDatasets.descriptions.seed')}
            </p>

            <Button
              onClick={handleSeedDatabase}
              disabled={isSeeding}
              className="w-full md:w-auto"
            >
              {isSeeding ? t('adminDatasets.status.seeding') : t('adminDatasets.actions.seed')}
            </Button>

            {seedResult && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <h4 className="font-medium text-green-800 mb-2">Seeding Complete!</h4>
                <div className="text-sm text-green-700 space-y-1">
                  <p>• Users created: {seedResult.users_created}</p>
                  <p>• Questions created: {seedResult.questions_created}</p>
                  <p>• Sessions created: {seedResult.sessions_created}</p>
                  <p>• Interactions created: {seedResult.interactions_created}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Model Training */}
        <Card>
          <CardHeader>
            <CardTitle>
              {t("adminDatasets.trainModel")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {t('adminDatasets.descriptions.train')}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">{t('adminDatasets.config.confidenceThreshold')}</label>
                <input
                  type="range"
                  min="0.5"
                  max="0.9"
                  step="0.1"
                  value={trainConfig.confidence_threshold}
                  onChange={(e) => setTrainConfig({
                    ...trainConfig,
                    confidence_threshold: parseFloat(e.target.value)
                  })}
                  className="w-full mt-1"
                />
                <p className="text-xs text-muted-foreground">
                  {trainConfig.confidence_threshold} {t('adminDatasets.config.thresholdDescription')}
                </p>
              </div>

              <div>
                <label className="text-sm font-medium">{t('adminDatasets.config.calibration')}</label>
                <select
                  value={trainConfig.calibration}
                  onChange={(e) => setTrainConfig({
                    ...trainConfig,
                    calibration: e.target.value as 'platt' | 'isotonic' | 'none'
                  })}
                  className="w-full mt-1 p-2 border rounded-md"
                >
                  <option value="platt">Platt Scaling</option>
                  <option value="isotonic">Isotonic Regression</option>
                  <option value="none">No Calibration</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium">{t('adminDatasets.config.bins')}</label>
                <input
                  type="number"
                  min="5"
                  max="20"
                  value={trainConfig.bins}
                  onChange={(e) => setTrainConfig({
                    ...trainConfig,
                    bins: parseInt(e.target.value)
                  })}
                  className="w-full mt-1 p-2 border rounded-md"
                />
              </div>

              <div>
                <label className="text-sm font-medium">{t('adminDatasets.config.testSize')}</label>
                <input
                  type="range"
                  min="0.1"
                  max="0.5"
                  step="0.1"
                  value={trainConfig.test_size}
                  onChange={(e) => setTrainConfig({
                    ...trainConfig,
                    test_size: parseFloat(e.target.value)
                  })}
                  className="w-full mt-1"
                />
                <p className="text-xs text-muted-foreground">
                  {Math.round(trainConfig.test_size * 100)}% {t('adminDatasets.config.testSizeDescription')}
                </p>
              </div>
            </div>

            <Button
              onClick={handleTrainModel}
              disabled={isTraining || !overview || overview.total_interactions < 50}
              className="w-full md:w-auto"
            >
              {isTraining ? t('adminDatasets.status.training') : t('adminDatasets.actions.train')}
            </Button>

            {trainResult && (
              <div className={`p-4 border rounded-lg ${
                trainResult.success 
                  ? 'bg-green-50 border-green-200' 
                  : 'bg-red-50 border-red-200'
              }`}>
                <h4 className={`font-medium mb-2 ${
                  trainResult.success ? 'text-green-800' : 'text-red-800'
                }`}>
                  {trainResult.success ? 'Training Complete!' : 'Training Failed'}
                </h4>

                {trainResult.success ? (
                  <div className="text-sm space-y-1">
                    <p>• Model Version: {trainResult.model_version}</p>
                    <p>• Training Samples: {trainResult.n_samples}</p>
                    <p>• Features Used: {trainResult.n_features}</p>
                    {trainResult.metrics && (
                      <div className="mt-2">
                        <p>• ECE: {trainResult.metrics.ece?.toFixed(3)}</p>
                        <p>• Brier Score: {trainResult.metrics.brier?.toFixed(3)}</p>
                        <p>• ROC AUC: {trainResult.metrics.roc_auc?.toFixed(3)}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-red-700">{trainResult.error}</p>
                )}
              </div>
            )}

            {overview && overview.total_interactions < 50 && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  ⚠️ {t('adminDatasets.warnings.needMoreData')}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Data Export */}
        <Card>
          <CardHeader>
            <CardTitle>
              {t("adminDatasets.exportData")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {t('adminDatasets.descriptions.export')}
            </p>

            <Button
              onClick={handleExportData}
              variant="outline"
              className="w-full md:w-auto"
            >
              {t('adminDatasets.actions.export')}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
