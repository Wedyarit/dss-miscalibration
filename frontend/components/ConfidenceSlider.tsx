'use client';

import { useState } from 'react';
import { useTranslation } from '@/lib/useTranslation';
import { ClientOnly } from './ClientOnly';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

interface ConfidenceSliderProps {
  onConfidenceChange: (confidence: number) => void;
  disabled?: boolean;
}

const confidenceLevels = [
  { value: 0.2, label: 'studentTest.confidence.justGuessing', color: 'text-slate-600' },
  { value: 0.4, label: 'studentTest.confidence.notSure', color: 'text-amber-700' },
  { value: 0.6, label: 'studentTest.confidence.fairlyConfident', color: 'text-sky-700' },
  { value: 0.8, label: 'studentTest.confidence.verySure', color: 'text-blue-700' },
  { value: 1.0, label: 'studentTest.confidence.absolutelyCertain', color: 'text-emerald-700' },
];

export function ConfidenceSlider({ onConfidenceChange, disabled = false }: ConfidenceSliderProps) {
  const [confidence, setConfidence] = useState(0.6);
  const { t } = useTranslation();

  const handleConfidenceChange = (value: number) => {
    setConfidence(value);
    onConfidenceChange(value);
  };

  const getCurrentLevel = () => {
    return confidenceLevels.find((level) => confidence <= level.value) || confidenceLevels[4];
  };

  const currentLevel = getCurrentLevel();

  return (
    <div className="relative">
      <Card
        aria-disabled={disabled}
        className={`w-full transition-opacity ${disabled ? 'opacity-70' : ''}`}
      >
        <CardHeader>
          <CardTitle className="text-lg">{t('studentTest.confidence.selectConfidence')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg bg-muted/40 p-3 text-center text-sm">
            <span className={`font-medium ${currentLevel.color}`}>
              <ClientOnly fallback="Fairly Confident">{t(currentLevel.label)}</ClientOnly>
            </span>
          </div>

          <div className="grid grid-cols-1 gap-2 sm:grid-cols-5">
            {confidenceLevels.map((level) => (
              <Button
                key={level.value}
                variant="outline"
                size="sm"
                onClick={() => handleConfidenceChange(level.value)}
                disabled={disabled}
                className={`min-h-10 text-xs ${level.color} ${
                  confidence === level.value
                    ? 'border-primary/40 bg-primary/10 hover:bg-primary/20'
                    : 'hover:bg-muted/60'
                }`}
              >
                <ClientOnly fallback="Confidence">
                  {t(level.label)}
                </ClientOnly>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {disabled && (
        <div
          className="
            absolute inset-0 rounded-xl
            bg-white/60 backdrop-saturate-0
            cursor-not-allowed
            pointer-events-auto
          "
        />
      )}
    </div>
  );
}
