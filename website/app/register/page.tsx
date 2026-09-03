"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { getCaptcha, registerAccount } from "@/lib/api";
import { useLanguage } from "@/components/LanguageProvider";

const field =
  "mt-2 w-full rounded border border-white/10 bg-black/40 px-4 py-3 outline-none focus:border-amber-300/50";
const passwordPattern =
  "(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{10,72}";

export default function RegisterPage() {
  const { copy, locale } = useLanguage();
  const [captcha, setCaptcha] = useState<{
    challenge_id: string;
    question: string;
  } | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    getCaptcha()
      .then(setCaptcha)
      .catch(() => setError(copy("verificationUnavailable")));
  }, [copy]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!captcha) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    if (data.get("password") !== data.get("confirm")) {
      setError(copy("passwordMismatch"));
      return;
    }
    try {
      const result = await registerAccount({
        username: String(data.get("username")),
        email: String(data.get("email")),
        password: String(data.get("password")),
        language: locale,
        security_question: String(data.get("security_question")),
        security_answer: String(data.get("security_answer")),
        challenge_id: captcha.challenge_id,
        answer: String(data.get("answer")),
      });
      setMessage(result.message);
      setError(null);
      form.reset();
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : copy("registrationFailed"),
      );
      setCaptcha(await getCaptcha());
    }
  }

  return (
    <main className="min-h-screen text-white">
      <Header />
      <div className="mx-auto max-w-2xl px-6 py-16">
        <section className="mu-panel rounded-xl p-8">
          <div className="relative">
            <p className="mu-kicker text-center">
              ONE ACCOUNT · WEBSITE & GAME
            </p>
            <h1 className="mt-4 text-center text-3xl font-black">
              Create account
            </h1>
            <div className="mt-6 rounded border border-amber-300/20 bg-amber-300/5 p-4 text-xs leading-6 text-gray-400">
              <strong className="text-amber-200">Account rules</strong>
              <br />
              Username: 4–10 characters; only letters, numbers and underscore.
              <br />
              Password: 10–72 characters, with uppercase, lowercase, number and
              special character.
              <br />
              Email must be valid and unique. Security answer: 3–72 characters.
            </div>
            <form onSubmit={submit} className="mt-8 grid gap-5 sm:grid-cols-2">
              <label className="text-sm font-bold text-gray-300">
                Username
                <input
                  name="username"
                  required
                  minLength={4}
                  maxLength={10}
                  pattern="[A-Za-z0-9_]+"
                  title="Use 4–10 letters, numbers or underscores."
                  autoComplete="username"
                  className={field}
                />
              </label>
              <label className="text-sm font-bold text-gray-300">
                Email
                <input
                  name="email"
                  required
                  type="email"
                  autoComplete="email"
                  className={field}
                />
              </label>
              <label className="text-sm font-bold text-gray-300">
                Password
                <input
                  name="password"
                  required
                  type="password"
                  minLength={10}
                  maxLength={72}
                  pattern={passwordPattern}
                  title="Use 10–72 characters with uppercase, lowercase, number and special character."
                  autoComplete="new-password"
                  className={field}
                />
              </label>
              <label className="text-sm font-bold text-gray-300">
                Confirm password
                <input
                  name="confirm"
                  required
                  type="password"
                  minLength={10}
                  maxLength={72}
                  autoComplete="new-password"
                  className={field}
                />
              </label>
              <label className="text-sm font-bold text-gray-300 sm:col-span-2">
                Security question
                <select
                  name="security_question"
                  required
                  defaultValue=""
                  className={field}
                >
                  <option value="" disabled>
                    Select a question
                  </option>
                  <option value="first_pet">
                    What was the name of your first pet?
                  </option>
                  <option value="birth_city">
                    In what city were you born?
                  </option>
                  <option value="childhood_friend">
                    What was the first name of your childhood best friend?
                  </option>
                  <option value="first_school">
                    What was the name of your first school?
                  </option>
                </select>
              </label>
              <label className="text-sm font-bold text-gray-300 sm:col-span-2">
                Security answer
                <input
                  name="security_answer"
                  required
                  minLength={3}
                  maxLength={72}
                  autoComplete="off"
                  className={field}
                />
                <span className="mt-1 block text-xs font-normal text-gray-500">
                  Remember this answer. It is stored securely and cannot be
                  displayed later.
                </span>
              </label>
              <label className="text-sm font-bold text-gray-300 sm:col-span-2">
                Verification: {captcha?.question ?? "Loading…"}
                <input
                  name="answer"
                  required
                  inputMode="numeric"
                  className={field}
                />
              </label>
              {message && (
                <p className="text-emerald-400 sm:col-span-2">
                  {message}{" "}
                  <Link href="/login" className="underline">
                    Sign in
                  </Link>
                </p>
              )}
              {error && <p className="text-red-400 sm:col-span-2">{error}</p>}
              <button className="rounded bg-amber-400 py-3.5 font-black text-black sm:col-span-2">
                CREATE ACCOUNT
              </button>
            </form>
          </div>
        </section>
      </div>
      <Footer />
    </main>
  );
}
