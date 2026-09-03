"use client";
import { useEffect, useState } from "react";
import PageScaffold from "@/components/PageScaffold";
import { useLanguage } from "@/components/LanguageProvider";
import { getSiteSettings, SiteSetting } from "@/lib/api";

export default function ContactPage() {
  const { t, copy } = useLanguage();
  const [settings, setSettings] = useState<SiteSetting[]>([]);
  useEffect(() => {
    const controller = new AbortController();
    getSiteSettings(controller.signal)
      .then((data) => setSettings(data.items))
      .catch(() => undefined);
    return () => controller.abort();
  }, []);
  const contacts =
    settings.find((item) => item.key === "contacts")?.value ?? {};
  const stream = settings.find((item) => item.key === "stream")?.value ?? {};
  const channels = [
    [copy("email"), contacts.email],
    [copy("telephone"), contacts.phone],
    ["WhatsApp", contacts.whatsapp],
    ["Facebook", contacts.facebook],
    ["Discord", contacts.discord],
  ];
  return (
    <PageScaffold
      eyebrow={copy("officialChannels")}
      title={t("contact")}
      description={copy("contactDescription")}
    >
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {channels.map(([label, value]) => (
          <article key={String(label)} className="mu-panel rounded-xl p-7">
            <div className="relative">
              <p className="mu-kicker">{label}</p>
              <p className="mt-4 break-all text-sm text-gray-400">
                {String(value || copy("notConfigured"))}
              </p>
            </div>
          </article>
        ))}
      </div>
      {Boolean(stream.active) && stream.url && (
        <a
          href={String(stream.url)}
          className="mu-panel mt-8 block rounded-xl p-8 text-amber-300"
        >
          ● {copy("live")} — {String(stream.platform || copy("stream"))}
        </a>
      )}
    </PageScaffold>
  );
}
