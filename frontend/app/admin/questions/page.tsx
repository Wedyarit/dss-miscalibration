'use client';

import { useCallback, useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { questionsApi } from '@/lib/api';
import { Question } from '@/lib/types';
import { useTranslation } from '@/lib/useTranslation';

export default function AdminQuestionsPage() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [newQuestion, setNewQuestion] = useState({
    stem: '',
    options: ['', '', '', ''],
    correct_option: 0,
    tags: '',
    difficulty_hint: '',
  });
  const { t, language } = useTranslation();

  const loadQuestions = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await questionsApi.list(0, 100, undefined, language);
      setQuestions(response.questions);
    } catch (error) {
      console.error('Failed to load questions:', error);
    } finally {
      setIsLoading(false);
    }
  }, [language]);

  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);

  const handleCreateQuestion = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      setIsCreating(true);

      const questionData = {
        stem: newQuestion.stem,
        options: newQuestion.options.filter((opt) => opt.trim() !== ''),
        correct_option: newQuestion.correct_option,
        tags: newQuestion.tags
          .split(',')
          .map((tag) => tag.trim())
          .filter((tag) => tag !== ''),
        difficulty_hint: newQuestion.difficulty_hint
          ? parseFloat(newQuestion.difficulty_hint)
          : undefined,
      };

      await questionsApi.create(questionData);

      setNewQuestion({
        stem: '',
        options: ['', '', '', ''],
        correct_option: 0,
        tags: '',
        difficulty_hint: '',
      });

      await loadQuestions();
    } catch (error) {
      console.error('Failed to create question:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const updateOption = (index: number, value: string) => {
    const newOptions = [...newQuestion.options];
    newOptions[index] = value;
    setNewQuestion({ ...newQuestion, options: newOptions });
  };

  const addOption = () => {
    if (newQuestion.options.length < 6) {
      setNewQuestion({
        ...newQuestion,
        options: [...newQuestion.options, ''],
      });
    }
  };

  const removeOption = (index: number) => {
    if (newQuestion.options.length > 2) {
      const newOptions = newQuestion.options.filter((_, i) => i !== index);
      setNewQuestion({
        ...newQuestion,
        options: newOptions,
        correct_option: Math.min(newQuestion.correct_option, newOptions.length - 1),
      });
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold">{t('adminQuestions.title')}</h1>
          <p className="text-muted-foreground">{t('adminQuestions.subtitle')}</p>
        </div>

        {/* Create Question Form */}
        <Card>
          <CardHeader>
            <CardTitle>{t('adminQuestions.createNew')}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateQuestion} className="space-y-4">
              <div>
                <label htmlFor="question-text" className="text-sm font-medium">
                  {t('adminQuestions.form.questionText')}
                </label>
                <textarea
                  id="question-text"
                  value={newQuestion.stem}
                  onChange={(e) => setNewQuestion({ ...newQuestion, stem: e.target.value })}
                  className="w-full mt-1 p-3 border rounded-md"
                  rows={3}
                  placeholder={t('adminQuestions.placeholders.questionText')}
                  required
                />
              </div>

              <fieldset>
                <legend className="text-sm font-medium">{t('adminQuestions.form.options')}</legend>
                <div className="space-y-2 mt-1">
                  {newQuestion.options.map((option, index) => (
                    <div key={`option-${index}-${option}`} className="flex items-center space-x-2">
                      <input
                        type="radio"
                        name="correct_option"
                        checked={newQuestion.correct_option === index}
                        onChange={() => setNewQuestion({ ...newQuestion, correct_option: index })}
                        className="w-4 h-4"
                      />
                      <Input
                        value={option}
                        onChange={(e) => updateOption(index, e.target.value)}
                        placeholder={t('adminQuestions.placeholders.option').replace(
                          '{number}',
                          (index + 1).toString()
                        )}
                        required
                      />
                      {newQuestion.options.length > 2 && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => removeOption(index)}
                        >
                          {t('adminQuestions.form.removeOption')}
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
                {newQuestion.options.length < 6 && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={addOption}
                    className="mt-2"
                  >
                    {t('adminQuestions.form.addOption')}
                  </Button>
                )}
              </fieldset>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">{t('adminQuestions.form.tags')}</label>
                  <Input
                    value={newQuestion.tags}
                    onChange={(e) => setNewQuestion({ ...newQuestion, tags: e.target.value })}
                    placeholder={t('adminQuestions.placeholders.tags')}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">
                    {t('adminQuestions.form.difficulty')}
                  </label>
                  <Input
                    type="number"
                    min="0"
                    max="10"
                    step="0.1"
                    value={newQuestion.difficulty_hint}
                    onChange={(e) =>
                      setNewQuestion({ ...newQuestion, difficulty_hint: e.target.value })
                    }
                    placeholder={t('adminQuestions.placeholders.difficulty')}
                    className="mt-1"
                  />
                </div>
              </div>

              <Button type="submit" disabled={isCreating} className="w-full">
                {isCreating ? t('common.loading') : t('adminQuestions.form.submit')}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Questions List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>
                {t('adminQuestions.questionBank')} ({questions.length})
              </span>
              <Button onClick={loadQuestions} variant="outline" size="sm">
                {t('adminQuestions.actions.refresh')}
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                <p>Loading questions...</p>
              </div>
            ) : questions.length > 0 ? (
              <div className="space-y-4">
                {questions.map((question) => (
                  <Card key={question.id} className="p-4">
                    <div className="space-y-2">
                      <div className="flex items-start justify-between">
                        <h3 className="font-medium">{question.stem}</h3>
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline">#{question.id}</Badge>
                          {question.difficulty_hint && (
                            <Badge variant="secondary">
                              {t('adminQuestions.table.difficulty')}: {question.difficulty_hint}
                            </Badge>
                          )}
                        </div>
                      </div>

                      <div className="space-y-1">
                        {question.options.map((option, index) => (
                          <div
                            key={`option-${index}-${option}`}
                            className={`text-sm p-2 rounded ${
                              index === question.correct_option
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100'
                            }`}
                          >
                            <span className="font-medium">{String.fromCharCode(65 + index)}.</span>{' '}
                            {option}
                            {index === question.correct_option && (
                              <Badge variant="default" className="ml-2">
                                {t('adminQuestions.table.correct')}
                              </Badge>
                            )}
                          </div>
                        ))}
                      </div>

                      <div className="flex flex-wrap gap-1">
                        {question.tags.map((tag) => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                {t('adminQuestions.noQuestions')}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
