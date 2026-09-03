"use client";

import { useEffect, useRef, useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { localeFlags, localeNames, locales } from "@/lib/i18n";

export default function LanguageMenu() {
  const { locale, setLocale } = useLanguage();
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => { const close = (event: MouseEvent) => { if (!root.current?.contains(event.target as Node)) setOpen(false); }; document.addEventListener("mousedown", close); return () => document.removeEventListener("mousedown", close); }, []);
  return <div ref={root} className="relative"><button type="button" aria-label={`Language: ${localeNames[locale]}`} aria-expanded={open} onClick={() => setOpen((value) => !value)} className="flex h-10 items-center gap-2 rounded-md border border-amber-300/20 bg-gradient-to-b from-white/[.07] to-black/20 px-3 shadow-[0_8px_25px_rgba(0,0,0,.35),inset_0_1px_rgba(255,255,255,.05)] transition hover:border-amber-300/45"><span className="text-xl drop-shadow-[0_3px_4px_rgba(0,0,0,.8)]">{localeFlags[locale]}</span><span className={`text-[9px] text-amber-200/60 transition ${open ? "rotate-180" : ""}`}>▼</span></button>{open && <div className="absolute right-0 top-12 z-50 grid w-52 gap-1 rounded-lg border border-amber-300/20 bg-[#0a0c11]/[.98] p-2 shadow-[0_22px_60px_rgba(0,0,0,.7)] backdrop-blur-xl">{locales.map((item) => <button key={item} type="button" onClick={() => { setLocale(item); setOpen(false); }} className={`flex items-center gap-3 rounded px-3 py-2 text-left text-xs transition ${locale === item ? "bg-amber-300/10 text-amber-200" : "text-gray-400 hover:bg-white/5 hover:text-white"}`}><span className="text-lg drop-shadow-md">{localeFlags[item]}</span><span>{localeNames[item]}</span>{locale === item && <span className="ml-auto text-amber-300">◆</span>}</button>)}</div>}</div>;
}
