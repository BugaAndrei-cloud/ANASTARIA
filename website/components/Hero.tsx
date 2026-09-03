"use client";

import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";

export default function Hero() {
  const { copy, t } = useLanguage();
  return (
    <section className="relative isolate min-h-[calc(100vh-5rem)] overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_26%,rgba(245,158,11,0.2),transparent_28%),radial-gradient(circle_at_12%_60%,rgba(120,80,20,0.12),transparent_28%),radial-gradient(circle_at_88%_55%,rgba(75,45,110,.1),transparent_25%),linear-gradient(180deg,#08090d_0%,#0b0c11_45%,#08090d_100%)]" />
      <span className="ember absolute left-[14%] top-[35%] h-1 w-1 rounded-full bg-amber-300 shadow-[0_0_12px_3px_rgba(245,190,70,.4)]" />
      <span className="ember absolute right-[18%] top-[48%] h-1.5 w-1.5 rounded-full bg-amber-400 shadow-[0_0_14px_3px_rgba(245,190,70,.35)] [animation-delay:1.4s]" />

      <div className="absolute left-1/2 top-[28%] h-[28rem] w-[28rem] -translate-x-1/2 rounded-full bg-amber-500/[0.06] blur-[100px]" />
      <div className="mu-runes absolute inset-0 opacity-30" />
      <div className="pointer-events-none absolute left-1/2 top-1/2 -z-0 -translate-x-1/2 -translate-y-1/2 whitespace-nowrap font-serif text-[18vw] font-black tracking-[.12em] text-white/[.018]">
        ANASTARIA
      </div>
      <div className="mu-orbit absolute left-1/2 top-1/2 h-[34rem] w-[34rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-amber-300/[.07]" />

      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-amber-400/30 to-transparent" />

      <div className="relative mx-auto flex min-h-[calc(100vh-5rem)] max-w-7xl items-center justify-center px-6 py-24 text-center">
        <div className="max-w-5xl">
          <div className="mb-8 inline-flex items-center gap-3 rounded-full border border-emerald-400/20 bg-emerald-400/[0.04] px-4 py-2">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-50" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_14px_rgba(52,211,153,0.9)]" />
            </span>

            <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-gray-300">
              {copy("serverStatus")}
            </span>
          </div>

          <p className="text-xs font-bold uppercase tracking-[0.5em] text-amber-400 sm:text-sm">
            {copy("homeTagline")}
          </p>

          <h1 className="mt-5 font-serif text-6xl font-black tracking-[.04em] text-[#f4ead6] drop-shadow-[0_8px_35px_rgba(0,0,0,.8)] sm:text-7xl md:text-8xl lg:text-9xl">
            ANASTARIA
          </h1>

          <div className="mx-auto mt-7 flex items-center justify-center gap-4">
            <span className="h-px w-12 bg-gradient-to-r from-transparent to-amber-400/70 sm:w-20" />
            <span className="h-1.5 w-1.5 rotate-45 border border-amber-400 bg-amber-400/20" />
            <span className="h-px w-12 bg-gradient-to-l from-transparent to-amber-400/70 sm:w-20" />
          </div>

          <h2 className="mt-7 text-2xl font-semibold tracking-wide text-gray-200 sm:text-3xl md:text-4xl">
            {copy("journeyStarts")}
          </h2>

          <p className="mx-auto mt-6 max-w-2xl text-base leading-8 text-gray-400 sm:text-lg">
            {copy("homeDescription")}
          </p>

          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/register"
              className="group relative w-full overflow-hidden rounded-lg bg-amber-500 px-9 py-4 text-sm font-black tracking-[0.08em] text-black shadow-xl shadow-amber-500/10 transition hover:-translate-y-1 hover:bg-amber-400 sm:w-auto"
            >
              <span className="relative z-10">{t("play")}</span>

              <span className="absolute inset-0 -translate-x-full bg-white/20 transition-transform duration-500 group-hover:translate-x-full" />
            </Link>

            <Link
              href="/download"
              className="w-full rounded-lg border border-white/15 bg-white/[0.04] px-9 py-4 text-sm font-bold tracking-[0.08em] text-white transition hover:-translate-y-1 hover:border-white/30 hover:bg-white/[0.08] sm:w-auto"
            >
              {t("download")}
            </Link>
          </div>

          <div className="mt-16 flex flex-wrap items-center justify-center gap-x-7 gap-y-3 text-[10px] font-semibold uppercase tracking-[0.25em] text-gray-600 sm:gap-x-10">
            <span>{copy("epicWorld")}</span>
            <span className="hidden sm:inline">◆</span>
            <span>{copy("guildWars")}</span>
            <span className="hidden sm:inline">◆</span>
            <span>{copy("competitivePvp")}</span>
            <span className="hidden sm:inline">◆</span>
            <span>{copy("buildLegacy")}</span>
          </div>
        </div>
      </div>

      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[#08090d] via-[#08090d]/70 to-transparent" />
    </section>
  );
}
