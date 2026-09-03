# ANASTARIA Project (OpenMU) — Master Agent Instructions & Protocol

## 1. Scope & Hierarchy

- **Root Context:** This file applies to the entire ANASTARIA MMORPG workspace located at `D:\ANASTARIA`.
- **Precedence Rule:** Subdirectory-specific instructions (such as `D:\ANASTARIA\website\AGENTS.md`) take precedence for operations inside those respective subdirectories.
- **Strict Prompt Boundaries:** Execute **ONLY** what the user explicitly requests in the prompt. Do not perform unrequested refactoring, add optional features, or modify unrelated modules.

---

## 2. Core Project Boundaries & Architecture

- **Technology Ecosystem:**
  - **Game Server / Backend Services:** OpenMU (C# / .NET).
  - **Website / Web Apps:** Next.js / TypeScript (isolated in subfolders).
  - **Launcher / Mobile / Clients:** Shared ecosystem via explicit API layers.
- **Architectural Isolation:** Maintain strict decoupling between layers:
  $$\text{Website / Clients / Launcher} \longrightarrow \text{ANASTARIA API Layer} \longrightarrow \text{Database} \longrightarrow \text{OpenMU Game Server}$$
- **Direct Access Restriction:** Neither the website, mobile client, launcher, nor third-party integrations may ever connect directly to the game server database. All interactions must go through the typed ANASTARIA API.
- **Environment & Secrets:** Never hardcode secrets, connection strings, API keys, or production credentials in source code. Keep local configuration, build outputs, and credentials strictly ignored in Git (`.gitignore`).

---

## 3. OpenMU & Code Quality Standards

- **Code Inspection First:** Always inspect existing OpenMU / C# / TypeScript implementations and patterns before adding or modifying code.
- **Preserve Existing Work:** Do not discard or overwrite user changes, working configurations, or ongoing features present in the worktree.
- **No Hallucinated Data:** Do not fabricate production schemas, fake payment gateways, mock game accounts, or invented API endpoints unless explicitly tasked to generate temporary dev mocks.
- **C# / OpenMU Guidelines:**
  - Follow existing .NET / C# coding standards in the OpenMU solution.
  - Maintain thread safety and async/await best practices for high-performance server logic.
  - Respect existing plugin architecture, packet handlers, and game logic abstractions.

---

## 4. Sequential Execution Protocol (Step-by-Step)

For every task given in a prompt, the agent **MUST** follow this step-by-step sequence:

### Step 1: Context & Dependency Analysis

1. Read the user prompt carefully and identify the exact target component (e.g., Server, API, Website, Launcher).
2. Inspect the relevant existing code files, `.csproj`, `package.json`, or configuration files.
3. Check for child `AGENTS.md` files in the target directory and adhere to their specific rules.

### Step 2: Incremental Implementation

1. Execute the requested changes step-by-step without skipping steps.
2. Ensure modifications are minimal, clean, and directly address the prompt's request.
3. Ensure no duplicated code or conflicting abstractions are created across modules.

### Step 3: Verification & Compilation

1. Run the existing build, test, lint, or type-check commands for the modified project (e.g., `dotnet build`, `dotnet test`, `npm run build`, `npm run lint`).
2. If any compilation, runtime, or lint errors occur, diagnose and fix them immediately.
3. Repeat validation until the project compiles and passes checks cleanly.

### Step 4: Change Summary & Reporting

1. List all modified, added, or deleted files relative to `D:\ANASTARIA`.
2. Provide a brief, step-by-step report of the exact changes executed.

---

## 5. General Constraints & Anti-Patterns

- **DO NOT** modify files outside the prompt's requested scope.
- **DO NOT** install new global tools or extra NuGet/npm packages unless required to fulfill the prompt and verified as missing.
- **DO NOT** stop to request manual confirmation for routine, unambiguous implementation steps.
- **DO NOT** duplicate guidelines, rules, or documentation across multiple files unnecessarily.
