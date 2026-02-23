'use client';

import { useEffect, useRef, useState } from 'react';
import { useTranslation } from '@/lib/useTranslation';
import { ConfidenceSlider } from './ConfidenceSlider';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

interface QuestionCardProps {
  question: {
    id: number;
    stem: string;
    options: string[];
    correct_option: number;
    tags: string[];
    difficulty_hint?: number;
  };
  onAnswer: (
    chosenOption: number,
    confidence?: number,
    responseTime?: number,
    answerChangesCount?: number,
    timeToFirstChoiceMs?: number,
    timeAfterChoiceMs?: number
  ) => void;
  requireConfidence?: boolean;
  skipConfidencePrompt?: boolean;
  isLoading?: boolean;
}

export function QuestionCard({
  question,
  onAnswer,
  requireConfidence = false,
  skipConfidencePrompt = false,
  isLoading = false,
}: QuestionCardProps) {
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [confidence, setConfidence] = useState<number>(0.6);
  const [startTime] = useState(Date.now());
  const [firstChoiceTime, setFirstChoiceTime] = useState<number | null>(null);
  const [answerChangesCount, setAnswerChangesCount] = useState(0);
  const [isAnswerConfirmed, setIsAnswerConfirmed] = useState(false);
  const { t } = useTranslation();

  const confidenceRef = useRef<HTMLDivElement | null>(null);

  const handleOptionChange = (option: number) => {
    if (firstChoiceTime === null) {
      setFirstChoiceTime(Date.now());
    } else if (selectedOption !== null && selectedOption !== option) {
      setAnswerChangesCount((prev) => prev + 1);
    }
    setSelectedOption(option);
  };

  const handleSubmit = () => {
    if (selectedOption === null) return;

    const isConfidenceRequired = requireConfidence && !skipConfidencePrompt;

    if (isConfidenceRequired) {
      setIsAnswerConfirmed(true);
      if (confidenceRef.current) {
        const y = confidenceRef.current.getBoundingClientRect().top + window.scrollY;
        window.scrollTo({ top: y, behavior: 'smooth' });
      }
    } else {
      const totalTime = Date.now() - startTime;
      const timeToFirst = firstChoiceTime ? firstChoiceTime - startTime : null;
      const timeAfter = firstChoiceTime ? Date.now() - firstChoiceTime : null;

      onAnswer(
        selectedOption,
        undefined,
        totalTime,
        answerChangesCount,
        timeToFirst || undefined,
        timeAfter || undefined
      );
    }
  };

  const handleContinue = () => {
    if (selectedOption === null) return;
    const isConfidenceRequired = requireConfidence && !skipConfidencePrompt;
    const confidenceValue = isConfidenceRequired ? confidence : undefined;

    if (isConfidenceRequired && confidenceValue === undefined) return;

    const totalTime = Date.now() - startTime;
    const timeToFirst = firstChoiceTime ? firstChoiceTime - startTime : null;
    const timeAfter = firstChoiceTime ? Date.now() - firstChoiceTime : null;

    onAnswer(
      selectedOption,
      confidenceValue,
      totalTime,
      answerChangesCount,
      timeToFirst || undefined,
      timeAfter || undefined
    );
  };

  const isConfidenceRequired = requireConfidence && !skipConfidencePrompt;
  const canSubmit = selectedOption !== null && !isAnswerConfirmed;
  const canContinue = isConfidenceRequired && isAnswerConfirmed && confidence !== undefined;

  useEffect(() => {
    if (isAnswerConfirmed && isConfidenceRequired && confidenceRef.current) {
      const y = confidenceRef.current.getBoundingClientRect().top + window.scrollY;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  }, [isAnswerConfirmed, isConfidenceRequired]);

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl">
            {t('studentTest.questionTitle').replace('{id}', question.id.toString())}
          </CardTitle>
          <div className="flex gap-2">
            {question.tags.map((tag) => (
              <Badge key={tag} variant="secondary">
                {tag}
              </Badge>
            ))}
            {question.difficulty_hint && (
              <Badge variant="outline">
                {t('adminQuestions.table.difficulty')}: {question.difficulty_hint}/10
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="relative">
          <div
            aria-disabled={isAnswerConfirmed}
            className={`space-y-4 transition-opacity ${isAnswerConfirmed ? 'opacity-70' : ''}`}
          >
            <div className="text-lg leading-relaxed">{question.stem}</div>

            <div className="space-y-3">
              {question.options.map((option, index) => (
                <label
                  key={`option-${index}-${option.slice(0, 20)}`}
                  className={`flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedOption === index
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-muted/50'
                  }`}
                >
                  <input
                    disabled={isAnswerConfirmed}
                    type="radio"
                    name="option"
                    value={index}
                    checked={selectedOption === index}
                    onChange={() => handleOptionChange(index)}
                    className="w-4 h-4 text-primary"
                  />
                  <span className="flex-1">
                    <span className="font-medium">{String.fromCharCode(65 + index)}.</span> {option}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {isAnswerConfirmed && (
            <div
              className="
                absolute inset-0 rounded-lg
                bg-white/60
                cursor-not-allowed
                pointer-events-auto
              "
            />
          )}
        </div>

        <Button
          onClick={handleSubmit}
          disabled={!canSubmit || isLoading}
          className="w-full"
          size="lg"
        >
          {isLoading
            ? t('common.loading')
            : isConfidenceRequired
              ? t('studentTest.confirmAnswer')
              : t('studentTest.submitAnswer')}
        </Button>

        {!isConfidenceRequired && isAnswerConfirmed && (
          <div className="rounded-lg border bg-muted/30 p-4 text-sm text-muted-foreground">
            {t('studentTest.confidence.skippedForThisQuestion')}
          </div>
        )}

        {isConfidenceRequired && isAnswerConfirmed && (
          <div ref={confidenceRef}>
            <ConfidenceSlider onConfidenceChange={setConfidence} disabled={false} />
          </div>
        )}

        {isConfidenceRequired && isAnswerConfirmed && (
          <Button
            onClick={handleContinue}
            disabled={!canContinue || isLoading}
            className="w-full"
            size="lg"
          >
            {isLoading ? t('common.loading') : t('studentTest.submitAnswer')}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
