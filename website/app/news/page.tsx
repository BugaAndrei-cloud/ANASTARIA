"use client";
import Link from "next/link";
import PageScaffold from "@/components/PageScaffold";
import { useLanguage } from "@/components/LanguageProvider";
import { useNews } from "@/hooks/useNews";

export default function NewsPage() {
  const { locale, copy, t } = useLanguage(); const { items, loading, error } = useNews();
  return <PageScaffold eyebrow={copy("latest")} title={t("news")} description={copy("newsDescription")}>
    {loading ? <div className="mu-panel rounded-xl p-12 text-center text-gray-500">{copy("loading")}</div> : error ? <div className="mu-panel rounded-xl p-12 text-center text-red-400">{error}</div> : items.length === 0 ? <div className="mu-panel rounded-xl p-12 text-center"><span className="text-3xl text-amber-300">◆</span><h2 className="mt-5 text-2xl font-black">{copy("noNews")}</h2><p className="mt-3 text-gray-500">{copy("noNewsDescription")}</p></div> : <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">{items.map((item) => <article key={item.id} className="mu-panel group flex min-h-80 flex-col overflow-hidden rounded-xl p-7 transition hover:-translate-y-1 hover:border-amber-300/45"><div className="relative flex flex-1 flex-col"><div className="flex items-center justify-between"><span className="rounded border border-amber-300/20 bg-amber-300/5 px-3 py-1 text-[10px] font-black uppercase tracking-wider text-amber-300">{item.category}</span><time className="text-xs text-gray-600">{new Date(item.published_at ?? item.created_at).toLocaleDateString(locale)}</time></div><h2 className="mt-7 text-2xl font-black group-hover:text-amber-200">{item.title}</h2><p className="mt-4 flex-1 text-sm leading-7 text-gray-500">{item.summary ?? item.content ?? ""}</p><Link href="/news" className="mt-7 text-xs font-black uppercase tracking-wider text-amber-300">{copy("readArticle")} →</Link></div></article>)}</div>}
  </PageScaffold>;
}
