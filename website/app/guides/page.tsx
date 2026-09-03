"use client";

import PageScaffold from "@/components/PageScaffold";
import { useLanguage } from "@/components/LanguageProvider";

const sections = [
  "Getting started",
  "Characters & classes",
  "Reset & mastery",
  "Crafting",
  "Events",
  "Guilds & Castle Siege",
];
export default function GuidesPage() {
  const { copy, locale } = useLanguage();
  const translatedSections = [
    "Getting started",
    "Characters & classes",
    "Reset & mastery",
    "Crafting",
    "Events",
    "Guilds & Castle Siege",
  ];
  const roSections = [
    "Noțiuni introductive",
    "Personaje și clase",
    "Resetări și măiestrie",
    "Meșteșug",
    "Evenimente",
    "Bresle și Asediul Castelului",
  ];
  return (
    <PageScaffold
      eyebrow={copy("knowledgeArchive")}
      title={copy("gameGuides")}
      description={copy("guidesDescription")}
    >
      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {sections.map((section, index) => (
          <article key={section} className="mu-panel rounded-xl p-7">
            <div className="relative">
              <span className="text-2xl text-amber-300">◆</span>
              <h2 className="mt-4 text-xl font-black">
                {locale === "ro"
                  ? roSections[index]
                  : translatedSections[index]}
              </h2>
              <p className="mt-3 text-sm leading-6 text-gray-500">
                {copy("guideCategory")}
              </p>
            </div>
          </article>
        ))}
      </div>
    </PageScaffold>
  );
}
