"use client";

import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import { GameEvent, getEvents } from "@/lib/api";

interface EventWithNextTime extends GameEvent {
  nextEventTime: Date | null;
  timeRemaining: string;
}

function nextEvent(schedule: string, now: Date): Date | null {
  const times = [...schedule.matchAll(/\b(\d{2}):(\d{2})\b/g)].map((match) => [
    Number(match[1]),
    Number(match[2]),
  ]);

  if (!times.length) return null;

  for (const [hour, minute] of times) {
    const candidate = new Date(now);
    candidate.setUTCHours(hour, minute, 0, 0);
    if (candidate > now) return candidate;
  }

  const [hour, minute] = times[0];
  const result = new Date(now);
  result.setUTCDate(result.getUTCDate() + 1);
  result.setUTCHours(hour, minute, 0, 0);
  return result;
}

function countdown(target: Date | null, now: Date): string {
  if (!target) return "Schedule only";
  const seconds = Math.max(
    0,
    Math.floor((target.getTime() - now.getTime()) / 1000),
  );
  return `${String(Math.floor(seconds / 3600)).padStart(2, "0")}:${String(
    Math.floor((seconds % 3600) / 60),
  ).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}

export default function EventsTable() {
  const { locale, copy } = useLanguage();
  const [events, setEvents] = useState<EventWithNextTime[]>([]);
  const [now, setNow] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    const controller = new AbortController();

    getEvents(controller.signal)
      .then((data) => {
        const activeEvents = data.items
          .filter((e) => e.active)
          .map((e) => {
            const nextTime = nextEvent(e.schedule, new Date(data.server_time));
            return {
              ...e,
              nextEventTime: nextTime,
              timeRemaining: countdown(nextTime, new Date(data.server_time)),
            };
          })
          // Sort by time remaining (ascending - soonest first)
          .sort((a, b) => {
            if (!a.nextEventTime && !b.nextEventTime) return 0;
            if (!a.nextEventTime) return 1;
            if (!b.nextEventTime) return -1;
            return a.nextEventTime.getTime() - b.nextEventTime.getTime();
          });

        setEvents(activeEvents);
        setLoading(false);
      })
      .catch((reason) => {
        if (!(reason instanceof DOMException && reason.name === "AbortError")) {
          setError(
            reason instanceof Error ? reason.message : "Error loading events",
          );
        }
        setLoading(false);
      });

    return () => {
      window.clearInterval(timer);
      controller.abort();
    };
  }, []);

  // Update time remaining for current event every second
  const liveEvents = events.map((event) => ({
    ...event,
    timeRemaining: countdown(event.nextEventTime, now),
  }));

  if (loading) {
    return (
      <div className="mu-panel rounded-xl p-4">
        <p className="text-xs text-gray-400">{copy("loadingGeneric")}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mu-panel rounded-xl p-4">
        <p className="text-xs text-red-400">{error}</p>
      </div>
    );
  }

  return (
    <div className="mu-panel rounded-xl overflow-hidden">
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <span className="text-xs font-black tracking-[.3em] text-amber-300/50">
            01
          </span>
          <h3 className="text-lg font-black text-white">
            {copy("worldEvents")}
          </h3>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10 bg-white/[0.02]">
              <th className="px-4 py-2 text-left text-[10px] font-bold uppercase tracking-wider text-amber-400">
                {copy("serverTime")}
              </th>
              <th className="px-4 py-2 text-left text-[10px] font-bold uppercase tracking-wider text-amber-400">
                {copy("worldEvents")}
              </th>
            </tr>
          </thead>
          <tbody>
            {liveEvents.map((event) => {
              const translated =
                event.translations[locale] ?? event.translations.en ?? {};
              return (
                <tr
                  key={event.id}
                  className="border-b border-white/5 transition hover:bg-white/[0.05]"
                >
                  <td className="px-4 py-2">
                    <span className="font-mono text-xs font-bold text-amber-300">
                      {event.timeRemaining}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    <span className="text-xs text-white">
                      {translated.title ?? event.slug}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {events.length === 0 && (
        <div className="p-4 text-center text-xs text-gray-500">
          {copy("noActiveEvents")}
        </div>
      )}
    </div>
  );
}
