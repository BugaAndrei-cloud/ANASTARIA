import Link from "next/link";
import EventsTable from "./EventsTable";
import { useLanguage } from "@/components/LanguageProvider";

const pillars = [
  {
    title: "Player economy",
    text: "Crafting, materials, trading and meaningful resource sinks beyond reset progression.",
    href: "/guides",
  },
  {
    title: "Premium shop",
    text: "Account services, cosmetics and VIP benefits prepared for API-driven catalog data.",
    href: "/shop",
  },
];

export default function WorldPortal() {
  const { copy } = useLanguage();
  return (
    <section className="relative border-y border-amber-300/10 bg-black/25">
      <div className="mx-auto max-w-7xl px-6 py-24">
        <div className="text-center">
          <p className="mu-kicker">{copy("enterWorld")}</p>
          <h2 className="mu-title mt-4 text-4xl sm:text-5xl">
            {copy("journeyStarts")}
          </h2>
          <p className="mx-auto mt-5 max-w-2xl leading-7 text-gray-400">
            {copy("homeDescription")}
          </p>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          <EventsTable />
          {pillars.map((pillar, index) => (
            <Link
              key={pillar.title}
              href={pillar.href}
              className="mu-panel group rounded-xl p-8 transition duration-300 hover:-translate-y-1 hover:border-amber-300/45"
            >
              <div className="relative">
                <span className="text-xs font-black tracking-[.3em] text-amber-300/50">
                  0{index + 2}
                </span>
                <h3 className="mt-5 text-2xl font-black group-hover:text-amber-200">
                  {copy(index === 0 ? "playerEconomy" : "premiumShop")}
                </h3>
                <p className="mt-4 text-sm leading-7 text-gray-500">
                  {copy(index === 0 ? "homeDescription" : "shopDescription")}
                </p>
                <span className="mt-7 inline-block text-xs font-bold uppercase tracking-wider text-amber-300">
                  {copy("discover")}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
