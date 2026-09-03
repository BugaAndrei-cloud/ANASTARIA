"use client";

import FeatureCards from "@/components/FeatureCards";
import Footer from "@/components/Footer";
import Header from "@/components/Header";
import Hero from "@/components/Hero";
import NewsPreview from "@/components/NewsPreview";
import ServerStatus from "@/components/ServerStatus";
import WorldPortal from "@/components/WorldPortal";
import { useLanguage } from "@/components/LanguageProvider";

export default function Home() {
  const { copy } = useLanguage();
  return (
    <main className="min-h-screen bg-[#08090d] text-white">
      <Header />

      <Hero />

      <ServerStatus />

      <WorldPortal />

      <NewsPreview />

      <FeatureCards />

      <section className="relative overflow-hidden border-t border-amber-200/10 bg-[radial-gradient(circle_at_50%_100%,rgba(180,117,29,.14),transparent_45%)]">
        <div className="mu-runes absolute inset-0 opacity-20" />
        <div className="relative mx-auto max-w-7xl px-6 py-24 text-center">
          <p className="text-[10px] font-black uppercase tracking-[.45em] text-amber-500">
            {copy("homeTagline")}
          </p>
          <h2 className="mt-4 font-serif text-4xl font-black uppercase tracking-[.06em] text-[#f4ead6]">
            {copy("journeyStarts")}
          </h2>

          <p className="mx-auto mt-4 max-w-xl text-gray-400">
            {copy("downloadDescription")}
          </p>
          <div className="mx-auto mt-7 h-px w-48 bg-gradient-to-r from-transparent via-amber-500/70 to-transparent" />
        </div>
      </section>

      <Footer />
    </main>
  );
}
