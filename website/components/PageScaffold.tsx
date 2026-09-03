"use client";

import Footer from "@/components/Footer";
import Header from "@/components/Header";
import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";

export default function PageScaffold({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  const { t } = useLanguage();
  return (
    <main className="min-h-screen bg-[#06070a] text-[#eee8dc]">
      <Header />
      <section className="relative overflow-hidden border-b border-amber-200/10 bg-[radial-gradient(circle_at_50%_-20%,rgba(180,117,29,.23),transparent_45%),linear-gradient(180deg,#11100d,#07080b)]">
        <div className="mu-runes absolute inset-0 opacity-25" />
        <div className="relative mx-auto max-w-[1500px] px-5 py-10 sm:px-8 sm:py-14">
          <Link
            href="/"
            className="text-xs font-bold uppercase tracking-[.22em] text-stone-500 transition hover:text-amber-300"
          >
            ← {t("home")}
          </Link>
          <div className="mt-12 text-center">
            <p className="text-[10px] font-bold uppercase tracking-[.55em] text-amber-500">
              {eyebrow}
            </p>
            <h1 className="mt-4 font-serif text-5xl font-black uppercase tracking-[.06em] text-[#f4ead6] sm:text-7xl">
              {title}
            </h1>
            <div className="mx-auto mt-5 h-px w-56 bg-gradient-to-r from-transparent via-amber-500/70 to-transparent" />
            <p className="mx-auto mt-6 max-w-2xl text-sm leading-7 text-stone-500">
              {description}
            </p>
          </div>
        </div>
      </section>
      <div className="relative mx-auto max-w-[1500px] px-5 py-10 sm:px-8">
        {children}
      </div>
      <Footer />
    </main>
  );
}
