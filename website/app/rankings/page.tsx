"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { getPublicApiUrl } from "@/lib/api";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useLanguage } from "@/components/LanguageProvider";

type RankingType = "resets" | "level" | "master" | "experience" | "killers";

type RankingPlayer = {
  rank: number;
  character_id: string;
  name: string;
  character_class: string;
  level: number;
  master_level: number;
  resets: number;
  experience: number;
  master_experience: number;
  player_kills: number;
  guild_name: string;
  alliance_name: string;
  map_name: string;
  created_at: string;
  character_status: number;
  quest_progress: number;
  is_online: boolean;
};

const rankingTabs: { id: RankingType; label: string; detail: string }[] = [
  { id: "resets", label: "Resets", detail: "Legendary rebirths" },
  { id: "level", label: "Level", detail: "Highest level" },
  { id: "master", label: "Master", detail: "Master progression" },
  { id: "experience", label: "Experience", detail: "Total experience" },
  { id: "killers", label: "PK", detail: "Player kills" },
];

const number = new Intl.NumberFormat("en-US");
const apiUrl = getPublicApiUrl();

function primaryValue(player: RankingPlayer, type: RankingType) {
  const values = {
    resets: `${number.format(player.resets)} resets`,
    level: `Level ${number.format(player.level)}`,
    master: `Master ${number.format(player.master_level)}`,
    experience: `${number.format(player.experience)} EXP`,
    killers: `${number.format(player.player_kills)} kills`,
  };
  return values[type];
}

function crest(rank: number) {
  if (rank === 1) return "I";
  if (rank === 2) return "II";
  return "III";
}

function medal(rank: number) {
  if (rank === 1) return <span title="Gold" className="drop-shadow-[0_2px_5px_rgba(245,190,65,.6)]">🥇</span>;
  if (rank === 2) return <span title="Silver" className="drop-shadow-[0_2px_5px_rgba(210,220,230,.45)]">🥈</span>;
  if (rank === 3) return <span title="Bronze" className="drop-shadow-[0_2px_5px_rgba(190,110,55,.45)]">🥉</span>;
  return null;
}

