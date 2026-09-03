"use client";

import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";

type FeatureCopyKey =
  | "enterWorld"
  | "epicWorld"
  | "homeDescription"
  | "exploreWorld"
  | "viewRankings"
  | "premiumShop"
  | "shopDescription"
  | "enterArmory";

const features: {
  number: string;
  eyebrow: FeatureCopyKey;
  title: FeatureCopyKey;
  description: FeatureCopyKey;
  href: string;
  action: FeatureCopyKey;
}[] = [
  {
    number: "01",
    eyebrow: "enterWorld",
    title: "epicWorld",
    description: "homeDescription",
    href: "/news",
    action: "exploreWorld",
  },
  {
    number: "02",
    eyebrow: "viewRankings",
    title: "viewRankings",
    description: "homeDescription",
    href: "/rankings",
    action: "viewRankings",
  },
  {
    number: "03",
    eyebrow: "premiumShop",
    title: "premiumShop",
    description: "shopDescription",
    href: "/shop",
    action: "enterArmory",
  },
];

const featuresWithCopy: {
  number: string;
  eyebrow: FeatureCopyKey;
  title: FeatureCopyKey;
  description: FeatureCopyKey;
  href: string;
  action: FeatureCopyKey;
}[] = features;

export default function FeatureCards() {
  const { copy } = useLanguage();
  return (
    <section className="border-y border-white/10 bg-black/20">
      <div className="mx-auto max-w-7xl px-6 py-24">
        <div className="max-w-2xl">
          <p className="text-xs font-bold uppercase tracking-[0.35em] text-amber-400">
            {copy("enterWorld")}
          </p>

          <h2 className="mt-3 text-4xl font-black tracking-tight text-white sm:text-5xl">
            {copy("journeyStarts")}
          </h2>

          <p className="mt-5 text-base leading-8 text-gray-500">
            {copy("homeDescription")}
          </p>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {featuresWithCopy.map((feature) => (
            <Link
              key={feature.number}
              href={feature.href}
              className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] p-8 transition duration-300 hover:-translate-y-1 hover:border-amber-400/30 hover:bg-white/[0.05]"
            >
              <div className="absolute right-6 top-5 text-5xl font-black text-white/[0.04] transition duration-300 group-hover:text-amber-400/[0.08]">
                {feature.number}
              </div>

              <div className="relative">
                <div className="flex items-center gap-3">
                  <span className="h-px w-8 bg-amber-400/60" />

                  <span className="text-[10px] font-bold uppercase tracking-[0.25em] text-amber-400">
                    {copy(feature.eyebrow)}
                  </span>
                </div>

                <h3 className="mt-6 text-2xl font-black text-white transition group-hover:text-amber-400">
                  {copy(feature.title)}
                </h3>

                <p className="mt-4 min-h-28 text-sm leading-7 text-gray-500">
                  {copy(feature.description)}
                </p>

                <div className="mt-8 flex items-center justify-between border-t border-white/10 pt-5">
                  <span className="text-xs font-bold uppercase tracking-[0.15em] text-gray-400 transition group-hover:text-white">
                    {copy(feature.action)}
                  </span>

                  <span className="text-lg text-gray-600 transition group-hover:translate-x-1 group-hover:text-amber-400">
                    →
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
