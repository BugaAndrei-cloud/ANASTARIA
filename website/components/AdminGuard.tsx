"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getMe } from "@/lib/api";

export default function AdminGuard({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<"loading" | "allowed" | "denied">("loading");
  useEffect(() => { getMe().then((account) => setState(account.role === "game_master" ? "allowed" : "denied")).catch(() => setState("denied")); }, []);
  if (state === "loading") return <main className="min-h-screen bg-[#07080b] px-6 py-20 text-center text-gray-400">Checking Game Master access…</main>;
  if (state === "denied") return <main className="min-h-screen bg-[#07080b] px-6 py-20 text-center text-white"><h1 className="text-3xl font-black">Game Master access required</h1><Link href="/dashboard" className="mt-6 inline-block text-amber-300">Return to dashboard</Link></main>;
  return children;
}
