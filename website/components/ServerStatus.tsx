"use client";

import { useLanguage } from "@/components/LanguageProvider";
import { useEffect, useState } from "react";
import { getServerStatus } from "@/lib/api";

type ServerStatusProps = {
  status?: "online" | "offline" | "maintenance";
  playersOnline?: number | null;
  version?: string | null;
};

const statusConfig = {
  online: {
    label: "Online",
    color: "text-emerald-400",
    dot: "bg-emerald-400",
    glow: "shadow-[0_0_12px_rgba(52,211,153,0.8)]",
  },
  offline: {
    label: "Offline",
    color: "text-red-400",
    dot: "bg-red-400",
    glow: "shadow-[0_0_12px_rgba(248,113,113,0.8)]",
  },
  maintenance: {
    label: "Maintenance",
    color: "text-amber-400",
    dot: "bg-amber-400",
    glow: "shadow-[0_0_12px_rgba(251,191,36,0.8)]",
  },
} as const;

export default function ServerStatus({
  status = "online",
  playersOnline = 0,
  version = null,
}: ServerStatusProps) {
  const { copy } = useLanguage();
  const [live, setLive] = useState<{
    status: "online" | "offline" | "maintenance";
    players: number | null;
    version: string | null;
  }>({ status, players: playersOnline, version });
  useEffect(() => {
    const controller = new AbortController();
    const refresh = () =>
      getServerStatus(controller.signal)
        .then((data) =>
          setLive({
            status: data.status === "online" ? "online" : "offline",
            players: data.players_online,
            version: data.version,
          }),
        )
        .catch(() => setLive((current) => ({ ...current, status: "offline" })));
    refresh();
    const timer = window.setInterval(refresh, 5000);
    const onVisible = () => {
      if (document.visibilityState === "visible") refresh();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      controller.abort();
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [playersOnline, status, version]);
  const liveConfig = {
    ...statusConfig[live.status],
    label:
      live.status === "online"
        ? "Online"
        : live.status === "offline"
          ? "Offline"
          : "Maintenance",
  };

  return (
    <section className="border-y border-white/10 bg-black/20">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-gray-500">
              {copy("serverStatus")}
            </p>

            <div className="mt-3 flex items-center gap-3">
              <span
                className={`h-2.5 w-2.5 rounded-full ${liveConfig.dot} ${liveConfig.glow}`}
              />

              <span
                className={`text-lg font-bold uppercase tracking-wide ${liveConfig.color}`}
              >
                {liveConfig.label}
              </span>
            </div>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-gray-500">
              {copy("playersOnline")}
            </p>

            <p className="mt-3 text-lg font-bold text-white">
              {live.players ?? "—"}
            </p>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-gray-500">
              {copy("serverVersion")}
            </p>

            <p className="mt-3 text-lg font-bold text-white">
              {live.version ?? copy("comingSoon")}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
