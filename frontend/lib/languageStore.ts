'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Language = 'en' | 'ru';

interface LanguageState {
  language: Language;
  setLanguage: (language: Language) => void;
  isHydrated: boolean;
  setHydrated: () => void;
}

export const useLanguageStore = create<LanguageState>()(
  persist(
    (set) => ({
      language: 'en',
      setLanguage: (language) => set({ language }),
      isHydrated: false,
      setHydrated: () => set({ isHydrated: true }),
    }),
    {
      name: 'language-storage',
      partialize: (state) => ({ language: state.language }),
    }
  )
);
