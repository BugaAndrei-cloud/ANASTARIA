# ANASTARIA Player Marketplace — audited architecture

Status: Phase 1 architecture decision. Economic mutations are intentionally not enabled yet.

## Audit findings

- The website is Next.js and uses `website/lib/i18n.ts`. The enabled locale registry currently contains 11 locales: `en`, `ro`, `ru`, `es`, `pt`, `pt-BR`, `es-AR`, `fil`, `lt`, `de`, and `fr`.
- Website authentication is cookie based. FastAPI stores only a SHA-256 hash of the opaque session token in `web_sessions`; the cookie is HttpOnly, SameSite=Lax, and Secure in production.
- FastAPI and OpenMU currently use the same PostgreSQL database. ANASTARIA-owned tables use the default schema, while OpenMU uses `data` for account state and `config` for definitions.
- The OpenMU EF implementation gives every physical `Item`, `ItemStorage`, `Character`, and `Account` a persistent UUID. `Item.Id` is therefore the marketplace instance identity; definition/level/options are not an identity.
- A character owns an `Inventory` (`ItemStorage`), and an account owns a `Vault` (`ItemStorage`). Physical items belong to exactly one storage through the OpenMU EF relationship. Zen is numeric `ItemStorage.Money` (inventory or vault, depending on the selected policy).
- Item instances contain their definition, slot, durability, level, skill flag, option links (including excellent/luck/harmony/socket options as configured), ancient-set links, socket count, store price, and pet experience. Marketplace display snapshots must be derived from these real relationships.
- Jewels and crafting materials are physical item instances unless a separately audited server currency says otherwise. Aggregated quantities in the UI must resolve to, lock, and move exact UUIDs during settlement.
- OpenMU keeps an account/player aggregate in a per-player EF context. Client packet mutations and periodic saves are serialized by `PlayerPersistence`, but that lock is process-local. There is no persistent `IsOnline` column on `Account` or `Character` which can safely fence an external writer.
- OpenMU can run offline helper players as well as connected players. Checking only network connections would therefore be insufficient.
- The current website Shop is a separate server catalog and remains unchanged by the marketplace design.
- `server/anastaria` contains no existing marketplace integration service or command boundary to reuse.

## Safety decision

FastAPI must not update OpenMU item storage, item options, inventory money, or vault money directly. Restricting the website to “offline characters” is not sufficient without an authoritative game-server lease/fence: a login can race the check, and an offline-helper session can still hold the aggregate in memory.

All OpenMU-owned mutations must run inside an ANASTARIA-owned game-server integration module, using the same player persistence serialization boundary as gameplay. The web API submits idempotent commands; it never edits a live inventory graph.

## Ownership and storage model

The authoritative physical item is always the existing OpenMU `data.Item` row with its existing UUID. Listing never clones it.

Marketplace storage is represented by dedicated OpenMU `ItemStorage` aggregates, created and mutated only by the game-server integration module:

- escrow storage: marketplace-owned, contains listed sale items;
- buyer delivery storage: account-owned logical delivery bucket;
- seller proceeds storage: account-owned logical bucket containing physical payment assets.

ANASTARIA tables reference the OpenMU item UUID and storage UUID but do not duplicate the physical item. JSON snapshots are display/history data only.

Every marketplace command verifies the location invariant before commit:

`one item UUID -> exactly one OpenMU storage -> exactly one marketplace purpose/owner`

Database uniqueness constraints additionally prevent one item UUID from appearing in two active escrow, delivery, or proceeds records.

## Command boundary

The FastAPI service writes a command to a transactional outbox and returns `202 Accepted` while processing, or waits for a bounded result when the game-server command endpoint is available. Each command has:

- a UUID command/transaction id;
- authenticated account id (never accepted from the browser);
- operation and validated payload;
- idempotency key scoped to account and operation;
- state (`PENDING`, `PROCESSING`, `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_FINAL`);
- attempt count, timestamps, stable result/error code, and structured parameters.

The integration worker claims commands with `FOR UPDATE SKIP LOCKED`. The game server acquires the affected player persistence locks in a deterministic account-id order, then starts one PostgreSQL transaction which locks marketplace rows and exact OpenMU storage/item rows. Login/character selection must acquire the same database advisory lock for an account; this is the cross-process fence missing from the current process-local lock.

The command result is persisted in the same transaction as the economic mutation. A retry returns the stored result and cannot repeat settlement.

## Listing state machines

Listing states:

- `DRAFT`
- `ESCROW_PENDING`
- `ACTIVE`
- `PROCESSING`
- `SOLD`
- `CANCELLED`
- `EXPIRED`
- `RECOVERY_REQUIRED`

Delivery/proceeds states:

- `AVAILABLE`
- `CLAIMING`
- `CLAIMED`
- `RECOVERY_REQUIRED`

Only explicit transitions are accepted. The conditional transition from `ACTIVE` to `PROCESSING`, protected by a row lock, makes buy-versus-buy and buy-versus-cancel mutually exclusive.

## Accepted Payment Assets

`market_asset_definitions` is administrative configuration, not a hardcoded jewel list. A definition contains a stable code, asset type, optional OpenMU item-definition UUID, display translation key, icon, enabled flags, listing/fee eligibility, min/max amount, and sort order.

Supported settlement adapters:

- `NUMERIC_STORAGE_MONEY`: audited numeric OpenMU storage balance, initially suitable for Zen;
- `PHYSICAL_ITEM`: exact OpenMU item instances matching one configured item-definition UUID and trade policy;
- future adapters may be registered for server-side ledgers only after their authority and locking rules are audited.

