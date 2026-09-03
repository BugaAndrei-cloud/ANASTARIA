"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import LanguageMenu from "@/components/LanguageMenu";
import { type CommonKey } from "@/lib/i18n";
import { getMe, type AccountMe } from "@/lib/api";

const navigation: { key: CommonKey; href: string }[] = [
  { key: "news", href: "/news" },
  { key: "rankings", href: "/rankings" },
  { key: "guides", href: "/guides" },
  { key: "shop", href: "/shop" },
  { key: "download", href: "/download" },
];

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [account, setAccount] = useState<AccountMe | null>(null);
  const pathname = usePathname();
  const { t, copy } = useLanguage();
  useEffect(() => {
    getMe()
      .then(setAccount)
      .catch(() => setAccount(null));
  }, [pathname]);

  return (
    <header className="sticky top-0 z-50 border-b border-amber-300/15 bg-[#07080c]/95 shadow-2xl shadow-black/30 backdrop-blur-xl">
      <div className="mx-auto flex min-h-20 max-w-[1500px] items-center justify-between gap-5 px-5 py-3">
        <Link
          href="/"
          className="group flex items-center gap-3"
          aria-label={`${"ANASTARIA"} ${t("home")}`}
          onClick={() => setMenuOpen(false)}
        >
          <div className="relative flex h-11 w-11 rotate-45 items-center justify-center border border-amber-400/45 bg-gradient-to-br from-amber-300/20 to-black shadow-[0_0_24px_rgba(212,160,50,.12)]">
            <span className="-rotate-45 text-xl font-black text-amber-300">
              A
            </span>
          </div>
          <div>
            <div className="text-xl font-black tracking-[0.18em] text-white group-hover:text-amber-300">
              ANASTARIA
            </div>
            <div className="text-[8px] font-bold uppercase tracking-[0.45em] text-amber-200/45">
              {copy("homeTagline")}
            </div>
          </div>
        </Link>
        <nav
          aria-label={t("home")}
          className="hidden items-center gap-1 xl:flex"
        >
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded px-3 py-2 text-[11px] font-bold uppercase tracking-[.12em] transition ${pathname === item.href ? "bg-amber-400/10 text-amber-300" : "text-gray-400 hover:bg-white/5 hover:text-amber-300"}`}
            >
              {t(item.key)}
            </Link>
          ))}
          <Link
            href="/coins"
            className={`rounded px-3 py-2 text-[11px] font-black uppercase tracking-[.12em] transition ${pathname === "/coins" ? "bg-amber-400/15 text-amber-300" : "text-amber-300 hover:bg-amber-400/10"}`}
          >
            {copy("coins")}
          </Link>
        </nav>
        <div className="hidden items-center gap-2 md:flex">
          <LanguageMenu />
          {account ? (
            <Link
              href="/dashboard"
              className="rounded border border-amber-300/35 px-4 py-2.5 text-xs font-bold text-amber-300 transition hover:bg-amber-300/10"
            >
              {account.role === "game_master"
                ? copy("gmDashboard")
                : copy("dashboard")}
            </Link>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded border border-white/15 px-4 py-2.5 text-xs font-bold text-gray-300 transition hover:border-amber-300/40 hover:text-white"
              >
                {t("login")}
              </Link>
              <Link
                href="/register"
                className="rounded bg-gradient-to-b from-amber-300 to-amber-600 px-5 py-2.5 text-xs font-black uppercase tracking-wide text-black shadow-lg shadow-amber-500/10 transition hover:-translate-y-0.5 hover:brightness-110"
              >
                {t("play")}
              </Link>
            </>
          )}
        </div>
        <button
          type="button"
          aria-label={menuOpen ? "×" : "☰"}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((open) => !open)}
          className="flex h-10 w-10 items-center justify-center rounded border border-white/10 bg-white/5 text-gray-300 xl:hidden"
        >
          {menuOpen ? "×" : "☰"}
        </button>
      </div>
      {menuOpen && (
        <div className="border-t border-amber-300/10 bg-[#08090d] xl:hidden">
          <nav
            className="mx-auto grid max-w-7xl gap-1 px-6 py-5 sm:grid-cols-2"
            aria-label="Mobile navigation"
          >
            {navigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMenuOpen(false)}
                className="border-b border-white/5 py-3 text-xs font-bold uppercase tracking-wider text-gray-400 hover:text-amber-300"
              >
                {t(item.key)}
              </Link>
            ))}
            <Link
              href="/coins"
              onClick={() => setMenuOpen(false)}
              className="border-b border-white/5 py-3 text-xs font-black uppercase tracking-wider text-amber-300"
            >
              {copy("coins")}
            </Link>
            <Link
              href="/contact"
              onClick={() => setMenuOpen(false)}
              className="py-3 text-xs font-bold uppercase tracking-wider text-gray-400"
            >
              {t("contact")}
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}
