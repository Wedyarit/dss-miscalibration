'use client';

import { useTranslation } from '@/lib/useTranslation';
import { ClientOnly } from './ClientOnly';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';

interface RiskBadgeProps {
  risk: number;
  recommendation: string;
  modelVersion?: string;
  onReturnToQuestion?: () => void;
  onContinue?: () => void;
  showReturnButton?: boolean;
}

export function RiskBadge({
  risk,
  recommendation: _recommendation,
  modelVersion,
  onReturnToQuestion,
  onContinue,
  showReturnButton = false,
}: RiskBadgeProps) {
  const isHighRisk = risk >= 0.5;
  const { t } = useTranslation();

  return (
    <Card
      className={`w-full max-w-lg mx-auto ${isHighRisk ? 'border-destructive bg-red-50' : 'border-green-500 bg-green-50'}`}
    >
      <CardContent className="p-6">
        {/* Header with icon and risk level */}
        <div className="flex items-center space-x-3 mb-4">
          <div className={`p-2 rounded-full ${isHighRisk ? 'bg-red-100' : 'bg-green-100'}`}>
            {isHighRisk ? (
              <span className="text-red-600 text-xl">⚠️</span>
            ) : (
              <span className="text-green-600 text-xl">✅</span>
            )}
          </div>
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <Badge
                variant={isHighRisk ? 'destructive' : 'secondary'}
                className="text-sm font-semibold"
              >
                {t('studentTest.risk.risk')}
              </Badge>
            </div>
          </div>
        </div>

        {/* Message */}
        <div className="mb-4">
          <p className={`text-base font-medium ${isHighRisk ? 'text-red-800' : 'text-green-800'}`}>
            <ClientOnly
              fallback={
                isHighRisk
                  ? 'High probability of confident error - please review your answer'
                  : 'Low risk - you can proceed with confidence'
              }
            >
              {isHighRisk ? t('studentTest.risk.highRisk') : t('studentTest.risk.lowRisk')}
            </ClientOnly>
          </p>

          {modelVersion && (
            <p className="text-xs text-muted-foreground mt-2">
              {t('studentTest.risk.model')}: {modelVersion}
            </p>
          )}
        </div>

        {/* Action buttons */}
        {showReturnButton && isHighRisk && onReturnToQuestion && (
          <div className="pt-4 border-t border-gray-200">
            <div className="flex space-x-3">
              <Button
                onClick={onReturnToQuestion}
                variant="outline"
                size="sm"
                className="flex-1 border-red-300 text-red-700 hover:bg-red-50"
              >
                {t('studentTest.risk.returnToQuestion')}
              </Button>
              {onContinue && (
                <Button
                  onClick={onContinue}
                  variant="default"
                  size="sm"
                  className="flex-1 bg-red-600 hover:bg-red-700"
                >
                  {t('studentTest.risk.continue')}
                </Button>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