A listing price is a set of unique `(listing_id, asset_definition_id, amount)` rows with positive bounded amounts. The API accepts asset codes and amounts only; it reloads definitions and the active listing price from the database.

## Atomic purchase

In one game-server-owned transaction:

1. obtain deterministic account advisory locks for buyer and seller;
2. lock listing and transition `ACTIVE -> PROCESSING`;
3. lock and verify the real escrow item and its unique location;
4. reload the configured price;
5. lock buyer numeric balances and select exact physical payment item UUIDs deterministically;
6. verify all components before mutating any component;
7. move/debit buyer assets into seller proceeds;
8. move the escrow item into buyer delivery;
9. write transaction, immutable price/item snapshots, asset movements, and audit records;
10. transition listing to `SOLD`, persist the idempotent result, and commit.

Delivery and proceeds are part of successful settlement, so a full vault never makes a completed purchase lose value. Claim is a separate idempotent command which checks rectangular inventory/vault capacity and either moves all requested assets atomically or leaves them available.

## Required implementation order

1. Add ANASTARIA marketplace metadata, outbox, idempotency, audit, and state constraints through Alembic.
2. Add the ANASTARIA-owned OpenMU integration module and shared account advisory-lock/login fence.
3. Implement escrow/list/cancel and invariant checks in the integration module.
4. Implement typed read APIs and the localized Browse/Details UI.
5. Implement the localized Sell/Price Builder flow.
6. Implement atomic purchase settlement.
7. Implement Delivery and Proceeds claims.
8. Add filters/history/admin asset configuration.
9. Verify every new visible key in all registered locales.
10. Run database, idempotency, concurrency, rollback, authorization, invariant, API, website, and locale-parity tests.

## Deployment gates

Marketplace economic endpoints must remain disabled until all of these gates pass:

- live PostgreSQL schema inspection matches the checked-in OpenMU EF mappings;
- login/selection and marketplace commands share the cross-process account fence;
- the integration module is deployed on every game-server instance;
- concurrency tests prove one winner for buy/buy and buy/cancel;
- crash/retry tests prove idempotent recovery;
- an invariant scanner reports no duplicate or ownerless physical item;
- all enabled website locales pass key and placeholder parity checks.

## Phase 2 concrete foundation

Phase 2 stores ANASTARIA-owned metadata in PostgreSQL's `public` schema; it does not add or mutate objects in OpenMU's `data` or `config` schemas. Physical OpenMU identifiers remain UUID references without cross-schema foreign keys so that ANASTARIA metadata ownership stays explicit. All relationships among Marketplace entities use database foreign keys.

The persistent foundation consists of normalized payment assets and prices, listings, commands, idempotency records, transactions, deliveries, proceeds and proceeds components, audit events, account fencing tokens, and a global physical-item location registry. The location registry has `openmu_item_id` as its primary key, preventing one physical item from being represented in escrow, delivery, and proceeds simultaneously.

Account fencing uses a transaction-scoped PostgreSQL advisory lock derived from the account UUID plus a persisted monotonically increasing token. `acquire_account_fence` must be called inside the same database transaction as the economic operation. Phase 3 must add the matching acquire call to normal login/character selection and Offline Helper entry before any Marketplace mutation is enabled.

Idempotency is scoped by authenticated account, operation, and caller-provided key. A canonical SHA-256 payload hash binds a key to one request. Matching retries return the existing command; a different payload raises `MARKETPLACE_IDEMPOTENCY_CONFLICT`. Command and idempotency rows are flushed in the caller's transaction, so domain state and outbox creation commit or roll back together.

## Phase 3 offline-only correction

Online physical Marketplace execution is prohibited. OpenMU claims a persistent
`marketplace_account_sessions` row in `STARTING` state before loading an account aggregate, changes
it to `ACTIVE` after login initialization, and changes it to `STOPPING` before teardown. The final
save is followed by recursive EF detach; only then may ownership be removed. Offline Helper handover
replaces the session id, kind, and monotonically increasing fence token under the same PostgreSQL
advisory lock, so there is no unowned interval.

Marketplace workers acquire the identical transaction-scoped lock using
`hashtextextended(account_id::text, 1296127045)`. Any session row blocks mutation regardless of
state, kind, or lease time. An expired lease creates a reconciliation requirement; lease expiry never
authorizes a mutation.

Affected account fences are:

- `CREATE_LISTING`, `CANCEL_LISTING`, `CLAIM_PROCEEDS`: seller/command account;
- `BUY_LISTING`, `CLAIM_DELIVERY`: buyer/command account.

BUY does not load or mutate the seller aggregate. Seller value remains in Marketplace-owned
proceeds until a separately fenced claim.

### Phase 3 physical storage and balance policy

Marketplace escrow, delivery, and physical proceeds are real `data.ItemStorage` rows registered by
`marketplace_physical_storages`. A move updates the existing `data.Item.ItemStorageId`; it never
inserts, clones, or replaces an item. `marketplace_item_locations` is a checked tracking index, not
the authoritative item owner.

Numeric assets default to `ACCOUNT_VAULT`, meaning `data.Account.VaultId -> data.ItemStorage.Money`.
`CHARACTER_INVENTORY` is allowed only with an explicit, account-owned `character_id`. Physical BUY
results always enter MARKET_DELIVERY first. CLAIM uses OpenMU's 8-column first-fit algorithm,
`ItemDefinition.Width/Height`, 15 vault rows and the account's vault-extension flag. When no valid
slot exists, value remains in Marketplace storage and the command receives a timed retry.

Every OpenMU row update and Marketplace state change uses the same SQLAlchemy PostgreSQL transaction.

Detailed lifecycles are documented in `docs/MARKETPLACE_STATE_MACHINE.md`.
