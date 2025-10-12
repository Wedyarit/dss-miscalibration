import React from 'react'
import '../styles/globals.css'
import {Footer, Header} from '@/components/Layout'
import {cookies} from "next/headers";
import Providers from './providers'

export const metadata = {
    title: 'DSS Miscalibration Prediction System',
    description: 'A Decision Support System for predicting miscalibration in learning environments',
}

export default function RootLayout({
                                       children,
                                   }: {
    children: React.ReactNode
}) {
    const lang = cookies().get('lang')?.value ?? 'en'

    return (
        <html lang={lang}>
        <body className="min-h-screen bg-background font-sans antialiased">
        <Providers>
            <div className="relative flex min-h-screen flex-col">
                <Header/>
                <main className="flex-1">
                    {children}
                </main>
                <Footer/>
            </div>
        </Providers>
        </body>
        </html>
    )
}
