# ANASTARIA Launcher — Agent Instructions

## 1. Scope and precedence

- These rules apply to everything under `D:\ANASTARIA\launcher`.
- Root `D:\ANASTARIA\AGENTS.md` still applies; this file takes precedence for launcher-specific work.
- Keep launcher changes isolated unless the task explicitly requires a coordinated API, website, installer, or game-client change.
- Inspect existing implementation before editing and preserve user changes.

## 2. Product role

The launcher is the trusted desktop entry point for ANASTARIA. It is responsible for:

- installing, verifying, repairing, and updating the game client;
- updating itself safely;
- exposing supported game settings before launch;
- authenticating through the ANASTARIA API;
- displaying server status, news, events, account information, and shop content;
- launching the configured game executable.

The launcher is not a game server, database client, payment processor, or source of production business data.

## 3. Architecture boundaries

Use this data flow:

`Launcher -> typed ANASTARIA API -> database/OpenMU`

- Never connect directly to PostgreSQL or any OpenMU database.
- Never invent or call undocumented production endpoints. Inspect `api/app/routers` and typed schemas first.
- Put new launcher-specific backend operations in the ANASTARIA API and define typed request/response contracts on both sides.
- The game connection itself may launch/connect to the OpenMU Connect Server using the client configuration, but account, news, events, shop, patch metadata, and installer metadata flow through the API/CDN boundary.
- Do not embed API secrets, signing private keys, database credentials, payment credentials, or production tokens.

## 4. Cross-project synchronization

Before changing shared behavior, inspect all affected sources:

- API contracts: `api/app/routers` and `api/app/schemas`;
- website contracts and translations: `website/lib/api.ts` and `website/lib/i18n.ts`;
- MonoGame settings: `client/multiplatform/Client.Main/Configuration/MuOnlineSettings.cs`;
- game startup/config loading: `client/multiplatform/Client.Main/MuGame.cs`;
- server protocol definitions: `external/OpenMU-Source`;
- launcher typed models and services: `launcher/Anastaria.Launcher`.

When a shared contract changes, update every affected typed consumer in the same task and verify each changed project. Do not duplicate server-owned schedules, shop prices, news, status, account state, client versions, or patch versions inside launcher UI code.

## 5. Localization

- No user-facing text may be added directly to XAML or C# after the localization foundation exists.
- Use stable translation keys and UTF-8 resources.
- Romanian and English are mandatory baseline languages. Keep keys synchronized with website terminology where concepts are shared.
- Server-provided localized content must use the API translation shape; do not hardcode translated copies in the launcher.
- Missing translations must fall back to English and remain visible, never crash the launcher.
- Buttons, validation messages, patch states, settings labels, error messages, installer copy, and accessibility names must all be localized.

## 6. Visual identity

- Match the official website design tokens rather than approximating a separate brand.
- Core palette: background `#08090D`, panel `#0E1118`, gold `#D7A53C`, foreground `#FFFFFF`.
- Use restrained fantasy elements: dark stone/metal surfaces, fine gold borders, runes, embers, and warm highlights. Maintain high contrast and readable controls.
- Use the shared official ANASTARIA logo asset. Do not create competing logos in individual views.
- Keep imagery in `Assets/`, use optimized local files, and record source/generation provenance in documentation.
- Support 100%, 125%, 150%, and 200% Windows scaling and a minimum window size of 940x620.

## 7. Game settings

- The launcher may edit only settings implemented and consumed by the client.
- Define settings once in the client configuration model; mirror them with typed launcher models.
- Preserve unknown JSON properties when editing client configuration so newer clients remain compatible.
- Validate supported resolutions, numeric ranges, enum values, and paths before saving.
- Write configuration atomically through a temporary file and replacement; never leave a partially written settings file.
- Do not expose protocol version, serial, connect-server host/port, patch URLs, or security-sensitive compatibility values as ordinary player settings.
- Separate settings into Display, Graphics, Performance, Audio, Interface, and Gameplay/Camera sections.

## 8. Authentication and account security

- Authenticate only over HTTPS in production.
- Keep API session cookies/tokens in memory or OS-protected storage; never log passwords, cookies, refresh tokens, or one-time tickets.
- Do not pass account passwords to the game process or place them on a command line.
- Automatic game login must use a short-lived, single-use launcher ticket issued by the API and validated by the server/client integration.
- Clear authentication state on logout and handle expired/revoked sessions.
- Shop purchases require explicit user confirmation and server-side validation; the launcher never calculates authoritative balances or grants items.

## 9. Patching and self-update

- Patch manifests must use normalized relative paths, declared sizes, SHA-256 hashes, and a cryptographic signature verified with a pinned public key.
- The manifest signing private key must never be present in the repository or launcher.
- Reject absolute paths, traversal, links/reparse-point escapes, unsupported algorithms, invalid signatures, duplicate destinations, and files outside the installation root.
- Download to a staging directory, support cancellation/resume where possible, verify before replacement, and use atomic moves.
- Preserve recoverable backups for critical executables/configuration and roll back failed updates.
- Never patch while the game is running. Use a separate updater process for launcher self-update.
- Asset and binary distribution URLs must be HTTPS in production.

## 10. Installer

- The installer deploys the launcher first; the launcher installs/repairs game payloads.
- Use per-user installation by default unless elevated machine-wide installation is explicitly required.
- Create Start Menu/Desktop shortcuts only through installer options.
- Uninstall must preserve user settings/screenshots by default and clearly offer removal of downloaded game data.
- Code signing is required for public release binaries and installer packages.

## 11. Code quality

- Current desktop implementation: .NET 10 WPF with nullable reference types.
- Keep UI, API access, patching, settings persistence, process launch, and authentication in separate classes/services.
- Use async I/O and cancellation tokens; never block the UI thread with network, hashing, or file operations.
- Avoid broad exception swallowing. Present localized safe errors and retain diagnostic detail without secrets.
- Use `HttpClient` reuse, typed DTOs, bounded timeouts, and explicit JSON naming.
- No new packages unless the existing framework cannot meet a required feature and the dependency has been reviewed.

## 12. Required execution sequence

1. Read the request and inspect launcher plus every affected contract owner.
2. Confirm whether a child `AGENTS.md` applies in any other target directory.
3. Implement the smallest complete vertical slice.
4. Build the launcher with `dotnet build launcher/Anastaria.Launcher/Anastaria.Launcher.csproj`.
5. If API changes: compile Python and run relevant API checks.
6. If website changes: run its configured lint/build scripts.
7. If client changes: build both Windows DX and GL heads; build Android when mobile-shared code changes.
8. Smoke-test launcher startup and the affected workflow.
9. Report every created, modified, or deleted file relative to `D:\ANASTARIA`, plus limitations that still require production infrastructure.

## 13. Definition of done

A launcher feature is complete only when:

- its UI is localized and consistent with the website brand;
- it uses a real typed contract or an explicitly unconfigured state;
- loading, offline, empty, error, cancellation, and success states are handled;
- security boundaries above are preserved;
- relevant builds/checks pass;
- no credentials, proprietary client data, build outputs, or local SDKs are added to Git.
