"use client"

import React from 'react'
import { Button } from './ui/button'
import { useTranslation } from '@/lib/useTranslation'
import { ClientOnly } from './ClientOnly'

export function LanguageToggle() {
  const { language, setLanguage } = useTranslation()

  return (
    <ClientOnly fallback={
      <div className="flex items-center space-x-1 bg-muted/50 rounded-lg p-1">
        <Button
          variant="default"
          size="sm"
          className="h-8 px-3 text-xs font-medium"
        >
          🇺🇸 EN
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 px-3 text-xs font-medium"
        >
          🇷🇺 RU
        </Button>
      </div>
    }>
      <div className="flex items-center space-x-1 bg-muted/50 rounded-lg p-1">
        <Button
          variant={language === 'en' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setLanguage('en')}
          className="h-8 px-3 text-xs font-medium"
        >
          🇺🇸 EN
        </Button>
        <Button
          variant={language === 'ru' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setLanguage('ru')}
          className="h-8 px-3 text-xs font-medium"
        >
          🇷🇺 RU
        </Button>
      </div>
    </ClientOnly>
  )
}
