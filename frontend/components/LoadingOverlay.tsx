"use client"

import React from 'react'
import { useTranslation } from '@/lib/useTranslation'

export function LoadingOverlay() {
  const { isLoading } = useTranslation()

  if (!isLoading) return null

  return (
    <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center">
      <div className="flex flex-col items-center space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        <p className="text-sm text-muted-foreground animate-pulse">
          Switching language...
        </p>
      </div>
    </div>
  )
}
