# ANASTARIA Marketplace state machines

## Listing

- `PENDING_ESCROW -> ACTIVE | FAILED`
- `ACTIVE -> PROCESSING | CANCEL_PENDING | EXPIRED`
- `PROCESSING -> SOLD | ACTIVE | FAILED`
- `CANCEL_PENDING -> CANCELLED | ACTIVE | FAILED`
- `SOLD`, `CANCELLED`, `EXPIRED`, and `FAILED` are terminal in Phase 2.

Only the Game Server integration worker may complete escrow, purchase, cancel, delivery, or proceeds transitions. FastAPI creates the domain request and outbox command atomically.

## Command

- `PENDING -> PROCESSING`
- `PROCESSING -> SUCCEEDED | RETRYABLE_FAILED | PERMANENT_FAILED`
- `RETRYABLE_FAILED -> PROCESSING` after `available_at` and backoff.
- `SUCCEEDED` and `PERMANENT_FAILED` are terminal.

Workers claim eligible rows with `FOR UPDATE SKIP LOCKED`. A stored successful result is authoritative for retries.

## Purchase transaction

- `CREATED -> PROCESSING`
- `PROCESSING -> PAYMENT_RESERVED | FAILED`
- `PAYMENT_RESERVED -> ITEM_TRANSFERRED | ROLLBACK_REQUIRED`
- `ITEM_TRANSFERRED -> COMPLETED | ROLLBACK_REQUIRED`
- recovery moves `ROLLBACK_REQUIRED` to `FAILED` after compensation or resumes it to `COMPLETED` when the durable item/payment movements prove completion.

Movement checkpoints are audit/history information. The intended settlement implementation performs payment, delivery, proceeds, transaction completion, command result, and listing completion in one PostgreSQL transaction.

## Delivery and proceeds

- `PENDING -> CLAIMING`
- `CLAIMING -> CLAIMED | PENDING | FAILED`
- `CLAIMED` is terminal.

A capacity failure returns to `PENDING` without moving value. Proceeds use a header plus normalized components. Numeric components are unique by proceeds and asset; every physical component retains an exact OpenMU item UUID.

## Physical item location

`marketplace_item_locations.openmu_item_id` is globally unique. Its location is one of `ESCROW`, `DELIVERY`, or `PROCEEDS`, with a reference, optional owner, and the fencing token which authorized the movement. Phase 3 changes this row in the same transaction as the authoritative OpenMU storage mutation.

## Account fence

1. Begin PostgreSQL transaction.
2. Acquire `pg_advisory_xact_lock` for every affected account in sorted UUID order.
3. Increment and read the persisted account fencing token.
4. Reload and lock all domain and OpenMU rows.
5. Validate the token and current state immediately before mutation.
6. Apply the economic operation and audit result.
7. Commit; PostgreSQL releases the advisory lock automatically.

Login, character selection, Offline Helper entry, and Marketplace settlement must all participate. Until the Phase 3 hooks exist, economic command processing remains disabled.

## Idempotency and recovery

## Persistent session safety

- `STARTING -> ACTIVE -> STOPPING -> removed` is the normal lifecycle.
- ONLINE/OFFLINE_HELPER handover replaces ownership atomically, without an absent session row.
- Every existing session row blocks physical Marketplace mutation, including an expired row.
- Expiry requires explicit reconciliation; removing a crashed session alone is insufficient.
- A blocked command uses `RETRYABLE_FAILED`, a stable reason code and a future `available_at`, so
  workers do not busy-loop.

## Idempotency and recovery

The unique scope is `(account_id, operation, idempotency_key)`. Canonical payload hashes reject key reuse with different input. Outbox commands also have a unique `(account_id, command_type, idempotency_key)` constraint. Correlation IDs connect commands, transactions, listings, deliveries, proceeds, and audit events for crash investigation.
