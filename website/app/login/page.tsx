"use client";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { loginAccount } from "@/lib/api";
import { useLanguage } from "@/components/LanguageProvider";
const field =
  "mt-2 w-full rounded border border-white/10 bg-black/40 px-4 py-3 outline-none focus:border-amber-300/50";
export default function LoginPage() {
  const router = useRouter();
  const { copy } = useLanguage();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy(true);
    setError(null);
    try {
      await loginAccount(
        String(data.get("username")),
        String(data.get("password")),
      );
      router.push("/dashboard");
      router.refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Login failed.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="min-h-screen text-white">
      <Header />
      <div className="mx-auto flex min-h-[calc(100vh-10rem)] max-w-md items-center px-6 py-16">
        <section className="mu-panel w-full rounded-xl p-8">
          <div className="relative">
            <div className="text-center">
              <p className="mu-kicker">ANASTARIA ACCOUNT</p>
              <h1 className="mt-4 text-3xl font-black">
                {copy("welcomeBack")}
              </h1>
              <p className="mt-3 text-sm text-gray-500">
                {copy("signInDescription")}
              </p>
            </div>
            <form onSubmit={submit} className="mt-8 space-y-5">
              <label className="block text-sm font-bold text-gray-300">
                {copy("username")}
                <input
                  name="username"
                  required
                  autoComplete="username"
                  className={field}
                />
              </label>
              <label className="block text-sm font-bold text-gray-300">
                {copy("password")}
                <input
                  name="password"
                  required
                  type="password"
                  autoComplete="current-password"
                  className={field}
                />
              </label>
              {error && <p className="text-sm text-red-400">{error}</p>}
              <div className="text-right">
                <Link
                  href="/forgot-password"
                  className="text-xs text-amber-300"
                >
                  {copy("forgotPassword")}
                </Link>
              </div>
              <button
                disabled={busy}
                className="w-full rounded bg-gradient-to-b from-amber-300 to-amber-600 py-3.5 text-sm font-black uppercase text-black disabled:opacity-50"
              >
                {busy ? copy("loadingGeneric") : copy("signIn")}
              </button>
            </form>
            <p className="mt-7 border-t border-white/10 pt-6 text-center text-sm text-gray-500">
              {copy("noAccount")}{" "}
              <Link href="/register" className="font-bold text-amber-300">
                {copy("createOne")}
              </Link>
            </p>
          </div>
        </section>
      </div>
      <Footer />
    </main>
  );
}
