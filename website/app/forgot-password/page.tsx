"use client";

import { FormEvent, useEffect, useState } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import {
  confirmSecurityReset,
  getCaptcha,
  requestSecurityReset,
} from "@/lib/api";
import { useLanguage } from "@/components/LanguageProvider";

const field =
  "mt-2 w-full rounded border border-white/10 bg-black/40 px-4 py-3 outline-none focus:border-amber-300/50";
const passwordPattern =
  "(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{10,72}";

export default function ForgotPage() {
  const { copy } = useLanguage();
  const [captcha, setCaptcha] = useState<{
    challenge_id: string;
    question: string;
  } | null>(null);
  const [recovery, setRecovery] = useState<{
    token: string;
    question: string;
  } | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    getCaptcha()
      .then(setCaptcha)
      .catch(() => setError(copy("verificationUnavailable")));
  }, [copy]);

  async function identify(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!captcha) return;
    const data = new FormData(event.currentTarget);
    try {
      setRecovery(
        await requestSecurityReset(
          String(data.get("username")),
          String(data.get("email")),
          captcha.challenge_id,
          String(data.get("answer")),
        ),
      );
      setError(null);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : copy("registrationFailed"),
      );
      setCaptcha(await getCaptcha());
    }
  }

  async function reset(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!recovery) return;
    const data = new FormData(event.currentTarget);
    if (data.get("password") !== data.get("confirm")) {
      setError(copy("passwordMismatch"));
      return;
    }
    try {
      const result = await confirmSecurityReset(
        recovery.token,
        String(data.get("security_answer")),
        String(data.get("password")),
      );
      setMessage(result.message);
      setError(null);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Password could not be changed.",
      );
    }
  }

  return (
    <main className="min-h-screen text-white">
      <Header />
      <div className="mx-auto my-20 max-w-md px-6">
        <section className="mu-panel rounded-xl p-8">
          <div className="relative space-y-5">
            <p className="mu-kicker">ACCOUNT RECOVERY</p>
            <h1 className="text-3xl font-black">Recover password</h1>
            {!recovery && !message && (
              <form onSubmit={identify} className="space-y-5">
                <label className="block text-sm">
                  Username
                  <input
                    name="username"
                    required
                    minLength={4}
                    maxLength={10}
                    pattern="[A-Za-z0-9_]+"
                    className={field}
                  />
                </label>
                <label className="block text-sm">
                  Account email
                  <input name="email" type="email" required className={field} />
                </label>
                <label className="block text-sm">
                  Verification: {captcha?.question ?? "Loading…"}
                  <input
                    name="answer"
                    required
                    inputMode="numeric"
                    className={field}
                  />
                </label>
                <button className="w-full rounded bg-amber-400 py-3 font-black text-black">
                  CONTINUE
                </button>
              </form>
            )}
            {recovery && !message && (
              <form onSubmit={reset} className="space-y-5">
                <p className="text-sm text-gray-300">{recovery.question}</p>
                <label className="block text-sm">
                  Security answer
                  <input
                    name="security_answer"
                    required
                    minLength={3}
                    maxLength={72}
                    autoComplete="off"
                    className={field}
                  />
                </label>
                <label className="block text-sm">
                  New password
                  <input
                    name="password"
                    type="password"
                    required
                    minLength={10}
                    maxLength={72}
                    pattern={passwordPattern}
                    title="Use uppercase, lowercase, number and special character."
                    autoComplete="new-password"
                    className={field}
                  />
                </label>
                <label className="block text-sm">
                  Confirm new password
                  <input
                    name="confirm"
                    type="password"
                    required
                    minLength={10}
                    maxLength={72}
                    autoComplete="new-password"
                    className={field}
                  />
                </label>
                <button className="w-full rounded bg-amber-400 py-3 font-black text-black">
                  CHANGE PASSWORD
                </button>
              </form>
            )}
            {message && <p className="text-sm text-emerald-400">{message}</p>}
            {error && <p className="text-sm text-red-400">{error}</p>}
          </div>
        </section>
      </div>
      <Footer />
    </main>
  );
}
