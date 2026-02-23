'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { sessionsApi } from '@/lib/api';
import { useTranslation } from '@/lib/useTranslation';

const STUDENT_NAME_KEY = 'dss.student.name';
const STUDENT_ID_KEY = 'dss.student.id';

export default function StudentLoginPage() {
  const [newStudentName, setNewStudentName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const { language } = useTranslation();

  const loginAs = async (name: string) => {
    try {
      setIsLoading(true);
      const resolved = await sessionsApi.resolveSimulatedUser(name);
      window.localStorage.setItem(STUDENT_NAME_KEY, resolved.student_name);
      window.localStorage.setItem(STUDENT_ID_KEY, String(resolved.user_id));
      router.push('/student/test');
    } catch (error) {
      console.error('Failed to login as student:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewStudent = async () => {
    if (!newStudentName.trim()) return;
    await loginAs(newStudentName.trim());
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mx-auto max-w-md space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>
              {language === 'ru' ? 'Вход студента' : 'Student login'}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button className="w-full" variant="outline" onClick={() => void loginAs('Анна')} disabled={isLoading}>
              Анна
            </Button>
            <Button className="w-full" variant="outline" onClick={() => void loginAs('Иван')} disabled={isLoading}>
              Иван
            </Button>
            <div className="space-y-2 pt-2">
              <Input
                value={newStudentName}
                onChange={(e) => setNewStudentName(e.target.value)}
                placeholder={language === 'ru' ? 'Новый студент' : 'New student'}
              />
              <Button className="w-full" onClick={() => void handleNewStudent()} disabled={isLoading}>
                {language === 'ru' ? 'Войти' : 'Login'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
