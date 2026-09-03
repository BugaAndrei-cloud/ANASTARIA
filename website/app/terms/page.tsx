"use client";

import PageScaffold from "@/components/PageScaffold";
import { useLanguage } from "@/components/LanguageProvider";

const terms = [
  [
    "1. General use",
    "By creating an account or using ANASTARIA services, users agree to follow the published game rules, community standards and applicable laws.",
  ],
  [
    "2. Accounts",
    "Users are responsible for protecting their credentials and for activity performed through their accounts. Account trading, fraud, automation and exploitation may lead to restrictions.",
  ],
  [
    "3. Virtual goods",
    "Characters, virtual currencies and digital items are licensed for use inside ANASTARIA. They do not represent bank deposits, investments or ownership of server software.",
  ],
  [
    "4. Payments",
    "Prices may be displayed in EUR, USD and other supported currencies. The system records the original amount, conversion and EUR base value before premium game currency is credited.",
  ],
  [
    "5. Refunds",
    "Refund eligibility depends on applicable consumer law, payment-provider rules and whether digital content has already been delivered or consumed.",
  ],
  [
    "6. Fair play",
    "Cheats, bots, unauthorized modifications, payment fraud, abusive conduct and attempts to disrupt services are prohibited.",
  ],
  [
    "7. Service changes",
    "Game systems, balancing, availability and content may change as ANASTARIA evolves. Material changes will be announced through official channels.",
  ],
];
export default function TermsPage() {
  const { copy, locale } = useLanguage();
  const roTerms = [
    [
      "1. Utilizare generală",
      "Prin crearea unui cont sau folosirea serviciilor ANASTARIA, utilizatorii acceptă regulile publicate ale jocului, standardele comunității și legile aplicabile.",
    ],
    [
      "2. Conturi",
      "Utilizatorii sunt responsabili pentru protejarea datelor de acces și pentru activitatea desfășurată prin conturile lor. Tranzacționarea conturilor, frauda, automatizarea și exploatarea pot duce la restricții.",
    ],
    [
      "3. Bunuri virtuale",
      "Personajele, monedele virtuale și obiectele digitale sunt licențiate pentru utilizare în ANASTARIA. Ele nu reprezintă depozite bancare, investiții sau drepturi de proprietate asupra software-ului serverului.",
    ],
    [
      "4. Plăți",
      "Prețurile pot fi afișate în EUR, USD și alte monede acceptate. Sistemul înregistrează suma inițială, conversia și valoarea de bază în EUR înainte de creditarea monedei premium.",
    ],
    [
      "5. Rambursări",
      "Eligibilitatea pentru rambursare depinde de legislația aplicabilă, regulile procesatorului de plăți și dacă produsul digital a fost deja livrat sau consumat.",
    ],
    [
      "6. Joc corect",
      "Trișarea, boții, modificările neautorizate, frauda la plată, comportamentul abuziv și încercările de perturbare a serviciilor sunt interzise.",
    ],
    [
      "7. Modificarea serviciului",
      "Sistemele de joc, echilibrarea, disponibilitatea și conținutul se pot schimba pe măsură ce ANASTARIA evoluează. Schimbările importante vor fi anunțate pe canalele oficiale.",
    ],
  ];
  const displayedTerms = locale === "ro" ? roTerms : terms;
  return (
    <PageScaffold
      eyebrow={copy("legalInformation")}
      title={copy("termsConditions")}
      description={copy("termsDescription")}
    >
      <div className="mu-panel rounded-xl p-8 sm:p-10">
        <div className="relative space-y-8">
          {displayedTerms.map(([title, content]) => (
            <section key={title}>
              <h2 className="text-xl font-black text-amber-200">{title}</h2>
              <p className="mt-3 leading-7 text-gray-400">{content}</p>
            </section>
          ))}
          <p className="border-t border-amber-300/15 pt-6 text-xs uppercase tracking-wider text-amber-300/60">
            {copy("draftNotice")}
          </p>
        </div>
      </div>
    </PageScaffold>
  );
}
