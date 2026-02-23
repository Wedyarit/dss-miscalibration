'use client';

import { useEffect, useState } from 'react';
import { useTranslation } from '@/lib/useTranslation';
import { ClientOnly } from './ClientOnly';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';

interface RiskBadgeProps {
  risk: number;
  showIntervention: boolean;
  messageRu: string;
  reasonCode?: string;
  reasonText?: string;
  onReturnToQuestion?: () => void;
  onContinue?: () => void;
  showReturnButton?: boolean;
}

export function RiskBadge({
  risk: _risk,
  showIntervention,
  messageRu: _messageRu,
  reasonCode,
  reasonText,
  onReturnToQuestion,
  onContinue,
  showReturnButton = false,
}: RiskBadgeProps) {
  const [cooldown, setCooldown] = useState(showIntervention ? 3 : 0);
  const { t } = useTranslation();
  const reasonLabel = reasonCode ? t(`studentTest.risk.reasons.${reasonCode}`) : null;
  const canContinue = !showIntervention || cooldown <= 0;

  useEffect(() => {
    if (!showIntervention) {
      setCooldown(0);
      return;
    }
    setCooldown(3);
  }, [showIntervention]);

  useEffect(() => {
    if (!showIntervention || cooldown <= 0) {
      return;
    }
    const timer = window.setTimeout(() => setCooldown((prev) => prev - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [cooldown, showIntervention]);

  return (
    <Card className="w-full max-w-lg mx-auto border-border bg-card shadow-sm">
      <CardContent className="p-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="rounded-full bg-muted p-2">
            <span className="text-lg text-muted-foreground">💡</span>
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold">
              {showIntervention
                ? t('studentTest.risk.secondOpinion')
                : t('studentTest.risk.analyticPause')}
            </p>
          </div>
        </div>

        <div className="mb-4">
          <p className="text-base font-medium text-foreground">
            <ClientOnly
              fallback={
                showIntervention
                  ? t('studentTest.risk.highRisk')
                  : t('studentTest.risk.lowRisk')
              }
            >
              {showIntervention ? t('studentTest.risk.highRisk') : t('studentTest.risk.lowRisk')}
            </ClientOnly>
          </p>

          {(reasonLabel || reasonText) && (
            <p className="mt-2 text-sm text-muted-foreground">
              {reasonLabel || reasonText}
            </p>
          )}
        </div>

        {showReturnButton && onReturnToQuestion && (
          <div className="pt-4 border-t border-border">
            <div className="flex space-x-3">
              <Button
                onClick={onReturnToQuestion}
                variant="outline"
                size="sm"
                className="flex-1"
              >
                {t('studentTest.risk.returnToQuestion')}
              </Button>
              {onContinue && (
                <Button
                  onClick={onContinue}
                  variant="default"
                  size="sm"
                  disabled={!canContinue}
                  className="flex-1"
                >
                  {canContinue
                    ? t('studentTest.risk.continue')
                    : t('studentTest.risk.waitCooldown').replace('{seconds}', String(cooldown))}
                </Button>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
