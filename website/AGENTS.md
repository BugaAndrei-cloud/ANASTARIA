## Regula obligatorie de localizare

Orice text nou sau modificat care este afișat în site trebuie adăugat în sistemul i18n și tradus în toate limbile disponibile în `website/lib/i18n.ts`. Nu se acceptă texte UI hardcodate într-o singură limbă. Se păstrează neschimbate doar denumirile jocului, numele obiectelor/personajelor și valorile dinamice primite din API.

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# ANASTARIA Website — Agent Instructions & Execution Protocol

## 1. Project Scope & Boundaries

- **Root Context:** This is the official ANASTARIA MMORPG website located at `D:\ANASTARIA\website`, part of the larger project at `D:\ANASTARIA`.
- **Directory Isolation:** Do not modify, create, or delete any files outside `D:\ANASTARIA\website` unless explicitly requested by the user in the prompt.
- **Prompt Scope:** Execute **ONLY** what the user explicitly requests in the prompt. Do not invent unrequested features, side tasks, or optional refactorings.

---

## 2. Technology & Architecture Stack

- **Dependencies:** Use strict versions already installed in `package.json`:
  - Next.js 16.3.3
  - React 19.2.8
  - TypeScript
  - Tailwind CSS v4
- **Routing:** Exclusively use the Next.js App Router (`app/` folder). The main entry point is `app/page.tsx`.
- **Forbidden Patterns:** Never create or reference a `pages/` directory or `pages/index.tsx`.
- **Component Strategy:** Maintain modular code architecture. Break down complex pages into reusable components under a `/components` directory. Never write the entire application inside `app/page.tsx`.
- **App Routes Structure:** Use distinct App Router route folders for:
  - `/` (Homepage)
  - `/news`
  - `/rankings`
  - `/shop`
  - `/download`
  - `/login`
  - `/register`

---

## 3. Data Flow & Security Rules

- **Zero Hardcoding Policy:** Never hardcode production business or game data into components. This includes: news, rankings, player online counters, server status, shop items, prices, currencies, active events, character stats, accounts, game configs, client download URLs, payment gateways, or auth secrets.
- **Data Layer:** All dynamic data must flow through typed TypeScript interfaces/props via a dedicated API/data layer.
- **Mock Data Standard:** Development/demo placeholders must be explicitly tagged as mock data (e.g., `mockNewsData`). Never hallucinate fake production endpoints, API schemas, or DB tables.
- **Architecture Flow:**
  $$\text{Website} \longrightarrow \text{ANASTARIA API} \longrightarrow \text{Database} \longrightarrow \text{Game Server}$$
- **Direct Database Restriction:** The website frontend must **NEVER** attempt a direct connection to the game database.

---

## 4. Authentication, Shop, & System Integrations

- **Authentication:** Do not build authentication screens or logic unless explicitly tasked in the prompt. All future login systems (Website, Google Auth, Android, PC Client) must share a unified ANASTARIA account backend.
- **Shop & Payments:** Do not create shop items, checkout logic, payment gateway scripts, or transaction routes until explicitly requested.

---

## 5. Sequential Execution Protocol (Step-by-Step)

When a prompt is given, follow these sequential steps without skipping:

### Step 1: Pre-Implementation Analysis

1. Inspect the target codebase files related to the prompt.
2. Consult current Next.js local docs at `node_modules/next/dist/docs/` to confirm API syntax (especially breaking changes in Next.js 16+ / React 19+).
3. Verify existing `package.json` scripts and installed components before creating new dependencies.

### Step 2: Implementation Phase

1. Make surgical, clean file edits directly to solve the exact requirement of the prompt.
2. Adhere strictly to TypeScript types — avoid `any` types wherever possible.
3. Keep code clean, DRY (Don't Repeat Yourself), and well-structured.

### Step 3: Verification & Quality Assurance

1. Run only scripts present in `package.json` (e.g., `npm run lint`, `npm run build`).
2. If any build or lint errors occur, analyze them carefully and fix them step by step.
3. Repeat step 3 until the build/lint passes cleanly.

### Step 4: Final Reporting

1. List every file created, modified, or deleted.
2. Provide a concise summary of the exact changes made to satisfy the prompt.

---

## 6. General Constraints & Anti-Patterns

- **DO NOT** replace Next.js, React, or Tailwind CSS with alternative frameworks.
- **DO NOT** initialize secondary projects or monorepo sub-apps unless instructed.
- **DO NOT** install npm packages arbitrarily without verifying if existing packages satisfy the requirement.
- **DO NOT** stop midway to ask for confirmation on routine implementation tasks unless there is an unresolvable ambiguity in the prompt.
- **DO NOT** duplicate rules or instructions in this file or across documentation files.

---

## 7. Master Development Roadmap

1. Frontend structure and visual design.
2. ANASTARIA API layer setup.
3. Database and unified account system.
4. Website authentication and Google Login.
5. Game/server synchronization and status integration.
6. Shop ecosystem and payment gateway integration.
7. Android APK & PC Client unified login integration.
