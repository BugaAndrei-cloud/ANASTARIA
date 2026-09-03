"use client";
import { FormEvent, useEffect, useState } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { getMe, updateProfile, type AccountMe } from "@/lib/api";
import { useLanguage } from "@/components/LanguageProvider";
const field =
  "mt-2 w-full rounded border border-white/10 bg-black/40 px-4 py-3";
export default function ProfilePage() {
  const { copy } = useLanguage();
  const [account, setAccount] = useState<AccountMe | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
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
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const d = new FormData(event.currentTarget);
    await updateProfile({
      display_name: String(d.get("display_name")),
      country_code: String(d.get("country_code")) || null,
      avatar_url: String(d.get("avatar_url")) || null,
      bio: String(d.get("bio")) || null,
    });
    setMessage(copy("profileSaved"));
  }
  return (
    <main className="min-h-screen text-white">
      <Header />
      <div className="mx-auto max-w-3xl px-6 py-16">
        {error && (
          <div className="mu-panel rounded-xl p-8 text-red-400">{error}</div>
        )}
        {account && (
          <form onSubmit={submit} className="mu-panel rounded-xl p-8">
            <div className="relative">
              <p className="mu-kicker">{copy("accountSettings")}</p>
              <h1 className="mt-3 text-4xl font-black">{account.username}</h1>
              <p className="mt-2 text-sm text-gray-500">{account.email}</p>
              <div className="mt-8 grid gap-5 sm:grid-cols-2">
                <label>
                  {copy("displayName")}
                  <input
                    name="display_name"
                    required
                    defaultValue={
                      account.profile?.display_name ?? account.username
                    }
                    className={field}
                  />
                </label>
                <label>
                  {copy("country")}
                  <input
                    name="country_code"
                    maxLength={2}
                    defaultValue={account.profile?.country_code ?? ""}
                    placeholder="RO"
                    className={field}
                  />
                </label>
                <label className="sm:col-span-2">
                  {copy("avatarUrl")}
                  <input
                    name="avatar_url"
                    defaultValue={account.profile?.avatar_url ?? ""}
                    className={field}
                  />
                </label>
                <label className="sm:col-span-2">
                  {copy("about")}
                  <textarea
                    name="bio"
                    maxLength={500}
                    rows={5}
                    defaultValue={account.profile?.bio ?? ""}
                    className={field}
                  />
                </label>
              </div>
              {message && <p className="mt-5 text-emerald-400">{message}</p>}
              <button className="mt-6 w-full rounded bg-amber-400 py-3 font-black text-black">
                {copy("saveProfile")}
              </button>
            </div>
          </form>
        )}
      </div>
      <Footer />
    </main>
  );
}
