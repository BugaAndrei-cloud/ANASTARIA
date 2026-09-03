"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { createNews } from "@/lib/api";

const categories = ["GAME", "CLIENT", "LAUNCHER", "WEBSITE", "GENERAL"] as const;

export default function AdminNewsPage() {
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setMessage(null);
    setError(null);

    const form = event.currentTarget;
    const formData = new FormData(form);

    try {
      await createNews({
        title: String(formData.get("title") ?? "").trim(),
        category: String(formData.get("category") ?? "GENERAL"),
        summary: String(formData.get("summary") ?? "").trim() || null,
        content: String(formData.get("content") ?? "").trim() || null,
      });
      form.reset();
      setMessage("News published successfully.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Publishing failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#07080b] px-6 py-16 text-white">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-center justify-between gap-6">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.32em] text-amber-400">
              Admin dashboard
            </p>
            <h1 className="mt-3 text-4xl font-black">Publish news</h1>
          </div>
          <Link href="/news" className="text-sm text-gray-400 hover:text-white">
            View news →
          </Link>
        </div>

        <p className="mt-5 text-sm leading-7 text-gray-500">
          Add updates about the game, client, launcher or website. This page must
          be protected by the ANASTARIA account system before production launch.
        </p>

        <form
          onSubmit={handleSubmit}
          className="mt-10 space-y-6 rounded-2xl border border-amber-400/15 bg-white/[0.03] p-7 sm:p-10"
        >
          <label className="block">
            <span className="text-xs font-bold uppercase tracking-[0.18em] text-gray-400">Title</span>
            <input
              name="title"
              required
              maxLength={200}
              className="mt-3 w-full rounded-lg border border-white/10 bg-black/30 px-4 py-3 outline-none focus:border-amber-400/60"
            />
          </label>

          <label className="block">
            <span className="text-xs font-bold uppercase tracking-[0.18em] text-gray-400">Category</span>
            <select
              name="category"
              className="mt-3 w-full rounded-lg border border-white/10 bg-[#111217] px-4 py-3 outline-none focus:border-amber-400/60"
            >
              {categories.map((category) => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="text-xs font-bold uppercase tracking-[0.18em] text-gray-400">Short summary</span>
            <textarea
              name="summary"
              rows={3}
              maxLength={500}
              className="mt-3 w-full resize-y rounded-lg border border-white/10 bg-black/30 px-4 py-3 outline-none focus:border-amber-400/60"
            />
          </label>

          <label className="block">
            <span className="text-xs font-bold uppercase tracking-[0.18em] text-gray-400">News content</span>
            <textarea
              name="content"
              required
              rows={10}
              className="mt-3 w-full resize-y rounded-lg border border-white/10 bg-black/30 px-4 py-3 outline-none focus:border-amber-400/60"
            />
          </label>

          {message && <p className="text-sm text-emerald-400">{message}</p>}
          {error && <p className="text-sm text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-amber-500 px-6 py-4 text-sm font-black uppercase tracking-[0.14em] text-black transition hover:bg-amber-400 disabled:cursor-wait disabled:opacity-60"
          >
            {submitting ? "Publishing..." : "Publish news"}
          </button>
        </form>
      </div>
    </main>
  );
}

