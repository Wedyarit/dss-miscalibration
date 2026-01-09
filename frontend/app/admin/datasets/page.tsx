'use client';

import { useCallback, useEffect, useState } from 'react';
import { MetricCard } from '@/components/MetricCard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { adminApi, analyticsApi } from '@/lib/api';
import { AnalyticsOverview, TrainRequest, TrainResponse } from '@/lib/types';
import { useTranslation } from '@/lib/useTranslation';

export default function AdminDatasetsPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [isSeeding, setIsSeeding] = useState(false);
  const [isTraining, setIsTraining] = useState(false);
  const [seedResult, setSeedResult] = useState<{
    users_created?: number;
    questions_created?: number;
    questions_seeded?: number;
    sessions_created?: number;
    interactions_created?: number;
    purpose_fixed?: {
      calibration_sessions?: number;
      real_sessions?: number;
    };
    error?: string;
  } | null>(null);
  const [trainResult, setTrainResult] = useState<TrainResponse | null>(null);
  const [trainConfig, setTrainConfig] = useState<TrainRequest>({
    confidence_threshold: 0.7,
    calibration: 'platt',
    bins: 10,
    test_size: 0.2,
  });
  const { t } = useTranslation();

  const loadOverview = useCallback(async () => {
    try {
      const data = await analyticsApi.getOverview();
      setOverview(data);
    } catch (error) {
      console.error('Failed to load overview:', error);
    }
  }, []);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  const handleSeedDatabase = async () => {
    try {
      setIsSeeding(true);
      setSeedResult(null);
      const result = await adminApi.seedDatabase();
      setSeedResult(result);

      await new Promise((resolve) => setTimeout(resolve, 500));
      await loadOverview();
    } catch (error) {
      console.error('Failed to seed database:', error);
      setSeedResult({
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      });
    } finally {
      setIsSeeding(false);
    }
  };

  const handleTrainModel = async () => {
    try {
      setIsTraining(true);
      const result = await adminApi.trainModel(trainConfig);
      setTrainResult(result);
      await loadOverview();
    } catch (error) {
      console.error('Failed to train model:', error);
    } finally {
      setIsTraining(false);
    }
  };

  const handleExportData = async () => {
    try {
      const blob = await analyticsApi.exportInteractions();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'interactions.csv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to export data:', error);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold">{t('adminDatasets.title')}</h1>
          <p className="text-muted-foreground">{t('adminDatasets.subtitle')}</p>
        </div>

        {/* Current Status */}
        {overview && (
          <Card>
            <CardHeader>
              <CardTitle>{t('adminDatasets.currentStatus')}</CardTitle>
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
                  variant={
                    overview.confident_error_rate < 0.2
                      ? 'success'
                      : overview.confident_error_rate > 0.4
                        ? 'danger'
                        : 'warning'
                  }
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Database Seeding */}
        <Card>
          <CardHeader>
            <CardTitle>{t('adminDatasets.seedDatabase')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">{t('adminDatasets.descriptions.seed')}</p>

            <Button onClick={handleSeedDatabase} disabled={isSeeding} className="w-full md:w-auto">
              {isSeeding ? (
                <span className="flex items-center gap-2">
                  <span className="animate-spin">⏳</span>
                  {t('adminDatasets.status.seeding')}
                </span>
              ) : (
                t('adminDatasets.actions.seed')
              )}
            </Button>

            {seedResult && (
              <div
                className={`p-4 border rounded-lg ${
                  seedResult.error ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
                }`}
              >
                <h4
                  className={`font-medium mb-2 ${
                    seedResult.error ? 'text-red-800' : 'text-green-800'
                  }`}
                >
                  {seedResult.error
                    ? t('adminDatasets.seedResult.failed')
                    : t('adminDatasets.seedResult.success')}
                </h4>
                {seedResult.error ? (
                  <p className="text-sm text-red-700">{seedResult.error}</p>
                ) : (
                  <div className="text-sm text-green-700 space-y-1">
                    <p>
                      • {t('adminDatasets.seedResult.usersCreated')}:{' '}
                      {seedResult.users_created || 0}
                    </p>
                    <p>
                      • {t('adminDatasets.seedResult.questionsCreated')}:{' '}
                      {seedResult.questions_created || 0}
                    </p>
                    {seedResult.questions_seeded !== undefined && (
                      <p>
                        • {t('adminDatasets.seedResult.questionsWithRussian')}:{' '}
                        {seedResult.questions_seeded}
                      </p>
                    )}
                    <p>
                      • {t('adminDatasets.seedResult.sessionsCreated')}:{' '}
                      {seedResult.sessions_created || 0}
                    </p>
                    <p>
                      • {t('adminDatasets.seedResult.interactionsCreated')}:{' '}
                      {seedResult.interactions_created || 0}
                    </p>
                    {seedResult.purpose_fixed && (
                      <div className="mt-2 pt-2 border-t border-green-300">
                        <p className="font-medium">{t('adminDatasets.seedResult.purposeFixed')}:</p>
                        <p>
                          • {t('adminDatasets.seedResult.calibrationSessions')}:{' '}
                          {seedResult.purpose_fixed.calibration_sessions || 0}
                        </p>
                        <p>
                          • {t('adminDatasets.seedResult.realSessions')}:{' '}
                          {seedResult.purpose_fixed.real_sessions || 0}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Model Training */}
        <Card>
          <CardHeader>
            <CardTitle>{t('adminDatasets.trainModel')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">{t('adminDatasets.descriptions.train')}</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">
                  {t('adminDatasets.config.confidenceThreshold')}
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="0.9"
                  step="0.1"
                  value={trainConfig.confidence_threshold}
                  onChange={(e) =>
                    setTrainConfig({
                      ...trainConfig,
                      confidence_threshold: parseFloat(e.target.value),
                    })
                  }
                  className="w-full mt-1"
                />
                <p className="text-xs text-muted-foreground">
                  {trainConfig.confidence_threshold}{' '}
                  {t('adminDatasets.config.thresholdDescription')}
                </p>
              </div>

              <div>
                <label className="text-sm font-medium">
                  {t('adminDatasets.config.calibration')}
                </label>
                <select
                  value={trainConfig.calibration}
                  onChange={(e) =>
                    setTrainConfig({
                      ...trainConfig,
                      calibration: e.target.value as 'platt' | 'isotonic' | 'none',
                    })
                  }
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
                  onChange={(e) =>
                    setTrainConfig({
                      ...trainConfig,
                      bins: parseInt(e.target.value, 10),
                    })
                  }
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
                  onChange={(e) =>
                    setTrainConfig({
                      ...trainConfig,
                      test_size: parseFloat(e.target.value),
                    })
                  }
                  className="w-full mt-1"
                />
                <p className="text-xs text-muted-foreground">
                  {Math.round((trainConfig.test_size || 0.2) * 100)}%{' '}
                  {t('adminDatasets.config.testSizeDescription')}
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
              <div
                className={`p-4 border rounded-lg ${
                  trainResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                }`}
              >
                <h4
                  className={`font-medium mb-2 ${
                    trainResult.success ? 'text-green-800' : 'text-red-800'
                  }`}
                >
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
            <CardTitle>{t('adminDatasets.exportData')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {t('adminDatasets.descriptions.export')}
            </p>

            <Button onClick={handleExportData} variant="outline" className="w-full md:w-auto">
              {t('adminDatasets.actions.export')}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
