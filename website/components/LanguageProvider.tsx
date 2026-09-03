"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { type CommonKey, type Locale, locales, siteCopy, translations } from "@/lib/i18n";

type LanguageContextValue = { locale: Locale; setLocale: (locale: Locale) => void; t: (key: CommonKey) => string; copy: (key: keyof typeof siteCopy.en) => string };
const LanguageContext = createContext<LanguageContextValue | null>(null);

export default function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");

  useEffect(() => {
    const saved = window.localStorage.getItem("anastaria-locale") as Locale | null;
    const browserLocale = navigator.language as Locale;
    const nextLocale = saved && locales.includes(saved) ? saved : locales.includes(browserLocale) ? browserLocale : "en";
    const timer = window.setTimeout(() => setLocaleState(nextLocale), 0);
    return () => window.clearTimeout(timer);
  }, []);

  const setLocale = (nextLocale: Locale) => {
    setLocaleState(nextLocale);
    window.localStorage.setItem("anastaria-locale", nextLocale);
    document.documentElement.lang = nextLocale;
  };

  const value = useMemo(() => ({ locale, setLocale, t: (key: CommonKey) => translations[locale][key], copy: (key: keyof typeof siteCopy.en) => siteCopy[locale][key] }), [locale]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be used inside LanguageProvider.");
  return context;
}
