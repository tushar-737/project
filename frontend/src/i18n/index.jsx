import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { en } from './en';
import { hi } from './hi';

const DICTIONARIES = { en, hi };
const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(() => {
    try {
      return localStorage.getItem('ner_lang') || 'en';
    } catch {
      return 'en';
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('ner_lang', lang);
    } catch {
      /* ignore */
    }
    document.documentElement.lang = lang;
  }, [lang]);

  const value = useMemo(() => {
    const dict = DICTIONARIES[lang] || en;
    const t = (key) =>
      key.split('.').reduce((o, k) => (o && o[k] !== undefined ? o[k] : key), dict);
    return { lang, setLang, t };
  }, [lang]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

/** useTranslation(): { t, lang, setLang } */
export function useTranslation() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useTranslation must be used inside LanguageProvider');
  return ctx;
}
