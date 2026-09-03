"use client";

import Link from "next/link";
import { useLanguage } from "@/components/LanguageProvider";
import type { CommonKey } from "@/lib/i18n";

const footerLinks: (
  | { key: CommonKey; href: string }
  | { label: string; href: string }
)[] = [
  { key: "news", href: "/news" },
  { key: "rankings", href: "/rankings" },
  { key: "shop", href: "/shop" },
  { key: "download", href: "/download" },
  { key: "guides", href: "/guides" },
  { key: "contact", href: "/contact" },
  { label: "terms", href: "/terms" },
];

export default function Footer() {
  const year = new Date().getFullYear();
  const { t, copy } = useLanguage();

  return (
    <footer className="border-t border-amber-300/15 bg-black/35">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-8 md:flex-row md:items-center md:justify-between">
        <p className="text-sm text-gray-500">
          © {year} ANASTARIA. {copy("homeTagline")}.
        </p>

        <nav
          aria-label="Footer navigation"
          className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-gray-500"
        >
          {footerLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="transition hover:text-white"
            >
              {"key" in link ? t(link.key) : copy(link.label as "terms")}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  );
}
