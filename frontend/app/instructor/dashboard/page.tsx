'use client';

import { useCallback, useEffect, useState } from 'react';
import { MetricCard } from '@/components/MetricCard';
import { ReliabilityChart } from '@/components/ReliabilityChart';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { analyticsApi } from '@/lib/api';
import { InstructorSummary, ProblematicItem } from '@/lib/types';
import { useTranslation } from '@/lib/useTranslation';

export default function InstructorDashboardPage() {
  const [summary, setSummary] = useState<InstructorSummary | null>(null);
  const [problematicItems, setProblematicItems] = useState<ProblematicItem[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { t, language } = useTranslation();

  const loadDashboardData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const summaryData = await analyticsApi.getInstructorSummary(10, 0.7, 5, language);
      setSummary(summaryData);
      setProblematicItems(summaryData.problematic_items);
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

  const calibrationHealthLabel = (() => {
    if (!summary) return 'N/A';
    if (language === 'ru') {
      if (summary.class_self_awareness === 'High') return 'Высокое';
      if (summary.class_self_awareness === 'Medium') return 'Среднее';
      if (summary.class_self_awareness === 'Low') return 'Низкое';
    }
    return summary.class_self_awareness;
  })();

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

        {summary && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <span>{t('instructor.modelInfo.title')}</span>
                {summary.overview.model_version && (
                  <Badge variant="outline">v{summary.overview.model_version}</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="font-medium">{t('instructor.modelInfo.totalInteractions')}</span>
                  <p className="text-muted-foreground">{summary.overview.total_interactions}</p>
                </div>
                <div>
                  <span className="font-medium">{t('instructor.modelInfo.withConfidence')}</span>
                  <p className="text-muted-foreground">
                    {summary.overview.interactions_with_confidence}
                  </p>
                </div>
                <div>
                  <span className="font-medium">{t('instructor.modelInfo.confidenceRate')}</span>
                  <p className="text-muted-foreground">
                    {summary.overview.total_interactions > 0
                      ? `${((summary.overview.interactions_with_confidence / summary.overview.total_interactions) * 100).toFixed(1)}%`
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

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <MetricCard
            title={t('instructor.insights.classSelfAwareness')}
            value={calibrationHealthLabel}
            description={t('instructor.insights.classSelfAwarenessHint')}
            variant={
              summary?.class_self_awareness === 'High'
                ? 'success'
                : summary?.class_self_awareness === 'Low'
                  ? 'danger'
                  : 'warning'
            }
          />
          <MetricCard
            title={t('instructor.insights.dangerZones')}
            value={summary?.danger_zones.slice(0, 2).join(', ') || 'N/A'}
            description={t('instructor.insights.dangerZonesHint')}
            variant="warning"
          />
          <MetricCard
            title={t('instructor.insights.coachability')}
            value={summary ? `${(summary.overview.coachability_rate * 100).toFixed(0)}%` : '0%'}
            description={t('instructor.insights.coachabilityHint')}
            variant={
              (summary?.overview.coachability_rate ?? 0) >= 0.6
                ? 'success'
                : (summary?.overview.coachability_rate ?? 0) <= 0.3
                  ? 'warning'
                  : 'default'
            }
          />
          <MetricCard
            title={t('instructor.insights.hiddenStars')}
            value={summary ? String(summary.hidden_stars.length) : 'N/A'}
            description={t('instructor.insights.hiddenStarsHint')}
            variant="success"
          />
        </div>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>{t('instructor.advanced.title')}</CardTitle>
            <Button variant="outline" onClick={() => setShowAdvanced((prev) => !prev)}>
              {showAdvanced ? t('instructor.advanced.hide') : t('instructor.advanced.show')}
            </Button>
          </CardHeader>
          {showAdvanced && summary && (
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard
                  title={t('instructor.metrics.ece')}
                  value={summary.overview.ece.toFixed(3)}
                  description={t('instructor.metrics.lowerIsBetter')}
                  variant="warning"
                />
                <MetricCard
                  title={t('instructor.metrics.brier')}
                  value={summary.overview.brier.toFixed(3)}
                  description={t('instructor.metrics.lowerIsBetter')}
                  variant="warning"
                />
                <MetricCard
                  title={t('instructor.metrics.rocAuc')}
                  value={summary.overview.roc_auc.toFixed(3)}
                  description={t('instructor.metrics.higherIsBetter')}
                  variant="success"
                />
              </div>
              {summary.reliability.bins.length > 0 && (
                <ReliabilityChart
                  data={summary.reliability.bins}
                  modelVersion={summary.reliability.model_version}
                />
              )}
            </CardContent>
          )}
        </Card>

        {summary?.hidden_stars?.length ? (
          <Card>
            <CardHeader>
              <CardTitle>{t('instructor.insights.hiddenStars')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {summary.hidden_stars.map((student) => (
                <div
                  key={student.user_id}
                  className="flex flex-col sm:flex-row sm:items-center sm:justify-between rounded-md border p-3"
                >
                  <span className="font-medium">{student.student_name}</span>
                  <span className="text-sm text-muted-foreground">
                    {language === 'ru' ? 'Точность' : 'Accuracy'}: {(student.accuracy * 100).toFixed(0)}% |{' '}
                    {language === 'ru' ? 'Уверенность' : 'Confidence'}:{' '}
                    {(student.avg_confidence * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>
        ) : null}

        {/* Problematic Questions with pedagogical hints */}
        {problematicItems.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>{t('instructor.problematicItems')}</CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 pr-4">{t('instructor.tableHeaders.question')}</th>
                    <th className="py-2 pr-4">{t('instructor.tableHeaders.tags')}</th>
                    <th className="py-2 pr-4">{t('instructor.tableHeaders.confidentErrorRate')}</th>
                    <th className="py-2 pr-4">{t('instructor.tableHeaders.interactions')}</th>
                    <th className="py-2">{t('instructor.tableHeaders.whyProblematic')}</th>
                    <th className="py-2">{t('instructor.tableHeaders.recommendationForTeacher')}</th>
                  </tr>
                </thead>
                <tbody>
                  {problematicItems.slice(0, 10).map((item) => (
                    <tr key={item.item_id} className="border-b align-top">
                      <td className="py-3 pr-4">{item.stem}</td>
                      <td className="py-3 pr-4">{item.tags.join(', ')}</td>
                      <td className="py-3 pr-4">{(item.confident_error_rate * 100).toFixed(0)}%</td>
                      <td className="py-3 pr-4">{item.total_interactions}</td>
                      <td className="py-3 pr-4">{item.pedagogical_note || '-'}</td>
                      <td className="py-3">{item.recommendation_for_teacher || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}

        {/* No Data State */}
        {(!summary || summary.overview.total_interactions === 0) && (
          <Card>
            <CardContent className="p-8 text-center">
              <p className="text-muted-foreground mb-4">{t('instructor.noData.message')}</p>
              <Button asChild>
                <a href="/student/login">{t('instructor.noData.startTest')}</a>
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
