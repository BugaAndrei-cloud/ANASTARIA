"use client";

import Link from "next/link";

import { useNews } from "@/hooks/useNews";
import { useLanguage } from "@/components/LanguageProvider";

export type NewsItem = {
  id: string;
  category: string;
  title: string;
  excerpt: string;
  href: string;
  publishedAt: string;
};

type NewsPreviewProps = {
  items?: NewsItem[];
};

export default function NewsPreview({
  items,
}: NewsPreviewProps) {
  const news = useNews();
  const { locale, copy, t } = useLanguage();
  const visibleItems = items ?? news.items.slice(0, 3).map((item) => ({
    id: String(item.id),
    category: item.category,
    title: item.title,
    excerpt: item.summary ?? item.content ?? "",
    href: "/news",
    publishedAt: new Date(item.published_at ?? item.created_at).toLocaleDateString(locale),
  }));
  return (
    <section className="mx-auto max-w-7xl px-6 py-24">
      <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.35em] text-amber-400">
            {copy("latest")}
          </p>

          <h2 className="mt-3 text-4xl font-black tracking-tight text-white">
            {t("news")}
          </h2>

          <p className="mt-4 max-w-2xl text-base leading-7 text-gray-500">
            {copy("newsDescription")}
          </p>
        </div>

        <Link
          href="/news"
          className="text-sm font-bold uppercase tracking-wide text-gray-400 transition hover:text-amber-400"
        >
          {t("news")} →
        </Link>
      </div>

      <div className="mt-10 grid gap-6 md:grid-cols-3">
        {visibleItems.map((item) => (
          <article
            key={item.id}
            className="group flex h-full flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-7 transition duration-300 hover:-translate-y-1 hover:border-amber-400/30 hover:bg-white/[0.05]"
          >
            <div className="flex items-center justify-between gap-4">
              <span className="rounded-full border border-amber-400/20 bg-amber-400/5 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-amber-400">
                {item.category}
              </span>

              <span className="text-xs text-gray-600">
                {item.publishedAt}
              </span>
            </div>

            <h3 className="mt-6 text-xl font-bold leading-tight text-white transition group-hover:text-amber-400">
              {item.title}
            </h3>

            <p className="mt-4 flex-1 text-sm leading-7 text-gray-500">
              {item.excerpt}
            </p>

            <Link
              href={item.href}
              className="mt-7 inline-flex text-xs font-bold uppercase tracking-[0.15em] text-gray-400 transition hover:text-white"
            >
              {copy("readArticle")} →
            </Link>
          </article>
        ))}
      </div>
      {!news.loading && !news.error && visibleItems.length === 0 && (
        <p className="mt-10 rounded-xl border border-white/10 p-8 text-center text-sm text-gray-600">{copy("noNews")}</p>
      )}
    </section>
  );
}
