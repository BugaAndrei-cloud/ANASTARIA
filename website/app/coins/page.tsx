"use client";
import { useEffect, useState } from "react";
import PageScaffold from "@/components/PageScaffold";
import { getCommerceCatalog, type CommerceCatalog } from "@/lib/api";
import { useLanguage } from "@/components/LanguageProvider";
export default function CoinsPage() {
  const { copy } = useLanguage();
  const [data, setData] = useState<CommerceCatalog | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const c = new AbortController();
    getCommerceCatalog(c.signal)
      .then(setData)
      .catch((reason: unknown) => {
        if (!(reason instanceof DOMException && reason.name === "AbortError"))
          setError(
            reason instanceof Error ? reason.message : copy("noPackages"),
          );
      });
    return () => c.abort();
  }, [copy]);
  return (
    <PageScaffold
      eyebrow={copy("coins")}
      title={copy("coins")}
      description={copy("shopDescription")}
    >
      {error && (
        <div className="mu-panel rounded-xl p-10 text-red-400">{error}</div>
      )}
      {data && data.coin_packages.length === 0 && (
        <div className="mu-panel rounded-xl p-10 text-gray-500">
          {copy("noPackages")}
        </div>
      )}
      <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {data?.coin_packages.map((item) => (
          <article
            key={item.id}
            className={`mu-panel rounded-xl p-8 ${item.featured ? "border-amber-300/35" : ""}`}
          >
            <div className="relative">
              <p className="mu-kicker">
                {item.featured ? copy("comingSoon") : item.currency_code}
              </p>
              <h2 className="mt-4 text-2xl font-black">{item.title}</h2>
              <p className="mt-3 text-sm leading-6 text-gray-500">
                {item.description}
              </p>
              <div className="mt-7 text-4xl font-black text-amber-300">
                {item.coin_amount.toLocaleString()}
              </div>
              {item.bonus_amount > 0 && (
                <p className="mt-1 text-xs font-bold text-emerald-400">
                  + {item.bonus_amount.toLocaleString()} bonus
                </p>
              )}
              <div className="mt-6 border-t border-white/10 pt-5 text-lg font-bold">
                {(item.price_minor / 100).toFixed(2)} {item.settlement_currency}
              </div>
              <button
                disabled
                className="mt-5 w-full rounded border border-white/10 bg-white/5 py-3 text-xs font-black uppercase tracking-wider text-gray-600"
              >
                {copy("paymentsLater")}
              </button>
            </div>
          </article>
        ))}
      </section>
    </PageScaffold>
  );
}
