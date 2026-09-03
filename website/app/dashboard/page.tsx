"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { getMe, logoutAccount, type AccountMe } from "@/lib/api";
import { useLanguage } from "@/components/LanguageProvider";

const card =
  "group rounded-xl border border-white/10 bg-black/30 p-6 transition hover:-translate-y-0.5 hover:border-amber-300/35";

function PlayerDashboard({ account }: { account: AccountMe }) {
  const { copy } = useLanguage();
  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Link href="/profile" className={card}>
          <span className="text-2xl">⚙</span>
          <h2 className="mt-3 text-lg font-black text-amber-100">
            {copy("accountSettings")}
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            {copy("profilePreferences")}
          </p>
        </Link>
        <Link href="/forgot-password" className={card}>
          <span className="text-2xl">◆</span>
          <h2 className="mt-3 text-lg font-black text-amber-100">
            {copy("security")}
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            {copy("recoverChangePassword")}
          </p>
        </Link>
        <Link href="/download" className={card}>
          <span className="text-2xl">↓</span>
          <h2 className="mt-3 text-lg font-black text-amber-100">
            {copy("play")}
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            {copy("downloadLatestClient")}
          </p>
        </Link>
        <Link href="/vote-for-coins" className={card}>
          <span className="text-2xl">◆</span>
          <h2 className="mt-3 text-lg font-black text-amber-100">
            {copy("voteForCoins")}
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            {copy("voteDescription")}
          </p>
        </Link>
      </div>
      <section className="mt-10">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-black">{copy("characters")}</h2>
          <span className="text-xs text-gray-600">
            {account.characters.length} {copy("total")}
          </span>
        </div>
        {account.characters.length === 0 ? (
          <p className="mt-4 rounded-xl border border-white/10 p-6 text-gray-500">
            {copy("noCharacters")}
          </p>
        ) : (
          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {account.characters.map((character) => (
              <article key={character.id} className={card}>
                <p className="mu-kicker">{character.character_class}</p>
                <h3 className="mt-2 text-2xl font-black">{character.name}</h3>
                <div className="mt-4 flex gap-5 text-sm">
                  <span>
                    <b className="text-amber-300">{character.level}</b>{" "}
                    {copy("level")}
                  </span>
                  <span>
                    <b className="text-amber-300">{character.resets}</b>{" "}
                    {copy("resets")}
                  </span>
                </div>
                <p className="mt-3 text-xs text-gray-600">
                  {copy("currentlyIn")} {character.map_name}
                </p>
              </article>
            ))}
          </div>
        )}
      </section>
    </>
  );
}

function GameMasterDashboard() {
  const { copy, t } = useLanguage();
  const actions = [
    {
      href: "/admin/shop",
      icon: "◆",
      title: "premiumShop",
      text: "shopDescription",
    },
    {
      href: "/admin/content",
      icon: "✦",
      title: "content",
      text: "homeDescription",
    },
    {
      href: "/admin/news",
      icon: "▤",
      title: "latest",
      text: "newsDescription",
    },
  ] as const;
  return (
    <>
      <section className="rounded-2xl border border-red-400/20 bg-[linear-gradient(135deg,rgba(127,29,29,.16),rgba(0,0,0,.25))] p-7">
        <p className="text-xs font-black uppercase tracking-[.25em] text-red-300">
          {copy("gmDashboard")}
        </p>
        <h2 className="mt-3 text-2xl font-black">{copy("dashboard")}</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {actions.map((action) => (
            <Link
              key={action.href}
              href={action.href}
              className={`${card} min-h-44`}
            >
              <span className="text-3xl text-amber-300">{action.icon}</span>
              <h3 className="mt-5 text-xl font-black text-white">
                {copy(action.title)}
              </h3>
              <p className="mt-2 text-sm leading-6 text-gray-500">
                {copy(action.text)}
              </p>
              <span className="mt-4 block text-xs font-bold text-amber-300">
                {copy("discover")}
              </span>
            </Link>
          ))}
        </div>
      </section>
      <div className="mt-5 flex flex-wrap gap-3 text-sm">
        <Link
          href="/admin/download"
          className="rounded-lg border border-white/10 px-4 py-3 text-gray-400 hover:text-white"
        >
          {t("download")}
        </Link>
        <Link
          href="/profile"
          className="rounded-lg border border-white/10 px-4 py-3 text-gray-400 hover:text-white"
        >
          {copy("accountSettings")}
        </Link>
        <Link
          href="/shop"
          className="rounded-lg border border-white/10 px-4 py-3 text-gray-400 hover:text-white"
        >
          {t("shop")}
        </Link>
      </div>
    </>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const { copy } = useLanguage();
  const [account, setAccount] = useState<AccountMe | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loggingOut, setLoggingOut] = useState(false);
  useEffect(() => {
    getMe()
      .then(setAccount)
      .catch((reason) =>
        setError(
          reason instanceof Error
            ? reason.message
            : copy("authenticationRequired"),
        ),
      );
  }, [copy]);
  async function logOut() {
    setLoggingOut(true);
    setError(null);
    try {
      await logoutAccount();
      setAccount(null);
      router.replace("/login");
      router.refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Logout failed.");
      setLoggingOut(false);
    }
  }
  return (
    <main className="min-h-screen text-white">
      <Header />
      <div className="mx-auto max-w-6xl px-6 py-14">
        {error && (
          <div className={card}>
            <p className="text-red-400">{error}</p>
            {!account && (
              <Link href="/login" className="mt-4 inline-block text-amber-300">
                {copy("signInArrow")}
              </Link>
            )}
          </div>
        )}
        {account && (
          <>
            <header className="mb-9 flex flex-wrap items-center justify-between gap-5">
              <div>
                <p className="mu-kicker">
                  {account.role === "game_master"
                    ? copy("gameMaster")
                    : copy("dashboard")}
                </p>
                <h1 className="mt-2 text-4xl font-black">
                  {copy("welcomeBack")}, {account.username}
                </h1>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={`rounded-full border px-4 py-2 text-xs font-black uppercase ${account.role === "game_master" ? "border-red-400/40 bg-red-500/10 text-red-300" : "border-emerald-400/30 bg-emerald-400/10 text-emerald-300"}`}
                >
                  {account.role === "game_master"
                    ? copy("gameMaster")
                    : copy("player")}
                </span>
                <button
                  type="button"
                  onClick={() => void logOut()}
                  disabled={loggingOut}
                  className="rounded-lg border border-red-400/30 bg-red-500/10 px-4 py-2 text-xs font-black uppercase text-red-300 transition hover:bg-red-500/20 disabled:cursor-wait disabled:opacity-50"
                >
                  {loggingOut ? copy("loggingOut") : copy("logOut")}
                </button>
              </div>
            </header>
            {account.role === "game_master" ? (
              <GameMasterDashboard />
            ) : (
              <PlayerDashboard account={account} />
            )}
          </>
        )}
      </div>
      <Footer />
    </main>
  );
}
