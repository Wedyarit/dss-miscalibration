"use client"

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { ConfidenceSlider } from './ConfidenceSlider'
import { useTranslation } from '@/lib/useTranslation'

interface QuestionCardProps {
  question: {
    id: number
    stem: string
    options: string[]
    correct_option: number
    tags: string[]
    difficulty_hint?: number
  }
  onAnswer: (chosenOption: number, confidence?: number, responseTime?: number) => void
  mode: 'standard' | 'self_confidence'
  isLoading?: boolean
}

export function QuestionCard({ question, onAnswer, mode, isLoading = false }: QuestionCardProps) {
  const [selectedOption, setSelectedOption] = useState<number | null>(null)
  const [confidence, setConfidence] = useState<number>(60)
  const [startTime] = useState(Date.now())
  const { t } = useTranslation()

  const handleSubmit = () => {
    if (selectedOption === null) return

    const responseTime = Date.now() - startTime
    const confidenceValue = mode === 'self_confidence' ? confidence / 100 : undefined

    onAnswer(selectedOption, confidenceValue, responseTime)
  }

  const isConfidenceRequired = mode === 'self_confidence'
  const canSubmit = selectedOption !== null && (!isConfidenceRequired || confidence !== undefined)

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl">{t('studentTest.questionTitle').replace('{id}', question.id.toString())}</CardTitle>
          <div className="flex gap-2">
            {question.tags.map((tag) => (
              <Badge key={tag} variant="secondary">{tag}</Badge>
            ))}
            {question.difficulty_hint && (
              <Badge variant="outline">{t('adminQuestions.table.difficulty')}: {question.difficulty_hint}/10</Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="text-lg leading-relaxed">
          {question.stem}
        </div>

        <div className="space-y-3">
          {question.options.map((option, index) => (
            <label
              key={index}
              className={`flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                selectedOption === index
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:bg-muted/50'
              }`}
            >
              <input
                type="radio"
                name="option"
                value={index}
                checked={selectedOption === index}
                onChange={() => setSelectedOption(index)}
                className="w-4 h-4 text-primary"
              />
              <span className="flex-1">
                <span className="font-medium">{String.fromCharCode(65 + index)}.</span> {option}
              </span>
            </label>
          ))}
        </div>

        {isConfidenceRequired && (
          <ConfidenceSlider
            onConfidenceChange={setConfidence}
            disabled={isLoading}
          />
        )}

        <Button
          onClick={handleSubmit}
          disabled={!canSubmit || isLoading}
          className="w-full"
          size="lg"
        >
          {isLoading ? t('common.loading') : t('studentTest.submitAnswer')}
        </Button>
      </CardContent>
    </Card>
  )
}
