"use client";

import PageScaffold from "@/components/PageScaffold";
import { useLanguage } from "@/components/LanguageProvider";

export default function VoteForCoinsPage() {
  const { copy } = useLanguage();

  return (
    <PageScaffold
      eyebrow={copy("voteForCoins")}
      title={copy("voteForCoins")}
      description={copy("voteDescription")}
    >
      <section className="mu-panel mx-auto max-w-2xl rounded-xl p-8 text-center sm:p-12">
        <div className="relative">
          <span className="text-5xl text-amber-300">◆</span>
          <h2 className="mt-5 text-2xl font-black">
            {copy("voteUnavailable")}
          </h2>
          <p className="mt-4 leading-7 text-gray-400">
            {copy("voteDescription")}
          </p>
          <button
            type="button"
            disabled
            className="mt-8 rounded border border-white/10 bg-white/5 px-7 py-3 text-xs font-black uppercase tracking-wider text-gray-600"
          >
            {copy("voteNow")}
          </button>
        </div>
      </section>
    </PageScaffold>
  );
}
