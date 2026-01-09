'use client';

import { useCallback, useEffect, useState } from 'react';
import { DataTable } from '@/components/DataTable';
import { MetricCard } from '@/components/MetricCard';
import { ReliabilityChart } from '@/components/ReliabilityChart';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { analyticsApi } from '@/lib/api';
import { AnalyticsOverview, ProblematicItem, ReliabilityResponse } from '@/lib/types';
import { useTranslation } from '@/lib/useTranslation';

export default function InstructorDashboardPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [reliabilityData, setReliabilityData] = useState<ReliabilityResponse | null>(null);
  const [problematicItems, setProblematicItems] = useState<ProblematicItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { t, tObject, language } = useTranslation();

  const loadDashboardData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [overviewData, reliabilityData, problematicData] = await Promise.all([
        analyticsApi.getOverview(),
        analyticsApi.getReliability(),
        analyticsApi.getProblematicItems(0.7, 5, language),
      ]);

      setOverview(overviewData);
      setReliabilityData(reliabilityData);
      setProblematicItems(problematicData.items);
    } catch (err: unknown) {
      console.error('Dashboard error:', err);
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { status?: number } };
        if (axiosError.response?.status === 404) {
          setError(t('instructor.error.noData'));
        } else {
          setError(t('instructor.error.loadFailed'));
        }
      } else if (err && typeof err === 'object' && ('code' in err || 'message' in err)) {
        const networkError = err as { code?: string; message?: string };
        if (
          networkError.code === 'NETWORK_ERROR' ||
          networkError.message?.includes('Network Error')
        ) {
          setError(t('instructor.error.networkError'));
        } else {
          setError(t('instructor.error.loadFailed'));
        }
      } else {
        setError(t('instructor.error.loadFailed'));
      }
    } finally {
      setIsLoading(false);
    }
  }, [t, language]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const refreshData = () => {
    loadDashboardData();
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p>{t('common.loading')}</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <Card>
            <CardContent className="p-8 text-center">
              <p className="text-destructive mb-4">{error}</p>
              <Button onClick={refreshData}>{t('instructor.actions.retry')}</Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">{t('instructor.title')}</h1>
            <p className="text-muted-foreground">{t('instructor.subtitle')}</p>
          </div>
          <Button onClick={refreshData} variant="outline">
            {t('instructor.refreshData')}
          </Button>
        </div>

        {/* Model Info */}
        {overview?.model_version && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <span>{t('instructor.modelInfo.title')}</span>
                <Badge variant="outline">v{overview.model_version}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="font-medium">{t('instructor.modelInfo.totalInteractions')}</span>
                  <p className="text-muted-foreground">{overview.total_interactions}</p>
                </div>
                <div>
                  <span className="font-medium">{t('instructor.modelInfo.withConfidence')}</span>
                  <p className="text-muted-foreground">{overview.interactions_with_confidence}</p>
                </div>
                <div>
                  <span className="font-medium">{t('instructor.modelInfo.confidenceRate')}</span>
                  <p className="text-muted-foreground">
                    {overview.total_interactions > 0
                      ? `${((overview.interactions_with_confidence / overview.total_interactions) * 100).toFixed(1)}%`
                      : '0%'}
                  </p>
                </div>
                <div>
                  <span className="font-medium">{t('instructor.modelInfo.lastUpdated')}</span>
                  <p className="text-muted-foreground">Just now</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Metrics Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title={t('instructor.metrics.ece')}
            value={overview ? overview.ece.toFixed(3) : 'N/A'}
            description={t('instructor.metrics.lowerIsBetter')}
            variant={
              overview && overview.ece < 0.1
                ? 'success'
                : overview && overview.ece > 0.2
                  ? 'danger'
                  : 'warning'
            }
          />
          <MetricCard
            title={t('instructor.metrics.brier')}
            value={overview ? overview.brier.toFixed(3) : 'N/A'}
            description={t('instructor.metrics.lowerIsBetter')}
            variant={
              overview && overview.brier < 0.2
                ? 'success'
                : overview && overview.brier > 0.4
                  ? 'danger'
                  : 'warning'
            }
          />
          <MetricCard
            title={t('instructor.metrics.rocAuc')}
            value={overview ? overview.roc_auc.toFixed(3) : 'N/A'}
            description={t('instructor.metrics.higherIsBetter')}
            variant={
              overview && overview.roc_auc > 0.8
                ? 'success'
                : overview && overview.roc_auc < 0.6
                  ? 'danger'
                  : 'warning'
            }
          />
          <MetricCard
            title={t('instructor.metrics.confidentErrorRate')}
            value={overview ? `${(overview.confident_error_rate * 100).toFixed(1)}%` : 'N/A'}
            description="Rate of confident errors"
            variant={
              overview && overview.confident_error_rate < 0.2
                ? 'success'
                : overview && overview.confident_error_rate > 0.4
                  ? 'danger'
                  : 'warning'
            }
          />
        </div>

        {/* Reliability Chart */}
        {reliabilityData && reliabilityData.bins.length > 0 && (
          <ReliabilityChart
            data={reliabilityData.bins}
            modelVersion={reliabilityData.model_version}
          />
        )}

        {/* Problematic Questions */}
        {problematicItems.length > 0 && (
          <DataTable
            data={problematicItems}
            title={t('instructor.problematicItems')}
            headers={tObject<{
              question: string;
              tags: string;
              confidentErrorRate: string;
              interactions: string;
              avgConfidence: string;
              avgAccuracy: string;
            }>('instructor.tableHeaders')}
          />
        )}

        {/* No Data State */}
        {(!overview || overview.total_interactions === 0) && (
          <Card>
            <CardContent className="p-8 text-center">
              <p className="text-muted-foreground mb-4">{t('instructor.noData.message')}</p>
              <Button asChild>
                <a href="/student/test">{t('instructor.noData.startTest')}</a>
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
