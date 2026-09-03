"use client";

import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";

export default function LiveClocks({
  serverTimeIso = null,
}: {
  serverTimeIso?: string | null;
}) {
  const [now, setNow] = useState<Date | null>(null);
  const { copy, locale } = useLanguage();
  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);
  const local = now
    ? new Intl.DateTimeFormat(undefined, {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        timeZoneName: "short",
      }).format(now)
    : "—";
  const server = serverTimeIso
    ? new Intl.DateTimeFormat(locale, {
        dateStyle: "medium",
        timeStyle: "medium",
      }).format(new Date(serverTimeIso))
    : copy("awaitingServer");
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div className="mu-panel rounded-lg p-6">
        <p className="mu-kicker">{copy("yourTime")}</p>
        <p className="mt-3 text-2xl font-black text-white">{local}</p>
      </div>
      <div className="mu-panel rounded-lg p-6">
        <p className="mu-kicker">{copy("serverTime")}</p>
        <p className="mt-3 text-2xl font-black text-white">{server}</p>
      </div>
    </div>
  );
}
