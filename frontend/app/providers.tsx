import { cookies } from 'next/headers';
import type { Language } from '@/lib/i18n';
import { TranslationProvider } from '@/lib/useTranslation';

export default function Providers({ children }: { children: React.ReactNode }) {
  const cookieStore = cookies();
  const initialLanguage = (cookieStore.get('lang')?.value as Language) ?? 'en';

  return <TranslationProvider initialLanguage={initialLanguage}>{children}</TranslationProvider>;
}
