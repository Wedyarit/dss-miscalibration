'use client';

import { useState } from 'react';
import { ModeToggle } from '@/components/ModeToggle';
import { QuestionCard } from '@/components/QuestionCard';
import { RiskBadge } from '@/components/RiskBadge';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { predictionApi, questionsApi, sessionsApi } from '@/lib/api';
import { AnswerResponse, PredictionResponse, Question, Session } from '@/lib/types';
import { useTranslation } from '@/lib/useTranslation';

export default function StudentTestPage() {
  const [mode, setMode] = useState<'standard' | 'self_confidence'>('standard');
  const [session, setSession] = useState<Session | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [answerFeedback, setAnswerFeedback] = useState<AnswerResponse | null>(null);
  const [questionCount, setQuestionCount] = useState(0);
  const [showModeSelection, setShowModeSelection] = useState(true);
  const [canReturnToQuestion, setCanReturnToQuestion] = useState(false);
  const [hasReturnedToQuestion, setHasReturnedToQuestion] = useState(false);
  const [isTestCompleted, setIsTestCompleted] = useState(false);
  const { t, language } = useTranslation();

  const startTest = async () => {
    try {
      setIsLoading(true);
      const newSession = await sessionsApi.create(1, mode);
      setSession(newSession);
      setShowModeSelection(false);
      await loadNextQuestion();
    } catch (error) {
      console.error('Failed to initialize session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadNextQuestion = async () => {
    try {
      setIsLoading(true);

      const question = await questionsApi.getRandom(session?.id, language);
      setCurrentQuestion(question);

      setPrediction(null);
      setAnswerFeedback(null);
      setHasReturnedToQuestion(false);
    } catch (error: unknown) {
      console.error('Failed to load question:', error);

      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number } };
        if (axiosError.response?.status === 404) {
          setCurrentQuestion(null);
          setAnswerFeedback(null);
          setPrediction(null);
          setIsTestCompleted(true);
        }
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswer = async (
    chosenOption: number,
    confidence?: number,
    responseTime?: number,
    answerChangesCount?: number,
    timeToFirstChoiceMs?: number,
    timeAfterChoiceMs?: number
  ) => {
    if (!currentQuestion || !session) return;

    try {
      setIsLoading(true);

      const answerResponse = await sessionsApi.submitAnswer(
        session.id,
        currentQuestion.id,
        chosenOption,
        confidence,
        responseTime,
        language,
        answerChangesCount,
        timeToFirstChoiceMs,
        timeAfterChoiceMs
      );
      setAnswerFeedback(answerResponse);

      if (mode === 'standard' && !hasReturnedToQuestion) {
        const predictionResponse = await predictionApi.predict(
          1,
          currentQuestion.id,
          chosenOption,
          confidence,
          responseTime
        );
        setPrediction(predictionResponse);
        setCanReturnToQuestion(true);
      } else {
        setPrediction(null);
        setCanReturnToQuestion(false);
      }

      setQuestionCount((prev) => prev + 1);
    } catch (error) {
      console.error('Failed to submit answer:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReturnToQuestion = () => {
    setAnswerFeedback(null);
    setPrediction(null);
    setCanReturnToQuestion(false);
    setHasReturnedToQuestion(true);
  };

  const handleContinue = () => {
    setPrediction(null);
    setCanReturnToQuestion(false);
  };

  const handleNextQuestion = () => {
    void loadNextQuestion();
  };

  const handleFinishSession = async () => {
    if (!session) return;

    try {
      await sessionsApi.finish(session.id);
      setSession(null);
      setCurrentQuestion(null);
      setQuestionCount(0);
      setPrediction(null);
      setAnswerFeedback(null);
      setShowModeSelection(true);
      setHasReturnedToQuestion(false);
      setIsTestCompleted(false);
    } catch (error) {
      console.error('Failed to finish session:', error);
    }
  };

  return (
    <div className="container mx-auto px-6 py-8">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold">{t('studentTest.title')}</h1>
          <p className="text-muted-foreground">{t('studentTest.subtitle')}</p>
        </div>

        {/* Mode Selection Screen */}
        {showModeSelection && (
          <div className="space-y-6">
            <ModeToggle mode={mode} onModeChange={setMode} />

            <Card className="w-full max-w-md mx-auto">
              <CardContent className="p-8 text-center space-y-4">
                <h3 className="text-lg font-semibold">
                  {t('studentTest.modeSelection.readyToStart')}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {mode === 'standard'
                    ? t('studentTest.modeSelection.standardDescription')
                    : t('studentTest.modeSelection.selfConfidenceDescription')}
                </p>
                <Button onClick={startTest} disabled={isLoading} className="w-full">
                  {isLoading
                    ? t('studentTest.modeSelection.starting')
                    : t('studentTest.modeSelection.startTest')}
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Test Screen */}
        {!showModeSelection && (
          <div className="space-y-6">
            {/* Session Info */}
            {session && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>
                      {t('studentTest.session.sessionNumber').replace(
                        '{id}',
                        session.id.toString()
                      )}
                    </span>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline">
                        {session.mode === 'standard'
                          ? t('studentTest.modeSelection.standard')
                          : t('studentTest.modeSelection.selfConfidence')}
                      </Badge>
                      <Badge variant="secondary">
                        {t('studentTest.session.questions').replace(
                          '{count}',
                          questionCount.toString()
                        )}
                      </Badge>
                    </div>
                  </CardTitle>
                </CardHeader>
              </Card>
            )}

            {/* Current Question */}
            {currentQuestion && !answerFeedback && (
              <QuestionCard
                question={currentQuestion}
                onAnswer={handleAnswer}
                mode={mode}
                isLoading={isLoading}
              />
            )}

            {/* Answer Feedback */}
            {answerFeedback && (
              <Card className="w-full max-w-2xl mx-auto">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <span>{t('studentTest.feedback.title')}</span>
                    {/* Показываем бейдж только если нет высокого риска или если пользователь вернулся к вопросу */}
                    {(!prediction || prediction.risk < 0.5 || !canReturnToQuestion) && (
                      <Badge variant={answerFeedback.is_correct ? 'default' : 'destructive'}>
                        {answerFeedback.is_correct
                          ? t('studentTest.feedback.correct')
                          : t('studentTest.feedback.incorrect')}
                      </Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Показываем feedback только если нет высокого риска или если пользователь вернулся к вопросу */}
                  {(!prediction || prediction.risk < 0.5 || !canReturnToQuestion) && (
                    <p className="text-lg">{answerFeedback.feedback}</p>
                  )}

                  {prediction && mode === 'standard' && (
                    <RiskBadge
                      risk={prediction.risk}
                      recommendation={prediction.recommendation}
                      modelVersion={prediction.model_version}
                      onReturnToQuestion={handleReturnToQuestion}
                      onContinue={handleContinue}
                      showReturnButton={canReturnToQuestion}
                    />
                  )}

                  <div className="flex space-x-4">
                    {/* Показываем кнопки только если нет плашки риска или если пользователь вернулся к вопросу */}
                    {(!prediction || prediction.risk < 0.5 || !canReturnToQuestion) && (
                      <>
                        <Button onClick={handleNextQuestion} className="flex-1">
                          {t('studentTest.feedback.nextQuestion')}
                        </Button>
                        <Button onClick={handleFinishSession} variant="outline">
                          {t('studentTest.feedback.finishTest')}
                        </Button>
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Loading State */}
            {isLoading && (
              <Card className="w-full max-w-2xl mx-auto">
                <CardContent className="p-8 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                  <p>{t('common.loading')}</p>
                </CardContent>
              </Card>
            )}

            {/* Test Completed */}
            {isTestCompleted && (
              <Card className="w-full max-w-2xl mx-auto">
                <CardHeader>
                  <CardTitle className="text-2xl text-center text-green-600">
                    {t('studentTest.testCompleted.title')}
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-center space-y-4">
                  <p className="text-lg text-muted-foreground">
                    {t('studentTest.testCompleted.message')}
                  </p>
                  <Button onClick={handleFinishSession} className="w-full">
                    {t('studentTest.testCompleted.finishButton')}
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
