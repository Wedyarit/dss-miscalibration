'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useTranslation } from '@/lib/useTranslation';

export default function HomePage() {
  const { t, tArray } = useTranslation();

  return (
    <div className="container mx-auto px-6 py-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold tracking-tight">{t('home.title')}</h1>
          <p className="text-xl text-muted-foreground">{t('home.subtitle')}</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">{t('nav.studentTest')}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                {t('home.studentTestDescription')}
              </p>
              <Button asChild className="w-full">
                <Link href="/student/login">{t('home.startTestButton')}</Link>
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">{t('nav.instructorDashboard')}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                {t('home.instructorDescription')}
              </p>
              <Button asChild variant="outline" className="w-full">
                <Link href="/instructor/dashboard">{t('home.viewDashboardButton')}</Link>
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">{t('nav.adminQuestions')}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                {t('home.adminQuestionsDescription')}
              </p>
              <Button asChild variant="outline" className="w-full">
                <Link href="/admin/questions">{t('home.manageQuestionsButton')}</Link>
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">{t('nav.adminDatasets')}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                {t('home.adminDatasetsDescription')}
              </p>
              <Button asChild variant="outline" className="w-full">
                <Link href="/admin/datasets">{t('home.manageDataButton')}</Link>
              </Button>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{t('home.aboutTitle')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>{t('home.aboutDescription')}</p>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <h3 className="font-semibold mb-2">{t('home.keyFeatures')}</h3>
                <ul className="text-sm text-muted-foreground space-y-1">
                  {tArray('home.features').map((feature: string) => (
                    <li key={feature}>• {feature}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="font-semibold mb-2">{t('home.useCases')}</h3>
                <ul className="text-sm text-muted-foreground space-y-1">
                  {tArray('home.useCasesList').map((useCase: string) => (
                    <li key={useCase}>• {useCase}</li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
