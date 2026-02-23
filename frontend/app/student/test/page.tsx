'use client';

import { useEffect, useMemo, useState } from 'react';
import { QuestionCard } from '@/components/QuestionCard';
import { RiskBadge } from '@/components/RiskBadge';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { predictionApi, sessionsApi } from '@/lib/api';
import { AnswerResponse, AnswerSubmitPayload, PredictionResponse, Question, Session } from '@/lib/types';
import { useTranslation } from '@/lib/useTranslation';

const STUDENT_NAME_KEY = 'dss.student.name';
const STUDENT_ID_KEY = 'dss.student.id';

export default function StudentTestPage() {
  const [studentNameInput, setStudentNameInput] = useState('');
  const [selectedProfile, setSelectedProfile] = useState<'anna' | 'ivan' | 'new' | null>(null);
  const [studentName, setStudentName] = useState<string | null>(null);
  const [studentId, setStudentId] = useState<number | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [requireConfidence, setRequireConfidence] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [answerFeedback, setAnswerFeedback] = useState<AnswerResponse | null>(null);
  const [calibrationSamples, setCalibrationSamples] = useState<Array<{ confidence: number; isCorrect: boolean }>>([]);
  const [questionCount, setQuestionCount] = useState(0);
  const [showModeSelection, setShowModeSelection] = useState(true);
  const [canReturnToQuestion, setCanReturnToQuestion] = useState(false);
  const [hasReturnedToQuestion, setHasReturnedToQuestion] = useState(false);
  const [tempInitialData, setTempInitialData] = useState<AnswerSubmitPayload | null>(null);
  const [interventionShownAt, setInterventionShownAt] = useState<number | null>(null);
  const [isTestCompleted, setIsTestCompleted] = useState(false);
  const { t, language } = useTranslation();

  useEffect(() => {
    const savedName = window.localStorage.getItem(STUDENT_NAME_KEY);
    const savedId = window.localStorage.getItem(STUDENT_ID_KEY);
    if (savedName) {
      setStudentName(savedName);
      setStudentNameInput(savedName);
    }
    if (savedId) {
      const parsed = Number(savedId);
      if (Number.isFinite(parsed) && parsed > 0) {
        setStudentId(parsed);
      }
    }
  }, []);

  const calibrationProfile = useMemo(() => {
    if (calibrationSamples.length < 3) {
      return {
        title: language === 'ru' ? 'Недостаточно данных о калибровке' : 'Not enough calibration data yet',
        description:
          language === 'ru'
            ? 'Ответьте еще на несколько вопросов, чтобы увидеть персональный профиль.'
            : 'Answer a few more questions to unlock your personal calibration profile.',
      };
    }

    const avgConfidence = calibrationSamples.reduce((sum, x) => sum + x.confidence, 0) / calibrationSamples.length;
    const avgAccuracy =
      calibrationSamples.reduce((sum, x) => sum + (x.isCorrect ? 1 : 0), 0) / calibrationSamples.length;
    const delta = avgConfidence - avgAccuracy;

    if (delta > 0.15) {
      return {
        title: language === 'ru' ? 'Склонность к переоценке' : 'Bold Guesser',
        description:
          language === 'ru'
            ? 'Вы часто уверены сильнее, чем позволяет точность. Перед ответом проверяйте ключевую деталь.'
            : 'You tend to feel more certain than your accuracy suggests. Pause for one detail check.',
      };
    }
    if (delta < -0.15) {
      return {
        title: language === 'ru' ? 'Скрытая сильная сторона' : 'Cautious Expert',
        description:
          language === 'ru'
            ? 'Вы отвечаете точнее, чем оцениваете себя. Повышайте уверенность там, где вы стабильно правы.'
            : 'You perform better than you feel. Trust yourself more on topics where you are consistently right.',
      };
    }
    return {
      title: language === 'ru' ? 'Реалистичный мыслитель' : 'Realistic Thinker',
      description:
        language === 'ru'
          ? 'Ваша уверенность в целом соответствует результатам. Отличный базовый навык саморефлексии.'
          : 'Your confidence generally matches outcomes. Great self-awareness baseline.',
    };
  }, [calibrationSamples, language]);

  const handleResolveStudent = async () => {
    if (!studentNameInput.trim()) {
      return;
    }
    try {
      setIsLoading(true);
      const resolved = await sessionsApi.resolveSimulatedUser(studentNameInput.trim());
      setStudentName(resolved.student_name);
      setStudentId(resolved.user_id);
      window.localStorage.setItem(STUDENT_NAME_KEY, resolved.student_name);
      window.localStorage.setItem(STUDENT_ID_KEY, String(resolved.user_id));
    } catch (error) {
      console.error('Failed to resolve student user:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const startTest = async () => {
    if (!studentId) return;
    try {
      setIsLoading(true);
      const newSession = await sessionsApi.create(studentId);
      setSession(newSession);
      setShowModeSelection(false);
      setCalibrationSamples([]);
      await loadNextQuestion(newSession);
    } catch (error) {
      console.error('Failed to initialize session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadNextQuestion = async (activeSession?: Session) => {
    const targetSession = activeSession || session;
    if (!targetSession) return;
    try {
      setIsLoading(true);
      const nextQuestion = await sessionsApi.getNextQuestion(targetSession.id, language);
      setCurrentQuestion(nextQuestion.question);
      setRequireConfidence(nextQuestion.require_confidence);

      setPrediction(null);
      setAnswerFeedback(null);
      setHasReturnedToQuestion(false);
      setTempInitialData(null);
      setInterventionShownAt(null);
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
    if (!currentQuestion || !session || !studentId) return;

    try {
      setIsLoading(true);
      const payload: AnswerSubmitPayload = {
        item_id: currentQuestion.id,
        chosen_option: chosenOption,
        confidence,
        response_time_ms: responseTime || 0,
        answer_changes_count: answerChangesCount,
        time_to_first_choice_ms: timeToFirstChoiceMs,
        time_after_choice_ms: timeAfterChoiceMs,
      };

      const submitFinalAnswer = async (
        finalPayload: AnswerSubmitPayload,
        initialPayload?: AnswerSubmitPayload,
        reconsidered = false
      ) => {
        const hasInitialPayload = Boolean(initialPayload);
        const finalConfidence =
          finalPayload.confidence !== undefined
            ? finalPayload.confidence
            : initialPayload?.confidence;
        const requestPayload: AnswerSubmitPayload = {
          ...finalPayload,
          confidence: finalConfidence,
          initial_chosen_option: hasInitialPayload
            ? String(initialPayload!.chosen_option)
            : undefined,
          initial_confidence: hasInitialPayload ? initialPayload?.confidence : undefined,
          reconsidered: hasInitialPayload ? reconsidered : false,
          time_to_reconsider_ms:
            hasInitialPayload && interventionShownAt
              ? Math.max(0, Date.now() - interventionShownAt)
              : undefined,
        };

        const answerResponse = await sessionsApi.submitAnswer(session.id, requestPayload, language);
        setAnswerFeedback(answerResponse);

        const calibrationConfidence =
          initialPayload?.confidence !== undefined ? initialPayload.confidence : finalConfidence;
        if (calibrationConfidence !== undefined) {
          const initialChosen = initialPayload?.chosen_option;
          const calibrationIsCorrect =
            initialChosen !== undefined
              ? initialChosen === currentQuestion.correct_option
              : answerResponse.is_correct;
          setCalibrationSamples((prev) => [
            ...prev,
            { confidence: calibrationConfidence, isCorrect: calibrationIsCorrect },
          ]);
        }

        setPrediction(null);
        setCanReturnToQuestion(false);
        setInterventionShownAt(null);
        setTempInitialData(null);
        setHasReturnedToQuestion(false);
        setQuestionCount((prev) => prev + 1);
      };

      if (!hasReturnedToQuestion) {
        setTempInitialData(payload);
        const predictionResponse = await predictionApi.predict(
          studentId,
          currentQuestion.id,
          payload.chosen_option,
          payload.confidence,
          payload.response_time_ms
        );
        if (predictionResponse.intervention.show_intervention) {
          setPrediction(predictionResponse);
          setCanReturnToQuestion(true);
          setInterventionShownAt(Date.now());
          setAnswerFeedback({
            is_correct: false,
            correct_option: currentQuestion.correct_option,
            feedback: '',
            session_id: session.id,
          });
          return;
        }
        await submitFinalAnswer(payload);
      } else {
        const initialPayload = tempInitialData || undefined;
        const changedOption =
          initialPayload !== undefined && initialPayload.chosen_option !== payload.chosen_option;
        const initialConfidence = initialPayload?.confidence;
        const finalConfidence = payload.confidence ?? initialConfidence;
        const changedConfidence =
          initialPayload !== undefined &&
          initialConfidence !== undefined &&
          finalConfidence !== undefined &&
          initialConfidence !== finalConfidence;
        await submitFinalAnswer(
          payload,
          initialPayload,
          Boolean(initialPayload && (changedOption || changedConfidence))
        );
      }
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

  const handleContinue = async () => {
    if (!tempInitialData || !session || !currentQuestion) return;
    try {
      setIsLoading(true);
      const requestPayload: AnswerSubmitPayload = {
        ...tempInitialData,
        initial_chosen_option: String(tempInitialData.chosen_option),
        initial_confidence: tempInitialData.confidence,
        reconsidered: false,
        time_to_reconsider_ms: interventionShownAt
          ? Math.max(0, Date.now() - interventionShownAt)
          : undefined,
      };
      const answerResponse = await sessionsApi.submitAnswer(session.id, requestPayload, language);
      setAnswerFeedback(answerResponse);
      if (tempInitialData.confidence !== undefined) {
        const initialIsCorrect = tempInitialData.chosen_option === currentQuestion.correct_option;
        setCalibrationSamples((prev) => [
          ...prev,
          { confidence: tempInitialData.confidence!, isCorrect: initialIsCorrect },
        ]);
      }
      setPrediction(null);
      setCanReturnToQuestion(false);
      setInterventionShownAt(null);
      setTempInitialData(null);
      setHasReturnedToQuestion(false);
      setQuestionCount((prev) => prev + 1);
    } catch (error) {
      console.error('Failed to confirm answer after intervention:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNextQuestion = () => {
    void loadNextQuestion();
  };

  const resetStudentState = () => {
    setStudentName(null);
    setStudentNameInput('');
    setStudentId(null);
    setSession(null);
    setCurrentQuestion(null);
    setRequireConfidence(false);
    setPrediction(null);
    setAnswerFeedback(null);
    setCalibrationSamples([]);
    setQuestionCount(0);
    setShowModeSelection(true);
    setCanReturnToQuestion(false);
    setHasReturnedToQuestion(false);
    setTempInitialData(null);
    setInterventionShownAt(null);
    setIsTestCompleted(false);
    window.localStorage.removeItem(STUDENT_NAME_KEY);
    window.localStorage.removeItem(STUDENT_ID_KEY);
  };

  const handleSwitchStudent = async () => {
    if (session) {
      const shouldFinishAndLogout = window.confirm(
        t('studentTest.actions.logoutConfirmDescription')
      );
      if (!shouldFinishAndLogout) {
        return;
      }

      try {
        setIsLoading(true);
        await sessionsApi.finish(session.id);
      } catch (error) {
        console.error('Failed to finish session before switching student:', error);
      } finally {
        setIsLoading(false);
      }
    }

    resetStudentState();
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
      setTempInitialData(null);
      setInterventionShownAt(null);
      setIsTestCompleted(false);
      setRequireConfidence(false);
    } catch (error) {
      console.error('Failed to finish session:', error);
    }
  };

  const resolveProfile = async (profileName: string) => {
    setStudentNameInput(profileName);
    try {
      setIsLoading(true);
      const resolved = await sessionsApi.resolveSimulatedUser(profileName);
      setStudentName(resolved.student_name);
      setStudentId(resolved.user_id);
      window.localStorage.setItem(STUDENT_NAME_KEY, resolved.student_name);
      window.localStorage.setItem(STUDENT_ID_KEY, String(resolved.user_id));
    } catch (error) {
      console.error('Failed to resolve student profile:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const interventionActive = Boolean(
    prediction?.intervention?.show_intervention && canReturnToQuestion
  );

  return (
    <div className="container mx-auto px-4 py-6 sm:py-8">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold">{t('studentTest.title')}</h1>
          <p className="text-muted-foreground">{t('studentTest.subtitle')}</p>
        </div>

        {!studentId && (
          <Card className="w-full max-w-md mx-auto">
            <CardHeader>
              <CardTitle>
                {language === 'ru' ? 'Выберите профиль студента' : 'Choose student profile'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                <Button
                  variant={selectedProfile === 'anna' ? 'default' : 'outline'}
                  onClick={() => {
                    setSelectedProfile('anna');
                    void resolveProfile('Анна');
                  }}
                  disabled={isLoading}
                >
                  Анна
                </Button>
                <Button
                  variant={selectedProfile === 'ivan' ? 'default' : 'outline'}
                  onClick={() => {
                    setSelectedProfile('ivan');
                    void resolveProfile('Иван');
                  }}
                  disabled={isLoading}
                >
                  Иван
                </Button>
                <Button
                  variant={selectedProfile === 'new' ? 'default' : 'outline'}
                  onClick={() => setSelectedProfile('new')}
                  disabled={isLoading}
                >
                  {language === 'ru' ? 'Новый студент' : 'New student'}
                </Button>
              </div>
              {selectedProfile === 'new' && (
                <>
                  <Input
                    value={studentNameInput}
                    onChange={(e) => setStudentNameInput(e.target.value)}
                    placeholder={language === 'ru' ? 'Введите имя' : 'Enter student name'}
                  />
                  <Button className="w-full" disabled={isLoading} onClick={handleResolveStudent}>
                    {language === 'ru' ? 'Войти' : 'Login'}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        )}

        {studentId && studentName && (
          <div className="flex items-center justify-center gap-3 text-sm text-muted-foreground">
            <span>
              {language === 'ru' ? 'Текущий студент:' : 'Current student:'} {studentName}
            </span>
            <Button variant="outline" size="sm" disabled={isLoading} onClick={handleSwitchStudent}>
              {t('studentTest.actions.switchStudent')}
            </Button>
          </div>
        )}

        {/* Mode Selection Screen */}
        {showModeSelection && studentId && (
          <div className="space-y-6">
            <Card className="w-full max-w-md mx-auto">
              <CardContent className="p-8 text-center space-y-4">
                <h3 className="text-lg font-semibold">
                  {t('studentTest.modeSelection.readyToStart')}
                </h3>
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
                requireConfidence={requireConfidence}
                skipConfidencePrompt={hasReturnedToQuestion}
                isLoading={isLoading}
              />
            )}

            {/* Answer Feedback */}
            {answerFeedback && (
              <Card className="w-full max-w-2xl mx-auto">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <span>{t('studentTest.feedback.title')}</span>
                    {!interventionActive && (
                      <Badge variant={answerFeedback.is_correct ? 'default' : 'destructive'}>
                        {answerFeedback.is_correct
                          ? t('studentTest.feedback.correct')
                          : t('studentTest.feedback.incorrect')}
                      </Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {!interventionActive && (
                    <p className="text-lg">{answerFeedback.feedback}</p>
                  )}

                  {prediction && (
                    <RiskBadge
                      risk={prediction.intervention.risk}
                      showIntervention={prediction.intervention.show_intervention}
                      messageRu={prediction.intervention.message_ru}
                      reasonCode={prediction.intervention.reason_code}
                      reasonText={prediction.intervention.reason_text}
                      onReturnToQuestion={handleReturnToQuestion}
                      onContinue={handleContinue}
                      showReturnButton={canReturnToQuestion}
                    />
                  )}

                  <div className="flex space-x-4">
                    {!interventionActive && (
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
                  <Card className="border-primary/20 bg-primary/5">
                    <CardContent className="p-4 space-y-2">
                      <p className="font-semibold">{calibrationProfile.title}</p>
                      <p className="text-sm text-muted-foreground">{calibrationProfile.description}</p>
                    </CardContent>
                  </Card>
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
