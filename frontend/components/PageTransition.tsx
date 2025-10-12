"use client"

import React, { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'

export function PageTransition() {
  const [isTransitioning, setIsTransitioning] = useState(false)
  const pathname = usePathname()

  useEffect(() => {
    // Показываем плавный переход при смене страницы
    setIsTransitioning(true)
    
    // Скрываем переход через небольшую задержку
    const timer = setTimeout(() => {
      setIsTransitioning(false)
    }, 200)

    return () => clearTimeout(timer)
  }, [pathname])

  if (!isTransitioning) return null

  return (
    <div className="fixed inset-0 z-[9999] bg-white/80 backdrop-blur-sm transition-opacity duration-200 ease-in-out opacity-100">
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse">
          <div className="w-8 h-8 bg-primary/20 rounded-full"></div>
        </div>
      </div>
    </div>
  )
}
