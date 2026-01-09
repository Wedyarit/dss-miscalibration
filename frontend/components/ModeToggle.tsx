'use client';

import { useTranslation } from '@/lib/useTranslation';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';

interface ModeToggleProps {
  mode: 'standard' | 'self_confidence';
  onModeChange: (mode: 'standard' | 'self_confidence') => void;
}

export function ModeToggle({ mode, onModeChange }: ModeToggleProps) {
  const { t } = useTranslation();

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardContent className="p-4">
        <div className="space-y-3">
          <h3 className="text-sm font-medium">{t('studentTest.modeSelection.title')}</h3>
          <div className="flex space-x-2">
            <Button
              variant={mode === 'standard' ? 'default' : 'outline'}
              size="sm"
              onClick={() => onModeChange('standard')}
              className="flex-1"
            >
              {t('studentTest.modeSelection.standard')}
            </Button>
            <Button
              variant={mode === 'self_confidence' ? 'default' : 'outline'}
              size="sm"
              onClick={() => onModeChange('self_confidence')}
              className="flex-1"
            >
              {t('studentTest.modeSelection.selfConfidence')}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            {mode === 'standard'
              ? t('studentTest.modeSelection.standardDescription')
              : t('studentTest.modeSelection.selfConfidenceDescription')}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