export default function RankingsPage() {
  const { locale, t } = useLanguage();
  const [rankingType, setRankingType] = useState<RankingType>("resets");
  const [players, setPlayers] = useState<RankingPlayer[]>([]);
  const [selected, setSelected] = useState<RankingPlayer | null>(null);
  const [classFilter, setClassFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(Boolean(apiUrl));
  const [error, setError] = useState<string | null>(
    apiUrl ? null : "Rankings API is not configured.",
  );

  useEffect(() => {
    const controller = new AbortController();
    if (!apiUrl) {
      return () => controller.abort();
    }

    fetch(`${apiUrl}/rankings/${rankingType}?limit=100`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("Rankings are temporarily unavailable.");
        return response.json() as Promise<RankingPlayer[]>;
      })
      .then((items) => {
        setPlayers(items);
        setSelected(items[0] ?? null);
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Rankings could not be loaded.");
      })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, [rankingType]);

  const classes = useMemo(
    () => [...new Set(players.map((player) => player.character_class))].sort(),
    [players],
  );

  const visiblePlayers = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    return players.filter((player) => {
      const matchesClass = classFilter === "ALL" || player.character_class === classFilter;
      const matchesSearch = !query || player.name.toLocaleLowerCase().includes(query);
      return matchesClass && matchesSearch;
    });
  }, [classFilter, players, search]);

  const podium = players.slice(0, 3);

  return (
    <main className="min-h-screen bg-[#06070a] text-[#eee8dc]">
      <Header />
      <div className="border-b border-amber-200/10 bg-[radial-gradient(circle_at_50%_-20%,rgba(180,117,29,.23),transparent_45%),linear-gradient(180deg,#11100d,#07080b)]">
        <div className="mx-auto max-w-[1500px] px-5 py-10 sm:px-8 sm:py-14">
          <div className="flex flex-wrap items-center justify-between gap-5">
            <Link href="/" className="text-xs font-bold uppercase tracking-[.22em] text-stone-500 hover:text-amber-300">
              ← ANASTARIA
            </Link>
            <div className="rounded border border-emerald-400/20 bg-emerald-400/5 px-3 py-2 text-[10px] font-bold uppercase tracking-[.2em] text-emerald-400">
              Live character data
            </div>
          </div>
          <div className="mt-12 text-center">
            <p className="text-[10px] font-bold uppercase tracking-[.55em] text-amber-500">Hall of legends</p>
            <h1 className="mt-4 font-serif text-5xl font-black uppercase tracking-[.06em] text-[#f4ead6] sm:text-7xl">{t("rankings")}</h1>
            <div className="mx-auto mt-5 h-px w-56 bg-gradient-to-r from-transparent via-amber-500/70 to-transparent" />
            <p className="mx-auto mt-6 max-w-2xl text-sm leading-7 text-stone-500">
              The strongest warriors, master heroes and guild champions of ANASTARIA.
              Every value below is read from the live game database through the API.
            </p>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-[1500px] px-5 py-8 sm:px-8">
        <nav className="grid overflow-hidden rounded-lg border border-white/10 bg-[#0d0e12] sm:grid-cols-5">
          {rankingTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setLoading(true);
                setError(null);
                setRankingType(tab.id);
                setClassFilter("ALL");
                setSearch("");
              }}
              className={`border-b border-white/5 px-4 py-4 text-left transition sm:border-b-0 sm:border-r ${
                rankingType === tab.id ? "bg-amber-500/10 text-amber-300" : "text-stone-500 hover:bg-white/[.03] hover:text-stone-200"
              }`}
            >
              <span className="block text-xs font-black uppercase tracking-[.18em]">{tab.label}</span>
              <span className="mt-1 block text-[10px] text-stone-600">{tab.detail}</span>
            </button>
          ))}
        </nav>

        {!loading && !error && podium.length > 0 && (
          <section className="mt-8 grid gap-4 md:grid-cols-3">
            {podium.map((player) => (
              <button
                key={player.character_id}
                onClick={() => setSelected(player)}
                className={`group relative overflow-hidden rounded-lg border bg-gradient-to-b p-6 text-left transition hover:-translate-y-1 ${
                  player.rank === 1 ? "border-amber-400/40 from-amber-400/10 to-[#0c0d10]" : "border-white/10 from-white/[.04] to-[#0c0d10]"
                }`}
              >
                <span className="absolute right-5 top-2 font-serif text-7xl font-black text-white/[.035]">{crest(player.rank)}</span>
                <p className="text-[10px] font-black uppercase tracking-[.28em] text-amber-500">Rank #{player.rank}</p>
                <h2 className="mt-5 flex items-center gap-2 text-2xl font-black text-white group-hover:text-amber-300">
                  {medal(player.rank)} {player.name}
                  {player.is_online && <span title="Online" aria-label="Online" className="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-[0_0_9px_rgba(52,211,153,.9)]" />}
                </h2>
                <p className="mt-1 text-xs text-stone-500">{player.character_class}</p>
                <div className="mt-6 border-t border-white/10 pt-4 text-sm font-bold text-amber-200">{primaryValue(player, rankingType)}</div>
              </button>
            ))}
          </section>
        )}

        <div className="mt-8 grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
          <section className="overflow-hidden rounded-lg border border-white/10 bg-[#0c0d10]">
            <div className="flex flex-col gap-3 border-b border-white/10 p-4 sm:flex-row">
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search character..."
                className="min-w-0 flex-1 rounded border border-white/10 bg-black/30 px-4 py-3 text-sm outline-none placeholder:text-stone-700 focus:border-amber-500/40"
              />
              <select
                value={classFilter}
                onChange={(event) => setClassFilter(event.target.value)}
                className="rounded border border-white/10 bg-[#111216] px-4 py-3 text-xs font-bold uppercase tracking-wider outline-none"
              >
                <option value="ALL">All classes</option>
                {classes.map((name) => <option key={name} value={name}>{name}</option>)}
              </select>
            </div>

            {loading && <div className="p-16 text-center text-sm text-stone-600">Loading the Hall of Legends...</div>}
            {error && <div className="p-16 text-center text-sm text-red-400">{error}</div>}
            {!loading && !error && visiblePlayers.length === 0 && <div className="p-16 text-center text-sm text-stone-600">No warriors match this search.</div>}

            {!loading && !error && visiblePlayers.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[900px] text-left">
                  <thead className="bg-black/25 text-[9px] font-black uppercase tracking-[.2em] text-stone-600">
                    <tr><th className="px-5 py-4">Rank</th><th className="px-5 py-4">Character</th><th className="px-5 py-4">Class</th><th className="px-5 py-4">Resets</th><th className="px-5 py-4">Level</th><th className="px-5 py-4">Master</th><th className="px-5 py-4">PK</th><th className="px-5 py-4">Guild</th><th className="px-5 py-4">Alliance</th></tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {visiblePlayers.map((player) => (
                      <tr key={player.character_id} onClick={() => setSelected(player)} className="cursor-pointer text-sm transition hover:bg-amber-400/[.035]">
                        <td className="px-5 py-4 font-serif text-lg font-black text-amber-500">#{player.rank}</td>
                        <td className="px-5 py-4 font-bold text-stone-100">
                          <span className="inline-flex items-center gap-2">
                            {medal(player.rank)} {player.name}
                            {player.is_online && <span title="Online" aria-label="Online" className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,.85)]" />}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-xs text-stone-500">{player.character_class}</td>
                        <td className="px-5 py-4 font-bold text-amber-200">{number.format(player.resets)}</td>
                        <td className="px-5 py-4 text-stone-400">{number.format(player.level)}</td>
                        <td className="px-5 py-4 text-stone-400">{number.format(player.master_level)}</td>
                        <td className="px-5 py-4 text-red-400">{number.format(player.player_kills)}</td>
                        <td className="px-5 py-4 text-stone-500">{player.guild_name}</td>
                        <td className="px-5 py-4 text-stone-500">{player.alliance_name}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <aside className="h-fit rounded-lg border border-amber-300/15 bg-[linear-gradient(180deg,rgba(191,129,42,.08),rgba(12,13,16,.98))] p-6 xl:sticky xl:top-6">
            {selected ? (
              <>
                <p className="text-[9px] font-black uppercase tracking-[.3em] text-amber-500">Character profile</p>
                <h2 className="mt-3 flex items-center gap-3 text-3xl font-black text-white">
                  {selected.name}
                  {selected.is_online && <span title="Online" aria-label="Online" className="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-[0_0_9px_rgba(52,211,153,.9)]" />}
                </h2>
                <p className="mt-1 text-sm text-stone-500">{selected.character_class}</p>
                <dl className="mt-7 grid grid-cols-2 gap-px overflow-hidden rounded border border-white/10 bg-white/10 text-xs">
                  {[
                    ["Level", number.format(selected.level)], ["Master", number.format(selected.master_level)],
                    ["Resets", number.format(selected.resets)], ["PK kills", number.format(selected.player_kills)],
                    ["Guild", selected.guild_name], ["Alliance", selected.alliance_name],
                    ["Map", selected.map_name], ["Quest lines", number.format(selected.quest_progress)],
                  ].map(([label, value]) => <div key={label} className="bg-[#0c0d10] p-3"><dt className="text-[9px] uppercase tracking-wider text-stone-600">{label}</dt><dd className="mt-1 truncate font-bold text-stone-300">{value}</dd></div>)}
                </dl>
                <div className="mt-6">
                  <p className="text-[9px] font-black uppercase tracking-[.25em] text-stone-600">Successes</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {selected.rank <= 3 && <span className="rounded border border-amber-400/25 bg-amber-400/10 px-3 py-2 text-[10px] font-bold text-amber-300">TOP {selected.rank}</span>}
                    {selected.quest_progress > 0 && <span className="rounded border border-sky-400/20 bg-sky-400/10 px-3 py-2 text-[10px] font-bold text-sky-300">QUEST PROGRESS {selected.quest_progress}</span>}
                    {selected.guild_name !== "—" && <span className="rounded border border-violet-400/20 bg-violet-400/10 px-3 py-2 text-[10px] font-bold text-violet-300">GUILD MEMBER</span>}
                    {selected.rank > 3 && selected.quest_progress === 0 && selected.guild_name === "—" && <span className="text-xs text-stone-600">No recorded successes yet.</span>}
                  </div>
                </div>
                <p className="mt-7 border-t border-white/10 pt-5 text-[10px] leading-5 text-stone-600">Created {new Date(selected.created_at).toLocaleDateString(locale)}</p>
              </>
            ) : <p className="text-sm text-stone-600">Select a character to view the full profile.</p>}
          </aside>
        </div>
      </div>
      <Footer />
    </main>
  );
}
