'use client';

import React, { createContext, useContext, useEffect, useLayoutEffect, useMemo } from 'react';
import { Language, translations } from './i18n';
import { useLanguageStore } from './languageStore';

type TranslationContextType = {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: ((key: string) => string) & {
    <T extends string[]>(key: string): string | T;
    <T extends Record<string, unknown>>(key: string): string | T;
  };
  tArray: (key: string) => string[];
  tObject: <T extends Record<string, unknown>>(key: string) => T | undefined;
  isLoading: boolean;
  isHydrated: boolean;
};

const TranslationContext = createContext<TranslationContextType | undefined>(undefined);

export function TranslationProvider({
  children,
  initialLanguage,
}: {
  children: React.ReactNode;
  initialLanguage: Language;
}) {
  const { language, setLanguage, isHydrated, setHydrated } = useLanguageStore();

  const activeLanguage = isHydrated ? language : initialLanguage;

  useLayoutEffect(() => {
    useLanguageStore.setState({ language: initialLanguage });
  }, [initialLanguage]);

  useEffect(() => {
    setHydrated();
  }, [setHydrated]);

  useEffect(() => {
    document.cookie = `lang=${language}; path=/; max-age=31536000; samesite=lax`;
  }, [language]);

  const translate = useMemo(() => {
    return (key: string): string | string[] | Record<string, unknown> => {
      const keys = key.split('.');
      let value: unknown = translations[activeLanguage];
      for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
          value = (value as Record<string, unknown>)[k];
        } else {
          return key;
        }
      }
      if (typeof value === 'string') {
        return value;
      }
      if (Array.isArray(value)) {
        return value as string[];
      }
      if (value && typeof value === 'object') {
        return value as Record<string, unknown>;
      }
      return key;
    };
  }, [activeLanguage]);

  const t = useMemo(() => {
    const baseT = (key: string): string => {
      const result = translate(key);
      return typeof result === 'string' ? result : key;
    };

    return baseT as TranslationContextType['t'];
  }, [translate]);

  const tArray = useMemo(() => {
    return (key: string): string[] => {
      const result = translate(key);
      return Array.isArray(result) ? result : [];
    };
  }, [translate]);

  const tObject = useMemo(() => {
    return <T extends Record<string, unknown>>(key: string): T | undefined => {
      const result = translate(key);
      if (result && typeof result === 'object' && !Array.isArray(result)) {
        return result as T;
      }
      return undefined;
    };
  }, [translate]);

  return (
    <TranslationContext.Provider
      value={{
        language: activeLanguage,
        setLanguage,
        t,
        tArray,
        tObject,
        isLoading: false,
        isHydrated,
      }}
    >
      {children}
    </TranslationContext.Provider>
  );
}

export function useTranslation() {
  const context = useContext(TranslationContext);
  if (context === undefined) {
    throw new Error('useTranslation must be used within a TranslationProvider');
  }
  return context;
}
