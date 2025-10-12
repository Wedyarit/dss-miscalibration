"use client"

import React from 'react'
import {useTranslation} from '@/lib/useTranslation'
import {LanguageToggle} from '@/components/LanguageToggle'
import {ClientOnly} from '@/components/ClientOnly'

export function Header() {
    const {t} = useTranslation()

    return (
        <header
            className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container mx-auto px-6 flex h-16 items-center justify-between">
                <div className="flex items-center space-x-8">
                    <a className="flex items-center space-x-2" href="/">
            <span className="text-xl font-bold">
                {t('header.title')}
            </span>
                    </a>
                    <nav className="hidden md:flex items-center space-x-6 text-sm font-medium">
                        <a className="transition-colors hover:text-foreground/80" href="/student/test">
                                {t('header.studentTest')}
                        </a>
                        <a className="transition-colors hover:text-foreground/80" href="/instructor/dashboard">
                                {t('header.instructorDashboard')}
                        </a>
                        <a className="transition-colors hover:text-foreground/80" href="/admin/questions">
                                {t('header.adminQuestions')}
                        </a>
                        <a className="transition-colors hover:text-foreground/80" href="/admin/datasets">
                                {t('header.adminDatasets')}
                        </a>
                    </nav>
                </div>
                <LanguageToggle/>
            </div>
        </header>
    )
}

export function Footer() {
    const {t} = useTranslation()

    return (
        <footer className="border-t py-6 md:py-0">
            <div
                className="container mx-auto px-6 flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row">
                <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
                        {t('footer.description')}
                </p>
            </div>
        </footer>
    )
}
