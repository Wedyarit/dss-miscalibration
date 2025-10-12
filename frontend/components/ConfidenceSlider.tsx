"use client"

import React, {useState} from 'react'
import {Card, CardContent, CardHeader, CardTitle} from './ui/card'
import {Button} from './ui/button'
import {useTranslation} from '@/lib/useTranslation'
import {ClientOnly} from './ClientOnly'

interface ConfidenceSliderProps {
    onConfidenceChange: (confidence: number) => void
    disabled?: boolean
}

const confidenceLevels = [
    {value: 20, label: 'studentTest.confidence.veryLow', color: 'text-red-600'},
    {value: 40, label: 'studentTest.confidence.low', color: 'text-orange-600'},
    {value: 60, label: 'studentTest.confidence.medium', color: 'text-yellow-600'},
    {value: 80, label: 'studentTest.confidence.high', color: 'text-blue-600'},
    {value: 100, label: 'studentTest.confidence.veryHigh', color: 'text-green-600'}
]

export function ConfidenceSlider({onConfidenceChange, disabled = false}: ConfidenceSliderProps) {
    const [confidence, setConfidence] = useState(60)
    const {t} = useTranslation()

    const handleConfidenceChange = (value: number) => {
        setConfidence(value)
        onConfidenceChange(value)
    }

    const getCurrentLevel = () => {
        return confidenceLevels.find(level => confidence <= level.value) || confidenceLevels[4]
    }

    const currentLevel = getCurrentLevel()

    return (
        <Card className="w-full">
            <CardHeader>
                <CardTitle className="text-lg">
                        {t('studentTest.confidence.selectConfidence')}
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="space-y-3">
                    <div className="flex justify-between text-sm text-muted-foreground">
                        <span>0%</span>
                        <span className={`font-medium ${currentLevel.color}`}>
              {confidence}% - <ClientOnly fallback="Medium">{t(currentLevel.label)}</ClientOnly>
            </span>
                        <span>100%</span>
                    </div>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        step="5"
                        value={confidence}
                        onChange={(e) => handleConfidenceChange(parseInt(e.target.value))}
                        disabled={disabled}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                        style={{
                            background: `linear-gradient(to right, #ef4444 0%, #f97316 20%, #eab308 40%, #3b82f6 60%, #22c55e 80%, #22c55e 100%)`
                        }}
                    />
                </div>

                <div className="grid grid-cols-5 gap-2">
                    {confidenceLevels.map((level) => (
                        <Button
                            key={level.value}
                            variant={"outline"}
                            size="sm"
                            onClick={() => handleConfidenceChange(level.value)}
                            disabled={disabled}
                            className={`text-xs ${level.color} ${confidence === level.value ? `bg-accent` : ''}`}
                        >
                            <ClientOnly
                                fallback={level.value === 20 ? "Very Low" : level.value === 40 ? "Low" : level.value === 60 ? "Medium" : level.value === 80 ? "High" : "Very High"}>
                                {t(level.label)}
                            </ClientOnly>
                        </Button>
                    ))}
                </div>
            </CardContent>
        </Card>
    )
}
